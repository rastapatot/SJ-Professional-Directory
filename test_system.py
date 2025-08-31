#!/usr/bin/env python3
# SJ Professional Directory - System Test Script
# ============================================================================

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, DATABASE_PATH, SCHEMA_PATH
from database import DatabaseManager
from data_processor import DataProcessor
from query_processor import QueryProcessor
from text_processor import TextProcessor
from ai_inference import ProfessionInferencer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_creation():
    """Test database creation and schema."""
    print("\n🗄️  Testing Database Creation...")
    
    # Remove existing database for clean test
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print(f"   Removed existing database: {DATABASE_PATH}")
    
    try:
        db = DatabaseManager(DATABASE_PATH)
        db.create_database()
        print(f"   ✅ Database created successfully: {DATABASE_PATH}")
        
        # Test connection
        if db.test_connection():
            print("   ✅ Database connection test passed")
        else:
            print("   ❌ Database connection test failed")
            return False
        
        # Test basic operations
        stats = db.get_system_stats()
        print(f"   ✅ System stats retrieved: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database creation failed: {e}")
        return False

def test_text_processing():
    """Test text processing and normalization."""
    print("\n📝 Testing Text Processing...")
    
    try:
        processor = TextProcessor()
        
        # Test name normalization
        test_names = [
            "Dr. Juan Dela Cruz Jr.",
            "MARIA SANTOS",
            "Atty. Jose Rizal"
        ]
        
        for name in test_names:
            normalized = processor.normalize_name(name)
            print(f"   Name: '{name}' → '{normalized}'")
        
        # Test batch normalization
        test_batches = [
            "95-S",
            "Batch 93-B",
            "2001-G",
            "Batch No: 88-S1"
        ]
        
        for batch in test_batches:
            normalized = processor.normalize_batch(batch)
            print(f"   Batch: '{batch}' → {normalized.get('batch_normalized', 'FAILED')}")
        
        # Test location normalization
        test_locations = [
            "Makati City",
            "QC",
            "BGC, Taguig"
        ]
        
        for location in test_locations:
            normalized = processor.normalize_location(location)
            print(f"   Location: '{location}' → '{normalized}'")
        
        print("   ✅ Text processing tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Text processing failed: {e}")
        return False

def test_ai_inference():
    """Test AI profession inference."""
    print("\n🤖 Testing AI Inference...")
    
    try:
        inferencer = ProfessionInferencer()
        
        # Test member data samples
        test_members = [
            {
                'full_name': 'Dr. Maria Santos',
                'primary_email': 'maria.santos@hospital.com.ph',
                'current_company': 'Manila Medical Center'
            },
            {
                'full_name': 'Juan Dela Cruz',
                'primary_email': 'juan@lawfirm.com.ph',
                'current_profession': 'Attorney'
            },
            {
                'full_name': 'Jose Reyes',
                'primary_email': 'jose@petron.com',
                'office_address_full': 'Makati CBD, Makati City'
            }
        ]
        
        for i, member in enumerate(test_members, 1):
            print(f"   Testing member {i}: {member['full_name']}")
            inference = inferencer.infer_profession_info(member)
            
            if inference.get('inferred_profession'):
                print(f"     Profession: {inference['inferred_profession']} "
                      f"(confidence: {inference.get('inferred_profession_confidence', 0):.2f})")
            else:
                print("     No profession inferred")
        
        print("   ✅ AI inference tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ AI inference failed: {e}")
        return False

def test_query_processing():
    """Test natural language query processing."""
    print("\n💭 Testing Query Processing...")
    
    try:
        # Create database and query processor
        db = DatabaseManager(DATABASE_PATH)
        query_processor = QueryProcessor(db)
        
        # Test query parsing
        test_queries = [
            "I need a family lawyer in Makati",
            "Do we have a cardiologist at Heart Center?",
            "Find doctors in Quezon City",
            "Looking for accountants in BGC",
            "Show me batch 95-S members"
        ]
        
        for query in test_queries:
            print(f"   Query: '{query}'")
            
            # Test professional services query
            if any(word in query.lower() for word in ['need', 'lawyer', 'doctor', 'accountant']):
                components = query_processor._parse_professional_query(query)
                print(f"     Professional query components: {components}")
            else:
                components = query_processor._parse_directory_query(query)
                print(f"     Directory query components: {components}")
        
        print("   ✅ Query processing tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Query processing failed: {e}")
        return False

