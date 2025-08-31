# SJ Professional Directory - Natural Language Query Processing
# ============================================================================

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from fuzzywuzzy import fuzz

from database import DatabaseManager
from config import PROFESSION_KEYWORDS

logger = logging.getLogger(__name__)

class QueryProcessor:
    """Processes natural language queries for professional services and directory searches."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # Query pattern mappings
        self.profession_patterns = self._build_profession_patterns()
        self.location_patterns = self._build_location_patterns()
        self.service_patterns = self._build_service_patterns()
    
    def search_professional_services(self, query: str) -> List[Dict[str, Any]]:
        """Search for professional services based on natural language query."""
        logger.info(f"Processing professional services query: {query}")
        
        # Parse the query
        query_components = self._parse_professional_query(query)
        
        # Build search parameters
        search_params = self._build_search_params(query_components)
        
        # Execute search
        results = self.db.search_members(search_params)
        
        # Rank and filter results
        ranked_results = self._rank_professional_results(results, query_components)
        
        # Format results for display
        formatted_results = self._format_professional_results(ranked_results, query_components)
        
        return formatted_results
    
    def search_directory(self, query: str) -> List[Dict[str, Any]]:
        """Search directory for members based on natural language query."""
        logger.info(f"Processing directory query: {query}")
        
        # Parse the query
        query_components = self._parse_directory_query(query)
        
        # Build search parameters
        search_params = self._build_search_params(query_components)
        
        # Execute search
        results = self.db.search_members(search_params)
        
        # Format results
        formatted_results = self._format_directory_results(results, query_components)
        
        return formatted_results
    
    def _parse_professional_query(self, query: str) -> Dict[str, Any]:
        """Parse professional services query into components."""
        query_lower = query.lower()
        components = {
            'profession': None,
            'specialization': None,
            'location': None,
            'urgency': 'normal',
            'query_type': 'professional_service',
            'original_query': query
        }
        
        # Extract profession
        profession = self._extract_profession(query_lower)
        if profession:
            components['profession'] = profession
        
        # Extract location
        location = self._extract_location(query_lower)
        if location:
            components['location'] = location
        
        # Extract specialization
        specialization = self._extract_specialization(query_lower, profession)
        if specialization:
            components['specialization'] = specialization
        
        # Detect urgency
        urgency_indicators = ['urgent', 'asap', 'emergency', 'immediately', 'need now']
        if any(indicator in query_lower for indicator in urgency_indicators):
            components['urgency'] = 'urgent'
        
        return components
    
    def _parse_directory_query(self, query: str) -> Dict[str, Any]:
        """Parse directory search query into components."""
        query_lower = query.lower()
        components = {
            'name': None,
            'batch': None,
            'chapter': None,
            'profession': None,
            'location': None,
            'query_type': 'directory_search',
            'original_query': query
        }
        
        # Extract name (if quoted or specific patterns)
        name_match = re.search(r'["\'](.*?)["\']', query)
        if name_match:
            components['name'] = name_match.group(1)
        else:
            # Look for name patterns
            name_patterns = [
                r'find\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'looking for\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'contact\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
            ]
            for pattern in name_patterns:
                match = re.search(pattern, query)
                if match:
                    components['name'] = match.group(1)
                    break
        
        # Extract batch
        batch = self._extract_batch(query_lower)
        if batch:
            components['batch'] = batch
        
        # Extract chapter
        chapter = self._extract_chapter(query_lower)
        if chapter:
            components['chapter'] = chapter
        
        # Extract profession (for directory searches too)
        profession = self._extract_profession(query_lower)
        if profession:
            components['profession'] = profession
        
        # Extract location
        location = self._extract_location(query_lower)
        if location:
            components['location'] = location
        
        return components
    
    def _extract_profession(self, query: str) -> Optional[str]:
        """Extract profession from query text."""
        # Direct profession matches
        for profession, keywords in PROFESSION_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in query:
                    return profession
        
        # Common profession synonyms
        profession_synonyms = {
            'Legal': ['lawyer', 'attorney', 'legal advice', 'legal help', 'counsel'],
            'Medical': ['doctor', 'physician', 'medical help', 'healthcare', 'health'],
            'Engineering': ['engineer', 'engineering services', 'technical'],
            'Business': ['business consultant', 'financial advisor', 'accountant'],
            'IT/Technology': ['programmer', 'developer', 'it support', 'tech help']
        }
        
        for profession, synonyms in profession_synonyms.items():
            for synonym in synonyms:
                if synonym in query:
                    return profession
        
        return None
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query text."""
        # Philippine locations
        ph_locations = [
            'makati', 'manila', 'quezon city', 'qc', 'pasig', 'taguig', 'bgc',
            'mandaluyong', 'pasay', 'paranaque', 'las pinas', 'muntinlupa',
            'marikina', 'ortigas', 'alabang', 'eastwood', 'rockwell',
            'cebu', 'davao', 'iloilo', 'bacolod', 'cagayan de oro',
            'bulacan', 'cavite', 'laguna', 'rizal', 'batangas'
        ]
        
        # Location patterns
        location_patterns = [
            r'in\s+([a-z\s]+?)(?:\s|$)',
            r'at\s+([a-z\s]+?)(?:\s|$)',
            r'near\s+([a-z\s]+?)(?:\s|$)',
            r'from\s+([a-z\s]+?)(?:\s|$)',
            r'based in\s+([a-z\s]+?)(?:\s|$)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                match = match.strip()
                for location in ph_locations:
                    if location in match or fuzz.ratio(location, match) > 80:
                        return location.title()
        
        # Direct location mentions
        for location in ph_locations:
            if location in query:
                return location.title()
        
        return None
    
    def _extract_specialization(self, query: str, profession: Optional[str]) -> Optional[str]:
        """Extract specialization from query text."""
        if not profession:
            return None
        
        specialization_patterns = {
            'Legal': {
                'family law': ['family', 'divorce', 'custody', 'marriage'],
                'corporate law': ['corporate', 'business law', 'company'],
                'criminal law': ['criminal', 'defense'],
                'real estate law': ['real estate', 'property'],
                'labor law': ['labor', 'employment']
            },
            'Medical': {
                'cardiology': ['heart', 'cardiac', 'cardio'],
                'pediatrics': ['children', 'kids', 'pediatric'],
                'neurology': ['brain', 'neurological', 'neuro'],
                'dermatology': ['skin', 'dermat'],
                'psychiatry': ['mental health', 'psychiatric', 'therapy']
            },
            'Engineering': {
                'civil engineering': ['civil', 'construction', 'building'],
                'electrical engineering': ['electrical', 'power', 'electronics'],
                'mechanical engineering': ['mechanical', 'machinery'],
                'software engineering': ['software', 'programming']
            }
        }
        
        if profession in specialization_patterns:
            for specialization, keywords in specialization_patterns[profession].items():
                for keyword in keywords:
                    if keyword in query:
                        return specialization
        
        return None
    
    def _extract_batch(self, query: str) -> Optional[str]:
        """Extract batch information from query."""
        batch_patterns = [
            r'batch\s+(\d{2,4}[-\s]*[A-Z]*\d*)',
            r'(\d{2,4}[-\s]*[A-Z]+\d*)',
            r'(\d{4})\s+batch',
            r'batch\s+(\d{4})'
        ]
        
        for pattern in batch_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_chapter(self, query: str) -> Optional[str]:
        """Extract chapter information from query."""
        chapters = [
            'up diliman', 'upd', 'diliman',
            'up los banos', 'uplb', 'los banos',
            'up cebu', 'upc', 'cebu',
            'up iloilo', 'upi', 'iloilo',
            'ust', 'santo tomas',
            'feu', 'far eastern',
            'ue', 'university of the east',
            'lyceum'
        ]
        
        query_lower = query.lower()
        for chapter in chapters:
            if chapter in query_lower:
                return chapter.title()
        
        return None
    
    def _build_search_params(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Build database search parameters from query components."""
        params = {}
        
        if components.get('name'):
            params['name'] = components['name']
        
        if components.get('profession'):
            profession = components['profession']
            # Map profession categories back to searchable terms
            profession_mappings = {
                'Legal': 'lawyer',
                'Medical': 'doctor',
                'Engineering': 'engineer',
                'Business': 'manager',
                'IT/Technology': 'programmer',
                'Education': 'teacher',
                'Government': 'government'
            }
            params['profession'] = profession_mappings.get(profession, profession.lower())
        
        if components.get('location'):
            params['location'] = components['location']
        
        if components.get('batch'):
            params['batch'] = components['batch']
        
        if components.get('chapter'):
            params['chapter'] = components['chapter']
        
        return params
    
    def _rank_professional_results(self, results: List[Dict[str, Any]], 
                                 query_components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank professional service results by relevance."""
        if not results:
            return []
        
        scored_results = []
        
        for result in results:
            score = self._calculate_professional_relevance_score(result, query_components)
            scored_results.append((result, score))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [result for result, score in scored_results]
    
    def _calculate_professional_relevance_score(self, member: Dict[str, Any], 
                                              query_components: Dict[str, Any]) -> float:
        """Calculate relevance score for professional service matching."""
        score = 0.0
        
        # Base confidence score
        confidence = member.get('confidence_score', 0.5)
        score += confidence * 0.3
        
        # Profession match
        query_profession = query_components.get('profession', '').lower()
        member_profession = (member.get('current_profession_normalized') or '').lower()
        inferred_profession = (member.get('inferred_profession') or '').lower()
        
        if query_profession:
            if query_profession in member_profession:
                score += 0.4
            elif query_profession in inferred_profession:
                score += 0.3
            else:
                # Fuzzy match
                prof_similarity = max(
                    fuzz.ratio(query_profession, member_profession),
                    fuzz.ratio(query_profession, inferred_profession)
                ) / 100.0
                score += prof_similarity * 0.2
        
        # Location match
        query_location = (query_components.get('location') or '').lower()
        member_work_location = (member.get('office_address_city_normalized') or '').lower()
        member_home_location = (member.get('home_address_city_normalized') or '').lower()
        
        if query_location:
            if query_location in member_work_location:
                score += 0.25  # Work location is more relevant
            elif query_location in member_home_location:
                score += 0.15  # Home location is less relevant
            else:
                # Fuzzy location match
                loc_similarity = max(
                    fuzz.ratio(query_location, member_work_location),
                    fuzz.ratio(query_location, member_home_location)
                ) / 100.0
                score += loc_similarity * 0.1
        
        # Data freshness bonus
        estimated_vintage = member.get('estimated_data_vintage')
        if estimated_vintage:
            try:
                from datetime import date, datetime
                # Handle both string and date objects
                if isinstance(estimated_vintage, str):
                    if estimated_vintage.startswith('0020'):  # Fix obviously wrong dates
                        vintage_date = date(2020, 1, 1)  # Default to reasonable date
                    else:
                        vintage_date = datetime.strptime(estimated_vintage, '%Y-%m-%d').date()
                elif isinstance(estimated_vintage, date):
                    vintage_date = estimated_vintage
                else:
                    vintage_date = None
                
                if vintage_date:
                    days_old = (date.today() - vintage_date).days
                    if days_old < 365:  # Less than 1 year old
                        score += 0.05
                    elif days_old < 1825:  # Less than 5 years old
                        score += 0.02
            except (ValueError, TypeError):
                # If date parsing fails, skip the freshness bonus
                pass
        
        # Contact availability bonus
        if member.get('primary_email'):
            score += 0.05
        if member.get('mobile_phone'):
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _format_professional_results(self, results: List[Dict[str, Any]], 
                                   query_components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format professional service results for display."""
        formatted_results = []
        
        for member in results:
            # Calculate match explanation
            match_reasons = self._generate_match_explanation(member, query_components)
            
            formatted_result = {
                'id': member['id'],
                'name': member['full_name'],
                'nickname': member.get('nickname'),
                'profession': member.get('current_profession') or member.get('inferred_profession'),
                'company': member.get('current_company'),
                'work_location': member.get('office_address_city_normalized'),
                'home_location': member.get('home_address_city_normalized'),
                'email': member.get('primary_email'),
                'mobile': member.get('mobile_phone'),
                'batch': member.get('batch_normalized'),
                'chapter': member.get('school_chapter'),
                'confidence_score': member.get('confidence_score', 0),
                'data_vintage': member.get('estimated_data_vintage'),
                'match_reasons': match_reasons,
                'result_type': 'professional_service'
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results[:20]  # Limit to top 20 results
    
    def _format_directory_results(self, results: List[Dict[str, Any]], 
                                query_components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format directory search results for display."""
        formatted_results = []
        
        for member in results:
            formatted_result = {
                'id': member['id'],
                'name': member['full_name'],
                'nickname': member.get('nickname'),
                'email': member.get('primary_email'),
                'mobile': member.get('mobile_phone'),
                'home_phone': member.get('home_phone'),
                'profession': member.get('current_profession'),
                'company': member.get('current_company'),
                'batch': member.get('batch_normalized'),
                'chapter': member.get('school_chapter'),
                'home_address': member.get('home_address_city_normalized'),
                'work_address': member.get('office_address_city_normalized'),
                'confidence_score': member.get('confidence_score', 0),
                'result_type': 'directory_search'
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results[:50]  # Limit to top 50 results
    
    def _generate_match_explanation(self, member: Dict[str, Any], 
                                  query_components: Dict[str, Any]) -> List[str]:
        """Generate explanation of why this member matches the query."""
        reasons = []
        
        # Profession match
        query_profession = query_components.get('profession', '').lower()
        member_profession = (member.get('current_profession_normalized') or '').lower()
        if query_profession and query_profession in member_profession:
            reasons.append(f"Works as {member.get('current_profession')}")
        elif member.get('inferred_profession'):
            reasons.append(f"Likely works in {member.get('inferred_profession')} (AI inferred)")
        
        # Location match
        query_location = (query_components.get('location') or '').lower()
        if query_location:
            work_location = (member.get('office_address_city_normalized') or '').lower()
            home_location = (member.get('home_address_city_normalized') or '').lower()
            if query_location in work_location:
                reasons.append(f"Works in {member.get('office_address_city_normalized')}")
            elif query_location in home_location:
                reasons.append(f"Lives in {member.get('home_address_city_normalized')}")
        
        # Company info
        if member.get('current_company'):
            reasons.append(f"Works at {member.get('current_company')}")
        
        # Contact availability
        contact_methods = []
        if member.get('primary_email'):
            contact_methods.append('email')
        if member.get('mobile_phone'):
            contact_methods.append('mobile')
        if contact_methods:
            reasons.append(f"Available via {', '.join(contact_methods)}")
        
        return reasons
    
    def log_query(self, query: str, query_type: str, results: List[Dict[str, Any]]):
        """Log query for analytics and improvement."""
        try:
            # This would insert into query_log table
            # For now, just log to file
            logger.info(f"Query logged: {query_type} - '{query}' - {len(results)} results")
        except Exception as e:
            logger.error(f"Error logging query: {e}")
    
    def _build_profession_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for profession detection."""
        patterns = {}
        for profession, keywords in PROFESSION_KEYWORDS.items():
            patterns[profession] = [
                rf"(?:need|looking for|find)\s+.*?{keyword}" for keyword in keywords
            ]
        return patterns
    
    def _build_location_patterns(self) -> List[str]:
        """Build regex patterns for location detection."""
        return [
            r"(?:in|at|near|from|based in)\s+([a-zA-Z\s]+)",
            r"([a-zA-Z\s]+)\s+area",
            r"([a-zA-Z\s]+)\s+city"
        ]
    
    def _build_service_patterns(self) -> List[str]:
        """Build regex patterns for service detection."""
        return [
            r"need\s+(?:a\s+)?([a-zA-Z\s]+)",
            r"looking for\s+(?:a\s+)?([a-zA-Z\s]+)",
            r"find\s+(?:a\s+)?([a-zA-Z\s]+)",
            r"(?:any|do we have)\s+([a-zA-Z\s]+)"
        ]