# SJ Professional Directory - Data Processing Engine
# ============================================================================

import pandas as pd
import re
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import json
import os
import chardet

from config import (
    Config, RAW_FILES_DIR, SUPPORTED_FILE_TYPES, 
    PROFESSION_KEYWORDS, LOCATION_MAPPINGS, BATCH_PATTERNS,
    COMPANY_DOMAINS
)
from database import DatabaseManager
from text_processor import TextProcessor
from ai_inference import ProfessionInferencer

logger = logging.getLogger(__name__)

class DataProcessor:
    """Main data processing engine for importing and normalizing member data."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.text_processor = TextProcessor()
        self.ai_inferencer = ProfessionInferencer()
        self.stats = {
            'files_processed': 0,
            'records_found': 0,
            'records_imported': 0,
            'records_updated': 0,
            'duplicates_found': 0,
            'errors': []
        }
    
    def import_all_files(self) -> Dict[str, Any]:
        """Import all supported files from Raw_Files directory."""
        logger.info("Starting full data import from Raw_Files directory")
        
        # Create import batch
        batch_name = f"Full Import {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        source_files = self._discover_files()
        batch_id = self.db.create_import_batch(batch_name, [str(f) for f in source_files])
        
        try:
            # Process each file
            for file_path in source_files:
                try:
                    self._process_file(file_path, batch_id)
                    self.stats['files_processed'] += 1
                except Exception as e:
                    error_msg = f"Error processing {file_path}: {e}"
                    logger.error(error_msg)
                    self.stats['errors'].append(error_msg)
            
            # Update batch with final results
            self.db.update_import_batch(batch_id, {
                'total_files_processed': self.stats['files_processed'],
                'total_records_processed': self.stats['records_found'],
                'records_created': self.stats['records_imported'],
                'records_updated': self.stats['records_updated'],
                'errors_encountered': len(self.stats['errors']),
                'import_status': 'success' if not self.stats['errors'] else 'partial',
                'error_log': json.dumps(self.stats['errors'])
            })
            
            logger.info(f"Import completed: {self.stats}")
            return self.stats
            
        except Exception as e:
            # Update batch with failure status
            self.db.update_import_batch(batch_id, {
                'import_status': 'failed',
                'error_log': json.dumps([str(e)])
            })
            logger.error(f"Import failed: {e}")
            raise
    
    def _discover_files(self) -> List[Path]:
        """Discover all supported files in Raw_Files directory."""
        files = []
        
        # Main directory
        for file_path in RAW_FILES_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FILE_TYPES:
                files.append(file_path)
        
        # Subdirectories
        for subdir in ['UP Chapters', 'Other Chapters']:
            subdir_path = RAW_FILES_DIR / subdir
            if subdir_path.exists():
                for file_path in subdir_path.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FILE_TYPES:
                        files.append(file_path)
        
        logger.info(f"Discovered {len(files)} files for processing")
        return files
    
    def _process_file(self, file_path: Path, batch_id: int):
        """Process a single file based on its type."""
        file_type = SUPPORTED_FILE_TYPES.get(file_path.suffix.lower())
        
        logger.info(f"Processing {file_path} (type: {file_type})")
        
        if file_type == 'excel_old':
            self._process_excel_file(file_path, batch_id)
        elif file_type == 'excel_new':
            self._process_excel_file(file_path, batch_id)
        elif file_type == 'word_old' or file_type == 'word_new':
            self._process_word_file(file_path, batch_id)
        elif file_type == 'access':
            self._process_access_file(file_path, batch_id)
        elif file_type == 'text':
            self._process_text_file(file_path, batch_id)
        elif file_type == 'csv':
            self._process_csv_file(file_path, batch_id)
        else:
            logger.warning(f"Unsupported file type: {file_type} for {file_path}")
    
    def _process_excel_file(self, file_path: Path, batch_id: int):
        """Process Excel files (.xls, .xlsx)."""
        try:
            # Try to read Excel file
            if file_path.suffix.lower() == '.xls':
                # Old Excel format
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                # New Excel format
                df = pd.read_excel(file_path, engine='openpyxl')
            
            logger.info(f"Read Excel file with {len(df)} rows and columns: {list(df.columns)}")
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    member_data = self._extract_member_from_excel_row(row, file_path)
                    if member_data:
                        self._import_member(member_data, batch_id)
                        self.stats['records_found'] += 1
                except Exception as e:
                    logger.warning(f"Error processing row {idx} in {file_path}: {e}")
            
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {e}")
            # Try alternative approach with strings extraction
            self._process_file_with_strings(file_path, batch_id)
    
    def _process_word_file(self, file_path: Path, batch_id: int):
        """Process Word documents (.doc, .docx)."""
        try:
            # Try python-docx for .docx files
            if file_path.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # For .doc files, fall back to strings extraction
                text = self._extract_text_with_strings(file_path)
            
            # Extract member records from text
            members = self._extract_members_from_text(text, file_path)
            
            for member_data in members:
                self._import_member(member_data, batch_id)
                self.stats['records_found'] += 1
                
        except Exception as e:
            logger.error(f"Error processing Word file {file_path}: {e}")
            # Fallback to strings extraction
            self._process_file_with_strings(file_path, batch_id)
    
    def _process_text_file(self, file_path: Path, batch_id: int):
        """Process text files."""
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            # Read text
            with open(file_path, 'r', encoding=encoding) as f:
                text = f.read()
            
            # Extract member data
            if 'names.txt' in file_path.name.lower():
                # Special handling for email list files
                self._process_email_list(text, file_path, batch_id)
            else:
                # General text processing
                members = self._extract_members_from_text(text, file_path)
                for member_data in members:
                    self._import_member(member_data, batch_id)
                    self.stats['records_found'] += 1
                    
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
    
    def _process_access_file(self, file_path: Path, batch_id: int):
        """Process Access database files (.mdb)."""
        # Access files are complex - for now, extract strings and parse
        logger.info(f"Processing Access file {file_path} with strings extraction")
        self._process_file_with_strings(file_path, batch_id)
    
    def _process_csv_file(self, file_path: Path, batch_id: int):
        """Process CSV files."""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Read CSV file with {len(df)} rows and columns: {list(df.columns)}")
            
            for idx, row in df.iterrows():
                try:
                    member_data = self._extract_member_from_excel_row(row, file_path)
                    if member_data:
                        self._import_member(member_data, batch_id)
                        self.stats['records_found'] += 1
                except Exception as e:
                    logger.warning(f"Error processing CSV row {idx}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
    
    def _process_file_with_strings(self, file_path: Path, batch_id: int):
        """Fallback method using strings extraction."""
        try:
            text = self._extract_text_with_strings(file_path)
            members = self._extract_members_from_text(text, file_path)
            
            for member_data in members:
                self._import_member(member_data, batch_id)
                self.stats['records_found'] += 1
                
        except Exception as e:
            logger.error(f"Error processing file with strings {file_path}: {e}")
    
    def _extract_text_with_strings(self, file_path: Path) -> str:
        """Extract text using system 'strings' command."""
        import subprocess
        try:
            result = subprocess.run(['strings', str(file_path)], 
                                  capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            logger.error(f"Error running strings on {file_path}: {e}")
            return ""
    
    def _extract_member_from_excel_row(self, row: pd.Series, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract member data from Excel row."""
        # This is a generic extractor - would need customization based on actual Excel structure
        member_data = {}
        
        # Try to map common column names
        for col in row.index:
            col_lower = str(col).lower()
            value = row[col]
            
            if pd.isna(value) or value == '':
                continue
                
            value = str(value).strip()
            
            # Name fields
            if any(name_field in col_lower for name_field in ['name', 'nome', 'apellido']):
                member_data['full_name'] = value
            elif 'nickname' in col_lower or 'nick' in col_lower:
                member_data['nickname'] = value
            
            # Contact fields
            elif 'email' in col_lower or '@' in value:
                member_data['primary_email'] = value
            elif any(phone_field in col_lower for phone_field in ['phone', 'mobile', 'cell', 'tel']):
                if 'home' in col_lower:
                    member_data['home_phone'] = value
                elif 'mobile' in col_lower or 'cell' in col_lower:
                    member_data['mobile_phone'] = value
                else:
                    member_data['mobile_phone'] = value
            
            # Address fields
            elif 'address' in col_lower:
                if 'home' in col_lower:
                    member_data['home_address_full'] = value
                elif 'office' in col_lower or 'work' in col_lower:
                    member_data['office_address_full'] = value
                else:
                    member_data['home_address_full'] = value
            
            # Professional fields
            elif any(prof_field in col_lower for prof_field in ['profession', 'job', 'work', 'occupation']):
                member_data['current_profession'] = value
            elif 'company' in col_lower or 'employer' in col_lower:
                member_data['current_company'] = value
            
            # Academic fields
            elif 'batch' in col_lower:
                member_data['batch_original'] = value
            elif 'chapter' in col_lower or 'school' in col_lower:
                member_data['school_chapter'] = value
            elif 'course' in col_lower:
                member_data['course'] = value
        
        # Only return if we have at least a name or email
        if member_data.get('full_name') or member_data.get('primary_email'):
            member_data.update(self._add_file_metadata(file_path))
            return member_data
        
        return None
    
    def _extract_members_from_text(self, text: str, file_path: Path) -> List[Dict[str, Any]]:
        """Extract member records from unstructured text."""
        members = []
        
        # Look for structured member records
        # Pattern 1: NAME: value format
        name_pattern = r'NAME:\s*([^\n]+)'
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        batch_pattern = r'BATCH[:\s]*([^\n]+)'
        profession_pattern = r'PROFESSION[:\s]*([^\n]+)'
        
        # Find all matches
        names = re.findall(name_pattern, text, re.IGNORECASE)
        emails = re.findall(email_pattern, text)
        batches = re.findall(batch_pattern, text, re.IGNORECASE)
        professions = re.findall(profession_pattern, text, re.IGNORECASE)
        
        # Try to correlate them (this is approximate)
        for i, name in enumerate(names):
            member_data = {
                'full_name': name.strip(),
                'batch_original': batches[i].strip() if i < len(batches) else None,
                'current_profession': professions[i].strip() if i < len(professions) else None
            }
            
            # Try to find corresponding email
            if i < len(emails):
                member_data['primary_email'] = emails[i]
            
            member_data.update(self._add_file_metadata(file_path))
            members.append(member_data)
        
        # Also extract standalone emails
        for email in emails:
            if not any(email in str(m.get('primary_email', '')) for m in members):
                member_data = {
                    'primary_email': email
                }
                member_data.update(self._add_file_metadata(file_path))
                members.append(member_data)
        
        return members
    
    def _process_email_list(self, text: str, file_path: Path, batch_id: int):
        """Process email list files like names.txt."""
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if '@' in line and '.' in line:  # Basic email validation
                member_data = {
                    'primary_email': line
                }
                member_data.update(self._add_file_metadata(file_path))
                self._import_member(member_data, batch_id)
                self.stats['records_found'] += 1
    
    def _add_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Add file metadata to member record."""
        file_stat = file_path.stat()
        
        return {
            'source_file_name': file_path.name,
            'source_file_creation_date': datetime.fromtimestamp(file_stat.st_ctime).date(),
            'source_file_modified_date': datetime.fromtimestamp(file_stat.st_mtime).date(),
            'imported_from_source': str(file_path),
            'estimated_data_vintage': self._estimate_data_vintage(file_path)
        }
    
    def _estimate_data_vintage(self, file_path: Path) -> date:
        """Estimate when the data was originally collected."""
        filename = file_path.name.lower()
        
        # Extract year from filename
        year_matches = re.findall(r'(19|20)\d{2}', filename)
        if year_matches:
            year = int(year_matches[0])
            return date(year, 1, 1)
        
        # Look for decade indicators
        if '90s' in filename or 'dekada90' in filename:
            return date(1995, 1, 1)  # Mid-90s
        
        # Fallback to file modification date
        file_stat = file_path.stat()
        return datetime.fromtimestamp(file_stat.st_mtime).date()
    
    def _import_member(self, member_data: Dict[str, Any], batch_id: int):
        """Import or update a member record."""
        try:
            # Normalize the data
            normalized_data = self._normalize_member_data(member_data)
            
            # Check for existing member
            existing_member = self._find_existing_member(normalized_data)
            
            if existing_member:
                # Update existing record
                updates = self._merge_member_data(existing_member, normalized_data)
                if updates:
                    self.db.update_member(existing_member['id'], updates)
                    self.stats['records_updated'] += 1
                    logger.debug(f"Updated member {existing_member['id']}")
                else:
                    logger.debug(f"No updates needed for member {existing_member['id']}")
            else:
                # Create new record
                member_id = self.db.insert_member(normalized_data)
                self.stats['records_imported'] += 1
                logger.debug(f"Created new member {member_id}")
                
        except Exception as e:
            logger.error(f"Error importing member: {e}")
            logger.error(f"Member data: {member_data}")
    
    def _normalize_member_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize member data using various processors."""
        normalized = raw_data.copy()
        
        # Normalize name
        if normalized.get('full_name'):
            normalized['full_name_normalized'] = self.text_processor.normalize_name(
                normalized['full_name']
            )
        
        # Normalize batch
        if normalized.get('batch_original'):
            batch_info = self.text_processor.normalize_batch(normalized['batch_original'])
            normalized.update(batch_info)
        
        # Normalize locations
        if normalized.get('home_address_full'):
            home_city = self.text_processor.extract_city(normalized['home_address_full'])
            normalized['home_address_city'] = home_city
            normalized['home_address_city_normalized'] = self.text_processor.normalize_location(home_city)
        
        if normalized.get('office_address_full'):
            office_city = self.text_processor.extract_city(normalized['office_address_full'])
            normalized['office_address_city'] = office_city
            normalized['office_address_city_normalized'] = self.text_processor.normalize_location(office_city)
        
        # AI inference
        if Config.USE_AI_INFERENCE:
            ai_results = self.ai_inferencer.infer_profession_info(normalized)
            normalized.update(ai_results)
        
        # Calculate data quality scores
        normalized['data_completeness_score'] = self._calculate_completeness_score(normalized)
        normalized['confidence_score'] = self._calculate_confidence_score(normalized)
        
        return normalized
    
    def _find_existing_member(self, member_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find existing member by email or name similarity."""
        # First try exact email match
        if member_data.get('primary_email'):
            results = self.db.search_members({
                'email': member_data['primary_email']
            })
            if results:
                return results[0]
        
        # Then try name similarity
        if member_data.get('full_name_normalized'):
            results = self.db.search_members({
                'name': member_data['full_name_normalized']
            })
            
            # Use fuzzy matching to find close matches
            for result in results:
                similarity = self.text_processor.calculate_name_similarity(
                    member_data['full_name_normalized'],
                    result['full_name_normalized']
                )
                if similarity > 0.8:  # 80% similarity threshold
                    return result
        
        return None
    
    def _merge_member_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge new data with existing member data."""
        updates = {}
        
        # Update fields that are missing or have newer data
        for field, new_value in new.items():
            if field in ['id', 'created_at', 'updated_at']:
                continue
                
            if new_value is None:
                continue
                
            existing_value = existing.get(field)
            
            # Always update if existing field is empty
            if not existing_value:
                updates[field] = new_value
                continue
            
            # For dates, keep the more recent one
            if 'collected_date' in field:
                if isinstance(new_value, (date, datetime)):
                    if not existing_value or new_value > existing_value:
                        updates[field] = new_value
                continue
            
            # For confidence scores, keep higher confidence
            if 'confidence' in field:
                if float(new_value) > float(existing_value or 0):
                    updates[field] = new_value
                continue
            
            # For other fields, prefer longer/more complete values
            if len(str(new_value)) > len(str(existing_value)):
                updates[field] = new_value
        
        return updates
    
    def _calculate_completeness_score(self, member_data: Dict[str, Any]) -> float:
        """Calculate data completeness score (0.0 to 1.0)."""
        required_fields = [
            'full_name', 'primary_email', 'mobile_phone', 
            'current_profession', 'school_chapter', 'batch_normalized'
        ]
        
        filled_count = sum(1 for field in required_fields 
                          if member_data.get(field))
        
        return filled_count / len(required_fields)
    
    def _calculate_confidence_score(self, member_data: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the record."""
        score = 0.0
        
        # Base score from completeness
        score += member_data.get('data_completeness_score', 0) * 0.4
        
        # Bonus for verified email
        if member_data.get('primary_email') and '@' in member_data['primary_email']:
            score += 0.2
        
        # Bonus for profession information
        if member_data.get('current_profession'):
            score += 0.2
        
        # Bonus for batch information
        if member_data.get('batch_normalized'):
            score += 0.1
        
        # Factor in AI inference confidence
        ai_confidence = member_data.get('inferred_profession_confidence', 0)
        score += ai_confidence * 0.1
        
        return min(score, 1.0)  # Cap at 1.0