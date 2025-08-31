#!/usr/bin/env python3
"""
SJ Professional Directory - Cloud Setup Script
==============================================

This script initializes the database and imports sample data for Streamlit Cloud deployment.
Since cloud deployments are ephemeral, this runs on each startup.
"""

import sqlite3
import os
import logging
from pathlib import Path

def setup_cloud_database():
    """Setup database for cloud deployment."""
    db_path = "sj_directory.db"
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create new database with schema
    with open("database_schema.sql", "r") as f:
        schema = f.read()
    
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.close()
    
    print("✅ Database created for cloud deployment")
    return True

def create_sample_data():
    """Create sample member data for demonstration."""
    conn = sqlite3.connect("sj_directory.db")
    
    sample_members = [
        {
            'full_name': 'Juan Dela Cruz',
            'full_name_normalized': 'juan dela cruz',
            'nickname': 'Johnny',
            'primary_email': 'juan.delacruz@lawfirm.com',
            'mobile_phone': '0917-123-4567',
            'current_profession': 'Lawyer',
            'current_profession_normalized': 'lawyer',
            'current_company': 'Dela Cruz Law Office',
            'batch_original': '95-S',
            'batch_normalized': '95-S',
            'school_chapter': 'UP Diliman',
            'office_address_city_normalized': 'Makati',
            'home_address_city_normalized': 'Quezon City',
            'confidence_score': 0.95,
            'source_file_name': 'cloud_sample_data',
            'inferred_profession': 'Legal'
        },
        {
            'full_name': 'Maria Santos',
            'full_name_normalized': 'maria santos',
            'nickname': 'Marie',
            'primary_email': 'maria.santos@hospital.com',
            'mobile_phone': '0918-234-5678',
            'current_profession': 'Doctor',
            'current_profession_normalized': 'doctor',
            'current_company': 'Heart Center',
            'batch_original': '98-T',
            'batch_normalized': '98-T',
            'school_chapter': 'UST',
            'office_address_city_normalized': 'Manila',
            'home_address_city_normalized': 'Pasig',
            'confidence_score': 0.92,
            'source_file_name': 'cloud_sample_data',
            'inferred_profession': 'Medical'
        },
        {
            'full_name': 'Robert Garcia',
            'full_name_normalized': 'robert garcia',
            'nickname': 'Bobby',
            'primary_email': 'robert.garcia@techcorp.com',
            'mobile_phone': '0919-345-6789',
            'current_profession': 'Engineer',
            'current_profession_normalized': 'engineer',
            'current_company': 'Tech Solutions Inc',
            'batch_original': '00-U',
            'batch_normalized': '00-U',
            'school_chapter': 'UP Los Baños',
            'office_address_city_normalized': 'BGC',
            'home_address_city_normalized': 'Taguig',
            'confidence_score': 0.88,
            'source_file_name': 'cloud_sample_data',
            'inferred_profession': 'Engineering'
        }
    ]
    
    # Insert sample members
    for member in sample_members:
        placeholders = ', '.join(['?' for _ in member])
        columns = ', '.join(member.keys())
        
        conn.execute(
            f"INSERT INTO members ({columns}) VALUES ({placeholders})",
            list(member.values())
        )
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created {len(sample_members)} sample members")

if __name__ == "__main__":
    setup_cloud_database()
    create_sample_data()