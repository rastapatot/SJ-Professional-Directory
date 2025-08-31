#!/usr/bin/env python3
"""
SJ Professional Directory - Local Deployment Script (Python version)
====================================================================

This script sets up and runs the SJ Professional Directory locally.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"🐍 Python: {sys.version.split()[0]}")
    return True

def check_database():
    """Check if database exists and has data."""
    db_path = Path("sj_directory.db")
    
    if not db_path.exists():
        print("🗄️  Database not found. Creating database...")
        result = subprocess.run([sys.executable, "run.py", "--create-db"])
        if result.returncode != 0:
            print("❌ Database creation failed!")
            return False
    
    # Check member count
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM members")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            print("📥 No data found. Importing from Raw_Files...")
            result = subprocess.run([sys.executable, "run.py", "--import"])
            if result.returncode != 0:
                print("⚠️  Data import had issues, but continuing...")
            
            # Recheck count
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT COUNT(*) FROM members")
            count = cursor.fetchone()[0]
            conn.close()
        
        print(f"📊 Database contains {count} members")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_dependencies():
    """Check and install required dependencies."""
    required_packages = [
        'streamlit', 'pandas', 'fuzzywuzzy', 'python-levenshtein',
        'xlrd', 'openpyxl', 'chardet'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"📦 Installing missing dependencies: {', '.join(missing_packages)}")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "--user"
        ] + missing_packages)
        
        if result.returncode != 0:
            print("⚠️  Some packages may not have installed correctly")
            return False
    
    print("✅ All dependencies satisfied")
    return True

def create_directories():
    """Create necessary directories."""
    Path("logs").mkdir(exist_ok=True)
    print("📁 Created logs directory")

def start_streamlit():
    """Start the Streamlit application."""
    print("")
    print("🚀 Starting SJ Professional Directory...")
    print("📍 Local URL: http://localhost:8501")
    print("🔒 Admin Password: SJ92C!")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main deployment function."""
    print("🏢 SJ Professional Directory - Local Deployment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("streamlit_app.py").exists():
        print("❌ Error: streamlit_app.py not found.")
        print("Please run this script from the SJ directory.")
        return 1
    
    # Run all checks
    if not check_python_version():
        return 1
    
    if not check_dependencies():
        return 1
    
    if not check_database():
        return 1
    
    create_directories()
    
    # Start the application
    start_streamlit()
    
    return 0

if __name__ == "__main__":
    exit(main())