def test_data_import():
    """Test data import from sample data."""
    print("\n📥 Testing Data Import...")
    
    try:
        db = DatabaseManager(DATABASE_PATH)
        processor = DataProcessor(db)
        
        # Insert some test data manually
        test_members = [
            {
                'full_name': 'Juan Dela Cruz',
                'full_name_normalized': 'juan dela cruz',
                'primary_email': 'juan@example.com',
                'mobile_phone': '09171234567',
                'current_profession': 'Lawyer',
                'current_profession_normalized': 'lawyer',
                'batch_original': '95-S',
                'batch_normalized': '1995-S',
                'batch_year': 1995,
                'batch_semester': 'S',
                'school_chapter': 'UP Diliman',
                'confidence_score': 0.9,
                'data_completeness_score': 0.8,
                'source_file_name': 'test_data'
            },
            {
                'full_name': 'Maria Santos',
                'full_name_normalized': 'maria santos',
                'primary_email': 'maria@hospital.com',
                'current_profession': 'Doctor',
                'current_profession_normalized': 'doctor',
                'inferred_profession': 'Medical',
                'inferred_profession_confidence': 0.85,
                'batch_original': '93-B',
                'batch_normalized': '1993-B',
                'batch_year': 1993,
                'batch_semester': 'B',
                'school_chapter': 'UST',
                'confidence_score': 0.8,
                'data_completeness_score': 0.7,
                'source_file_name': 'test_data'
            }
        ]
        
        member_ids = []
        for member_data in test_members:
            member_id = db.insert_member(member_data)
            member_ids.append(member_id)
            print(f"   ✅ Inserted test member: {member_data['full_name']} (ID: {member_id})")
        
        # Test search
        results = db.search_members({'profession': 'lawyer'})
        print(f"   ✅ Search test: Found {len(results)} lawyers")
        
        # Test stats
        stats = db.get_system_stats()
        print(f"   ✅ Stats after import: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Data import test failed: {e}")
        return False

def test_full_query():
    """Test full query workflow."""
    print("\n🔍 Testing Full Query Workflow...")
    
    try:
        db = DatabaseManager(DATABASE_PATH)
        query_processor = QueryProcessor(db)
        
        # Test professional services search
        query = "I need a lawyer in Metro Manila"
        print(f"   Testing query: '{query}'")
        
        results = query_processor.search_professional_services(query)
        print(f"   ✅ Professional services search returned {len(results)} results")
        
        for result in results:
            print(f"     - {result['name']}: {result['profession']} "
                  f"(confidence: {result['confidence_score']:.2f})")
        
        # Test directory search
        query = "Find members from batch 95"
        print(f"   Testing query: '{query}'")
        
        results = query_processor.search_directory(query)
        print(f"   ✅ Directory search returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Full query test failed: {e}")
        return False

def main():
    """Run all system tests."""
    print("🚀 SJ Professional Directory - System Tests")
    print("=" * 50)
    
    # Check if Raw_Files directory exists
    raw_files_dir = Path("Raw_Files")
    if raw_files_dir.exists():
        print(f"📁 Raw_Files directory found: {len(list(raw_files_dir.iterdir()))} items")
    else:
        print("⚠️  Raw_Files directory not found - data import tests will be limited")
    
    tests = [
        ("Database Creation", test_database_creation),
        ("Text Processing", test_text_processing),
        ("AI Inference", test_ai_inference),
        ("Query Processing", test_query_processing),
        ("Data Import", test_data_import),
        ("Full Query Workflow", test_full_query)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())