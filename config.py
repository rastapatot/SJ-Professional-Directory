# SJ Professional Directory - Configuration
# ============================================================================

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Database configuration
DATABASE_PATH = BASE_DIR / "sj_directory.db"
SCHEMA_PATH = BASE_DIR / "database_schema.sql"

# Data sources
RAW_FILES_DIR = BASE_DIR / "Raw_Files"

# Flask configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sj-directory-secret-key-2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # Database
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # File upload limits
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file upload
    
    # AI/ML settings
    USE_AI_INFERENCE = os.environ.get('USE_AI_INFERENCE', 'True').lower() == 'true'
    AI_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for AI inferences
    
    # Professional services matching
    FUZZY_MATCH_THRESHOLD = 80  # Minimum similarity score for fuzzy matching
    
    # Data quality thresholds
    MIN_DATA_COMPLETENESS = 0.3  # Minimum fields filled to consider record "complete"
    DATA_FRESHNESS_YEARS = 5     # Years after which data is considered "stale"

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'sj_directory.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'default'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}

# File type mappings
SUPPORTED_FILE_TYPES = {
    '.xls': 'excel_old',
    '.xlsx': 'excel_new', 
    '.doc': 'word_old',
    '.docx': 'word_new',
    '.mdb': 'access',
    '.txt': 'text',
    '.csv': 'csv'
}

# Professional service categories and keywords
PROFESSION_KEYWORDS = {
    'Legal': [
        'lawyer', 'attorney', 'counsel', 'advocate', 'legal', 'law', 'esq',
        'litigation', 'corporate law', 'family law', 'criminal law',
        'real estate law', 'tax law', 'labor law'
    ],
    'Medical': [
        'doctor', 'physician', 'md', 'medical', 'clinic', 'hospital',
        'surgeon', 'cardiologist', 'pediatrician', 'neurologist',
        'dentist', 'nurse', 'healthcare', 'medicine'
    ],
    'Business': [
        'business', 'consultant', 'manager', 'executive', 'ceo', 'cfo',
        'entrepreneur', 'finance', 'accounting', 'cpa', 'marketing',
        'sales', 'operations', 'strategy'
    ],
    'Engineering': [
        'engineer', 'engineering', 'pe', 'civil', 'electrical', 'mechanical',
        'chemical', 'software', 'systems', 'technical', 'construction',
        'project manager', 'architect'
    ],
    'IT/Technology': [
        'programmer', 'developer', 'software', 'it', 'technology', 'tech',
        'computer', 'systems', 'network', 'database', 'web', 'mobile',
        'cybersecurity', 'data scientist'
    ],
    'Education': [
        'teacher', 'professor', 'educator', 'principal', 'dean',
        'academic', 'research', 'university', 'school', 'training'
    ],
    'Government': [
        'government', 'civil service', 'public service', 'bureau',
        'department', 'ministry', 'agency', 'municipal', 'federal'
    ],
    'Real Estate': [
        'real estate', 'broker', 'realtor', 'property', 'development',
        'construction', 'housing', 'commercial', 'residential'
    ]
}

# Location mappings for normalization
LOCATION_MAPPINGS = {
    'QC': 'Quezon City',
    'Makati CBD': 'Makati',
    'BGC': 'Taguig',
    'Ortigas': 'Pasig',
    'Mandaluyong City': 'Mandaluyong',
    'Pasay City': 'Pasay',
    'Manila City': 'Manila'
}

# Batch normalization patterns
BATCH_PATTERNS = [
    r'(\d{2,4})-([A-Z]+\d*)',  # 95-S, 2001-B1
    r'Batch\s+(\d{2,4})-([A-Z]+\d*)',  # Batch 95-S
    r'Batch\s+No[:\.]?\s*(\d{2,4})-([A-Z]+\d*)',  # Batch No: 95-S
    r'Batch\s+(\d{2,4})',  # Batch 99 (no letter)
    r'(\d{2,4})',  # Just numbers
]

# Email domain to company mappings (for profession inference)
COMPANY_DOMAINS = {
    'petron.com': 'Petron Corporation',
    'chevrontexaco.com': 'Chevron Texaco',
    'ccbpi.com': 'Coca-Cola Beverages Philippines',
    'firstgas.com.ph': 'First Gas Holdings',
    'sun.com.ph': 'Sun Cellular',
    'mozcom.com': 'Mozcom',
    'pilnet.com': 'Philippine Network Foundation',
    'yahoo.com': None,  # Generic email providers
    'gmail.com': None,
    'hotmail.com': None,
    'edsamail.com.ph': None
}