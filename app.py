# SJ Professional Directory - Main Application
# ============================================================================

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from pathlib import Path
import sqlite3
import logging
import os
from datetime import datetime

from config import Config, LOGGING_CONFIG, DATABASE_PATH, SCHEMA_PATH
from data_processor import DataProcessor
from query_processor import QueryProcessor
from database import DatabaseManager

# Create logs directory if it doesn't exist
Path('logs').mkdir(exist_ok=True)

# Configure logging
import logging.config
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize core components
db_manager = DatabaseManager(DATABASE_PATH)
data_processor = DataProcessor(db_manager)
query_processor = QueryProcessor(db_manager)

@app.route('/')
def index():
    """Main dashboard showing system status and quick stats."""
    try:
        stats = db_manager.get_system_stats()
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {e}", "error")
        return render_template('index.html', stats={})

@app.route('/search')
def search():
    """Professional directory search page."""
    return render_template('search.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for searching the directory."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        search_type = data.get('type', 'professional')  # 'professional' or 'directory'
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Process the query
        if search_type == 'professional':
            results = query_processor.search_professional_services(query)
        else:
            results = query_processor.search_directory(query)
        
        # Log the query
        query_processor.log_query(query, search_type, results)
        
        return jsonify({
            'results': results,
            'count': len(results),
            'query': query,
            'type': search_type
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin():
    """Admin dashboard for data management."""
    try:
        import_stats = db_manager.get_import_stats()
        data_quality = db_manager.get_data_quality_summary()
        return render_template('admin.html', 
                             import_stats=import_stats,
                             data_quality=data_quality)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        flash(f"Error: {e}", "error")
        return render_template('admin.html', import_stats={}, data_quality={})

@app.route('/admin/import', methods=['GET', 'POST'])
def import_data():
    """Data import interface."""
    if request.method == 'GET':
        return render_template('import.html')
    
    try:
        # Handle file upload and import
        import_type = request.form.get('import_type', 'full')
        
        if import_type == 'full':
            # Import all files from Raw_Files directory
            results = data_processor.import_all_files()
        elif import_type == 'single':
            # Import single file (would need file upload handling)
            flash("Single file import not yet implemented", "warning")
            return redirect(url_for('import_data'))
        
        flash(f"Import completed: {results}", "success")
        return redirect(url_for('admin'))
        
    except Exception as e:
        logger.error(f"Import error: {e}")
        flash(f"Import failed: {e}", "error")
        return redirect(url_for('import_data'))

@app.route('/admin/duplicates')
def manage_duplicates():
    """Duplicate management interface."""
    try:
        duplicates = db_manager.get_potential_duplicates()
        return render_template('duplicates.html', duplicates=duplicates)
    except Exception as e:
        logger.error(f"Error loading duplicates: {e}")
        flash(f"Error: {e}", "error")
        return render_template('duplicates.html', duplicates=[])

@app.route('/api/merge_duplicates', methods=['POST'])
def api_merge_duplicates():
    """API endpoint for merging duplicate records."""
    try:
        data = request.get_json()
        primary_id = data.get('primary_id')
        duplicate_ids = data.get('duplicate_ids', [])
        
        result = db_manager.merge_duplicates(primary_id, duplicate_ids)
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        logger.error(f"Merge error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/member/<int:member_id>')
def member_detail(member_id):
    """Detailed view of a member record."""
    try:
        member = db_manager.get_member_by_id(member_id)
        if not member:
            flash("Member not found", "error")
            return redirect(url_for('search'))
        
        history = db_manager.get_member_history(member_id)
        return render_template('member_detail.html', member=member, history=history)
        
    except Exception as e:
        logger.error(f"Error loading member {member_id}: {e}")
        flash(f"Error: {e}", "error")
        return redirect(url_for('search'))

@app.route('/api/stats')
def api_stats():
    """API endpoint for real-time statistics."""
    try:
        stats = db_manager.get_system_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db_manager.test_connection()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

def initialize_database():
    """Initialize the database with schema if it doesn't exist."""
    if not DATABASE_PATH.exists():
        logger.info("Database doesn't exist, creating new database...")
        try:
            db_manager.create_database()
            logger.info("Database created successfully")
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
    else:
        logger.info("Database already exists")

def main():
    """Main entry point for the application."""
    print("🚀 Starting SJ Professional Directory...")
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"📂 Raw Files: {Config.RAW_FILES_DIR}")
    
    try:
        # Initialize database
        initialize_database()
        
        # Start the web server
        print(f"🌐 Starting web server on {Config.HOST}:{Config.PORT}")
        print(f"🔗 Access the application at: http://{Config.HOST}:{Config.PORT}")
        
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())