# SJ Professional Directory - Text Processing and Normalization
# ============================================================================

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import date
from fuzzywuzzy import fuzz
import unicodedata

from config import LOCATION_MAPPINGS, BATCH_PATTERNS

logger = logging.getLogger(__name__)

class TextProcessor:
    """Handles text normalization, extraction, and fuzzy matching."""
    
    def __init__(self):
        self.name_prefixes = ['dr', 'dr.', 'atty', 'atty.', 'eng', 'eng.', 'prof', 'prof.']
        self.name_suffixes = ['jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv', 'md', 'pe', 'esq']
    
    def normalize_name(self, name: str) -> str:
        """Normalize a person's name for consistent matching."""
        if not name:
            return ""
        
        # Remove extra whitespace and convert to title case
        name = ' '.join(name.strip().split())
        
        # Remove common prefixes and suffixes for comparison
        words = name.lower().split()
        cleaned_words = []
        
        for word in words:
            # Skip prefixes/suffixes but keep the core name
            if word not in self.name_prefixes and word not in self.name_suffixes:
                cleaned_words.append(word)
        
        # Return the cleaned, lowercase version for matching
        return ' '.join(cleaned_words).lower()
    
    def normalize_batch(self, batch_str: str) -> Dict[str, Any]:
        """Normalize batch information into structured components."""
        if not batch_str:
            return {}
        
        result = {
            'batch_original': batch_str,
            'batch_normalized': None,
            'batch_year': None,
            'batch_semester': None,
            'batch_sub_number': None,
            'batch_decade': None,
            'batch_era': None
        }
        
        # Try each pattern
        for pattern in BATCH_PATTERNS:
            match = re.search(pattern, batch_str, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 1:
                    # Extract year
                    year_str = groups[0]
                    year = int(year_str)
                    
                    # Convert 2-digit to 4-digit year
                    if year < 50:
                        year += 2000  # 01-49 = 2001-2049
                    elif year < 100:
                        year += 1900  # 50-99 = 1950-1999
                    
                    result['batch_year'] = year
                    result['batch_decade'] = (year // 10) * 10
                    
                    # Determine era
                    if 1990 <= year < 2000:
                        result['batch_era'] = '90s'
                    elif 2000 <= year < 2010:
                        result['batch_era'] = '2000s'
                    elif 2010 <= year < 2020:
                        result['batch_era'] = '2010s'
                    else:
                        result['batch_era'] = f"{year}s"
                
                if len(groups) >= 2:
                    # Extract letter/semester code
                    semester_str = groups[1]
                    
                    # Extract letter and number components
                    letter_match = re.match(r'([A-Z]+)(\d*)', semester_str, re.IGNORECASE)
                    if letter_match:
                        result['batch_semester'] = letter_match.group(1).upper()
                        if letter_match.group(2):
                            result['batch_sub_number'] = int(letter_match.group(2))
                
                # Build normalized format
                if result['batch_year'] and result['batch_semester']:
                    normalized = f"{result['batch_year']}-{result['batch_semester']}"
                    if result['batch_sub_number']:
                        normalized += str(result['batch_sub_number'])
                    result['batch_normalized'] = normalized
                elif result['batch_year']:
                    result['batch_normalized'] = str(result['batch_year'])
                
                break
        
        return result
    
    def normalize_location(self, location: str) -> str:
        """Normalize location names for consistent matching."""
        if not location:
            return ""
        
        # Clean and standardize
        location = location.strip().title()
        
        # Apply mappings
        for abbrev, full_name in LOCATION_MAPPINGS.items():
            if abbrev.lower() in location.lower():
                location = location.replace(abbrev, full_name)
        
        # Remove common suffixes
        location = re.sub(r'\s+(City|Municipality|Town)$', '', location, flags=re.IGNORECASE)
        
        return location.strip()
    
    def extract_city(self, address: str) -> str:
        """Extract city name from full address."""
        if not address:
            return ""
        
        # Common patterns for Philippine addresses
        # Look for city patterns
        city_patterns = [
            r'([A-Za-z\s]+)\s+City',
            r'([A-Za-z\s]+),\s*Metro Manila',
            r'([A-Za-z\s]+),\s*Philippines',
            r'([A-Za-z\s]+),\s*\d{4}',  # City with zip code
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, address)
            if match:
                return match.group(1).strip()
        
        # Fallback: take the last significant word before common address endings
        words = address.split()
        for i, word in enumerate(reversed(words)):
            if word.lower() not in ['philippines', 'manila', 'metro', 'st', 'street', 'ave', 'avenue']:
                return word
        
        return ""
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (0.0 to 1.0)."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize both names
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        # Use fuzzy matching
        ratio = fuzz.ratio(norm1, norm2) / 100.0
        
        # Also try token sort ratio for different word orders
        token_ratio = fuzz.token_sort_ratio(norm1, norm2) / 100.0
        
        # Return the higher score
        return max(ratio, token_ratio)
    
    def extract_email_domain_info(self, email: str) -> Dict[str, Any]:
        """Extract information from email domain."""
        if not email or '@' not in email:
            return {}
        
        domain = email.split('@')[1].lower()
        
        # Check for institutional domains
        if domain.endswith('.edu.ph') or domain.endswith('.edu'):
            return {
                'domain_type': 'educational',
                'inferred_sector': 'Education'
            }
        elif domain.endswith('.gov.ph') or domain.endswith('.gov'):
            return {
                'domain_type': 'government',
                'inferred_sector': 'Government'
            }
        elif 'hospital' in domain or 'medical' in domain or 'clinic' in domain:
            return {
                'domain_type': 'medical',
                'inferred_sector': 'Medical'
            }
        elif any(corp in domain for corp in ['corp', 'inc', 'company', 'business']):
            return {
                'domain_type': 'corporate',
                'inferred_sector': 'Business'
            }
        elif domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
            return {
                'domain_type': 'personal',
                'inferred_sector': None
            }
        else:
            return {
                'domain_type': 'unknown',
                'inferred_sector': None
            }
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        # Philippine phone number patterns
        patterns = [
            r'\+63\s?\d{2}\s?\d{3}\s?\d{4}',  # +63 format
            r'0\d{2}-\d{3}-\d{4}',           # 0XX-XXX-XXXX
            r'0\d{3}-\d{3}-\d{3}',           # 0XXX-XXX-XXX
            r'\(\d{2,3}\)\s?\d{3}-?\d{4}',   # (XX) XXX-XXXX
            r'\d{3}-\d{4}',                  # XXX-XXXX (landline)
            r'09\d{2}-\d{3}-\d{4}',          # Mobile format
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)
        
        return list(set(numbers))  # Remove duplicates
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        return text.strip()
    
    def extract_professional_keywords(self, text: str) -> List[str]:
        """Extract potential professional keywords from text."""
        if not text:
            return []
        
        # Common professional terms
        professional_terms = [
            # Legal
            'lawyer', 'attorney', 'counsel', 'legal', 'law', 'litigation',
            'corporate law', 'family law', 'criminal law', 'real estate law',
            
            # Medical
            'doctor', 'physician', 'surgeon', 'medical', 'clinic', 'hospital',
            'cardiologist', 'pediatrician', 'neurologist', 'dentist',
            
            # Business
            'manager', 'executive', 'consultant', 'analyst', 'director',
            'ceo', 'cfo', 'coo', 'president', 'vice president',
            
            # Engineering
            'engineer', 'engineering', 'architect', 'construction',
            'civil engineer', 'electrical engineer', 'mechanical engineer',
            
            # IT
            'programmer', 'developer', 'software', 'systems', 'network',
            'database', 'web developer', 'system administrator',
            
            # Education
            'teacher', 'professor', 'educator', 'principal', 'dean',
            'instructor', 'lecturer', 'researcher',
            
            # Others
            'accountant', 'banker', 'broker', 'agent', 'specialist'
        ]
        
        text_lower = text.lower()
        found_terms = []
        
        for term in professional_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def parse_structured_text(self, text: str) -> Dict[str, str]:
        """Parse structured text with field labels."""
        if not text:
            return {}
        
        fields = {}
        
        # Common field patterns
        field_patterns = {
            'name': r'(?:NAME|Full Name|NOMBRE)[:\s]*([^\n]+)',
            'nickname': r'(?:NICKNAME|Nick)[:\s]*([^\n]+)',
            'email': r'(?:EMAIL|E-MAIL)[:\s]*([^\n]+)',
            'phone': r'(?:PHONE|TEL|MOBILE|CELL)[:\s]*([^\n]+)',
            'address': r'(?:ADDRESS|Home Address)[:\s]*([^\n]+)',
            'profession': r'(?:PROFESSION|JOB|WORK|OCCUPATION)[:\s]*([^\n]+)',
            'company': r'(?:COMPANY|EMPLOYER|OFFICE)[:\s]*([^\n]+)',
            'batch': r'(?:BATCH|Batch No)[:\s]*([^\n]+)',
            'chapter': r'(?:CHAPTER|School)[:\s]*([^\n]+)',
        }
        
        for field_name, pattern in field_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if value:
                    fields[field_name] = value
        
        return fields