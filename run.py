#!/usr/bin/env python3
# SJ Professional Directory - Quick Run Script
# ============================================================================

"""
Quick run script for SJ Professional Directory.

Usage:
    python run.py                    # Start web application
    python run.py --test            # Run system tests
    python run.py --import          # Import all data
    python run.py --create-db       # Create database only
"""

import sys
import argparse
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def run_app():
    """Run the main Streamlit application."""
    import subprocess
    import sys
    
    try:
        # Run Streamlit app
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], cwd=Path(__file__).parent)
        return result.returncode
    except Exception as e:
        print(f"❌ Failed to start Streamlit app: {e}")
        return 1

def run_flask_app():
    """Run the Flask application (alternative)."""
    from app import main
    return main()

def run_tests():
    """Run system tests."""
    from test_system import main as test_main
    return test_main()

def create_database():
    """Create database only."""
    from database import DatabaseManager
    from config import DATABASE_PATH
    
    print("🗄️  Creating database...")
    
    if DATABASE_PATH.exists():
        response = input(f"Database {DATABASE_PATH} already exists. Recreate? (y/N): ")
        if response.lower() != 'y':
            print("Database creation cancelled.")
            return 0
        DATABASE_PATH.unlink()
    
    try:
        db = DatabaseManager(DATABASE_PATH)
        db.create_database()
        print(f"✅ Database created successfully: {DATABASE_PATH}")
        return 0
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return 1

def import_data():
    """Import all data from Raw_Files."""
    from database import DatabaseManager
    from data_processor import DataProcessor
    from config import DATABASE_PATH, RAW_FILES_DIR
    
    if not DATABASE_PATH.exists():
        print("❌ Database not found. Creating database first...")
        if create_database() != 0:
            return 1
    
    if not RAW_FILES_DIR.exists():
        print(f"❌ Raw_Files directory not found: {RAW_FILES_DIR}")
        return 1
    
    print("📥 Starting data import...")
    
    try:
        db = DatabaseManager(DATABASE_PATH)
        processor = DataProcessor(db)
        
        results = processor.import_all_files()
        
        print("✅ Data import completed!")
        print(f"📊 Results: {results}")
        return 0
        
    except Exception as e:
        print(f"❌ Data import failed: {e}")
        return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SJ Professional Directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run.py                    # Start web application
    python run.py --test            # Run system tests
    python run.py --import          # Import all data
    python run.py --create-db       # Create database only
        """
    )
    
    parser.add_argument('--test', action='store_true', 
                       help='Run system tests')
    parser.add_argument('--import', action='store_true', dest='import_data',
                       help='Import data from Raw_Files directory')
    parser.add_argument('--create-db', action='store_true', dest='create_db',
                       help='Create database only')
    parser.add_argument('--flask', action='store_true',
                       help='Run Flask version instead of Streamlit')
    
    args = parser.parse_args()
    
    # Print banner
    print("🏢 SJ Professional Directory")
    print("=" * 40)
    
    if args.test:
        return run_tests()
    elif args.import_data:
        return import_data()
    elif args.create_db:
        return create_database()
    elif args.flask:
        return run_flask_app()
    else:
        return run_app()

if __name__ == "__main__":
    exit(main())