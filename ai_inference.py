# SJ Professional Directory - AI-Powered Profession Inference
# ============================================================================

import logging
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime

from config import PROFESSION_KEYWORDS, COMPANY_DOMAINS

logger = logging.getLogger(__name__)

class ProfessionInferencer:
    """AI-powered profession and service inference engine."""
    
    def __init__(self):
        self.profession_keywords = PROFESSION_KEYWORDS
        self.company_domains = COMPANY_DOMAINS
        
        # Build keyword-to-profession mappings
        self.keyword_mapping = {}
        for profession, keywords in self.profession_keywords.items():
            for keyword in keywords:
                self.keyword_mapping[keyword.lower()] = profession
    
    def infer_profession_info(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Infer profession information from available member data."""
        inference_results = {}
        
        # Collect all text data for analysis
        text_sources = []
        
        # Email domain analysis
        email = member_data.get('primary_email', '')
        if email:
            domain_info = self._analyze_email_domain(email)
            if domain_info:
                text_sources.append(('email_domain', domain_info))
        
        # Company name analysis
        company = member_data.get('current_company', '')
        if company:
            text_sources.append(('company_name', company))
        
        # Job title analysis
        profession = member_data.get('current_profession', '')
        if profession:
            text_sources.append(('job_title', profession))
        
        # Address analysis
        office_address = member_data.get('office_address_full', '')
        if office_address:
            text_sources.append(('office_address', office_address))
        
        # Analyze each source
        profession_scores = {}
        specialization_hints = []
        location_hints = []
        
        for source_type, text in text_sources:
            analysis = self._analyze_text_for_profession(text, source_type)
            
            # Aggregate profession scores
            for profession, score in analysis.get('profession_scores', {}).items():
                if profession not in profession_scores:
                    profession_scores[profession] = []
                profession_scores[profession].append((score, source_type))
            
            # Collect specializations and locations
            specialization_hints.extend(analysis.get('specializations', []))
            location_hints.extend(analysis.get('locations', []))
        
        # Determine best profession match
        best_profession, best_confidence = self._determine_best_profession(profession_scores)
        
        if best_profession and best_confidence >= 0.5:
            inference_results['inferred_profession'] = best_profession
            inference_results['inferred_profession_confidence'] = best_confidence
            inference_results['inferred_profession_source'] = 'ai_analysis'
            
            # Map to service category
            inference_results['inferred_service_category'] = best_profession
            inference_results['inferred_service_category_confidence'] = best_confidence
        
        # Infer specialization
        if specialization_hints:
            specialization = self._determine_specialization(specialization_hints, best_profession)
            if specialization:
                inference_results['inferred_specialization'] = specialization
                inference_results['inferred_specialization_confidence'] = 0.7
        
        # Infer work location
        if location_hints:
            work_location = self._determine_work_location(location_hints, member_data)
            if work_location:
                inference_results['inferred_work_location'] = work_location
                inference_results['inferred_work_location_confidence'] = 0.8
        
        return inference_results
    
    def _analyze_email_domain(self, email: str) -> Optional[str]:
        """Analyze email domain for profession clues."""
        if '@' not in email:
            return None
        
        domain = email.split('@')[1].lower()
        
        # Check known company domains
        if domain in self.company_domains:
            company = self.company_domains[domain]
            if company:
                return company
        
        # Analyze domain structure
        domain_parts = domain.split('.')
        
        # Educational institutions
        if 'edu' in domain_parts:
            return 'educational institution'
        
        # Government
        if 'gov' in domain_parts:
            return 'government agency'
        
        # Medical
        medical_indicators = ['hospital', 'medical', 'clinic', 'health']
        if any(indicator in domain for indicator in medical_indicators):
            return 'medical institution'
        
        # Legal
        legal_indicators = ['law', 'legal', 'attorney']
        if any(indicator in domain for indicator in legal_indicators):
            return 'law firm'
        
        # Business/Corporate
        business_indicators = ['corp', 'inc', 'company', 'consulting', 'group']
        if any(indicator in domain for indicator in business_indicators):
            return 'business corporation'
        
        return None
    
    def _analyze_text_for_profession(self, text: str, source_type: str) -> Dict[str, Any]:
        """Analyze text for profession indicators."""
        if not text:
            return {}
        
        text_lower = text.lower()
        results = {
            'profession_scores': {},
            'specializations': [],
            'locations': []
        }
        
        # Score each profession based on keyword matches
        for profession, keywords in self.profession_keywords.items():
            score = 0.0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # Weight scores based on source type
                    weight = self._get_source_weight(source_type, keyword)
                    score += weight
                    matched_keywords.append(keyword)
            
            if score > 0:
                # Normalize score
                max_possible_score = len(keywords) * self._get_source_weight(source_type, '')
                normalized_score = min(score / max_possible_score, 1.0)
                results['profession_scores'][profession] = normalized_score
        
        # Extract specializations
        specializations = self._extract_specializations(text_lower)
        results['specializations'] = specializations
        
        # Extract location hints
        locations = self._extract_location_hints(text_lower)
        results['locations'] = locations
        
        return results
    
    def _get_source_weight(self, source_type: str, keyword: str) -> float:
        """Get weight for profession score based on source type."""
        weights = {
            'job_title': 1.0,      # Job title is most reliable
            'company_name': 0.8,   # Company name is quite reliable
            'email_domain': 0.6,   # Email domain gives good hints
            'office_address': 0.4, # Office address gives some hints
        }
        
        base_weight = weights.get(source_type, 0.5)
        
        # Boost for high-confidence keywords
        high_confidence_keywords = [
            'doctor', 'physician', 'lawyer', 'attorney', 'engineer', 
            'professor', 'teacher', 'manager', 'director', 'ceo'
        ]
        
        if keyword.lower() in high_confidence_keywords:
            base_weight *= 1.5
        
        return base_weight
    
    def _extract_specializations(self, text: str) -> List[str]:
        """Extract profession specializations from text."""
        specializations = []
        
        # Medical specializations
        medical_specs = [
            'cardiology', 'cardiologist', 'pediatrics', 'pediatrician',
            'neurology', 'neurologist', 'surgery', 'surgeon',
            'dermatology', 'dermatologist', 'ophthalmology', 'ophthalmologist',
            'psychiatry', 'psychiatrist', 'radiology', 'radiologist'
        ]
        
        # Legal specializations
        legal_specs = [
            'family law', 'corporate law', 'criminal law', 'tax law',
            'labor law', 'real estate law', 'intellectual property',
            'litigation', 'corporate counsel'
        ]
        
        # Engineering specializations
        engineering_specs = [
            'civil engineering', 'electrical engineering', 'mechanical engineering',
            'chemical engineering', 'software engineering', 'systems engineering',
            'construction', 'architecture'
        ]
        
        # Business specializations
        business_specs = [
            'accounting', 'finance', 'marketing', 'human resources',
            'operations', 'consulting', 'strategy', 'business development'
        ]
        
        all_specs = medical_specs + legal_specs + engineering_specs + business_specs
        
        for spec in all_specs:
            if spec in text:
                specializations.append(spec)
        
        return list(set(specializations))  # Remove duplicates
    
    def _extract_location_hints(self, text: str) -> List[str]:
        """Extract location hints from text."""
        locations = []
        
        # Philippine cities and regions
        ph_locations = [
            'makati', 'manila', 'quezon city', 'pasig', 'taguig', 'mandaluyong',
            'pasay', 'paranaque', 'las pinas', 'muntinlupa', 'marikina',
            'cebu', 'davao', 'iloilo', 'bacolod', 'cagayan de oro',
            'ortigas', 'bgc', 'alabang', 'eastwood', 'rockwell'
        ]
        
        for location in ph_locations:
            if location in text:
                locations.append(location.title())
        
        return list(set(locations))
    
    def _determine_best_profession(self, profession_scores: Dict[str, List[Tuple[float, str]]]) -> Tuple[Optional[str], float]:
        """Determine the best profession match from aggregated scores."""
        if not profession_scores:
            return None, 0.0
        
        # Calculate weighted average for each profession
        final_scores = {}
        
        for profession, score_sources in profession_scores.items():
            if not score_sources:
                continue
            
            # Calculate weighted average
            total_weight = 0
            weighted_sum = 0
            
            for score, source_type in score_sources:
                weight = self._get_source_weight(source_type, '')
                weighted_sum += score * weight
                total_weight += weight
            
            if total_weight > 0:
                final_scores[profession] = weighted_sum / total_weight
        
        if not final_scores:
            return None, 0.0
        
        # Get the best match
        best_profession = max(final_scores, key=final_scores.get)
        best_score = final_scores[best_profession]
        
        return best_profession, best_score
    
    def _determine_specialization(self, specialization_hints: List[str], profession: Optional[str]) -> Optional[str]:
        """Determine the most likely specialization."""
        if not specialization_hints:
            return None
        
        # Filter specializations relevant to the profession
        relevant_specs = []
        
        if profession == 'Medical':
            medical_keywords = ['cardio', 'pediatr', 'neuro', 'surg', 'dermat', 'ophthal', 'psych', 'radio']
            relevant_specs = [spec for spec in specialization_hints 
                            if any(keyword in spec.lower() for keyword in medical_keywords)]
        elif profession == 'Legal':
            legal_keywords = ['law', 'legal', 'litigation', 'counsel']
            relevant_specs = [spec for spec in specialization_hints
                            if any(keyword in spec.lower() for keyword in legal_keywords)]
        elif profession == 'Engineering':
            engineering_keywords = ['engineering', 'engineer', 'construction', 'architect']
            relevant_specs = [spec for spec in specialization_hints
                            if any(keyword in spec.lower() for keyword in engineering_keywords)]
        
        if relevant_specs:
            # Return the most specific specialization
            return max(relevant_specs, key=len)
        elif specialization_hints:
            # Return the first specialization if no profession-specific match
            return specialization_hints[0]
        
        return None
    
    def _determine_work_location(self, location_hints: List[str], member_data: Dict[str, Any]) -> Optional[str]:
        """Determine the most likely work location."""
        if not location_hints:
            return None
        
        # Prefer locations from office address
        office_address = member_data.get('office_address_full', '').lower()
        for location in location_hints:
            if location.lower() in office_address:
                return location
        
        # Otherwise, return the first location hint
        return location_hints[0]
    
    def infer_address_type(self, address: str) -> str:
        """Infer whether an address is residential or professional."""
        if not address:
            return 'unknown'
        
        address_lower = address.lower()
        
        # Professional indicators
        professional_indicators = [
            'office', 'building', 'tower', 'plaza', 'center', 'centre',
            'floor', 'suite', 'room', 'unit', 'hospital', 'clinic',
            'law office', 'firm', 'corporation', 'company', 'inc',
            'makati cbd', 'ortigas center', 'bgc', 'eastwood'
        ]
        
        # Residential indicators
        residential_indicators = [
            'subdivision', 'village', 'homes', 'residence', 'street',
            'avenue', 'road', 'barangay', 'district', 'blk', 'lot'
        ]
        
        professional_score = sum(1 for indicator in professional_indicators 
                               if indicator in address_lower)
        residential_score = sum(1 for indicator in residential_indicators 
                              if indicator in address_lower)
        
        if professional_score > residential_score:
            return 'professional'
        elif residential_score > professional_score:
            return 'residential'
        else:
            return 'mixed'