# SJ Professional Directory - Streamlit Cloud Application
# ============================================================================

import streamlit as st
import pandas as pd
import logging
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, date

# Configure page
st.set_page_config(
    page_title="SJ Professional Directory",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cloud deployment setup
@st.cache_resource
def setup_cloud_environment():
    """Setup environment for cloud deployment."""
    # Check if database exists, if not create it
    if not os.path.exists("sj_directory.db"):
        with st.spinner("Setting up database for first run..."):
            try:
                result = subprocess.run([sys.executable, "streamlit_cloud_setup.py"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("✅ Database initialized with sample data")
                else:
                    st.error(f"Database setup failed: {result.stderr}")
                    return False
            except Exception as e:
                st.error(f"Setup error: {e}")
                return False
    return True

# Import our modules (with fallback for missing files)
try:
    from config import Config, DATABASE_PATH, RAW_FILES_DIR
    from database import DatabaseManager
    from data_processor import DataProcessor
    from query_processor import QueryProcessor
except ImportError as e:
    st.error(f"Module import error: {e}")
    st.info("This appears to be a cloud deployment. Some features may be limited.")
    DATABASE_PATH = Path("sj_directory.db")
    RAW_FILES_DIR = Path("Raw_Files")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point for cloud deployment."""
    
    # Setup cloud environment
    if not setup_cloud_environment():
        st.error("Failed to setup cloud environment")
        return
    
    # Cloud deployment notice
    st.info("🌩️ **Cloud Deployment** - This is a demonstration version with sample data. In production, connect to your member database.")
    
    # Initialize session state
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager(DATABASE_PATH)
    if 'query_processor' not in st.session_state:
        st.session_state.query_processor = QueryProcessor(st.session_state.db_manager)
    
    # Main interface
    main_search_interface()

def main_search_interface():
    """Main search interface."""
    st.title("🏢 SJ Professional Directory")
    st.markdown("*Your intelligent fraternity directory - Ask in plain English!*")
    
    # Search tabs
    search_tab, directory_tab, demo_tab = st.tabs([
        "🔍 Professional Services", 
        "📋 Member Directory",
        "🎯 Demo"
    ])
    
    with search_tab:
        st.header("Find Professional Help")
        st.markdown("**Examples**: *I need a family lawyer in Makati*, *Do we have a cardiologist at Heart Center?*")
        
        # Search input
        query = st.text_input(
            "What kind of professional help do you need?",
            placeholder="I need a lawyer in Makati...",
            key="prof_search"
        )
        
        if query:
            with st.spinner("Searching for professionals..."):
                try:
                    results = st.session_state.query_processor.search_professional_services(query)
                    display_professional_results(results, query)
                except Exception as e:
                    st.error(f"Search error: {e}")
    
    with directory_tab:
        st.header("Member Directory Search")
        st.markdown("Search by name, batch, chapter, or other criteria")
        
        # Directory search form
        with st.form("directory_search"):
            col1, col2, col3 = st.columns(3)
            with col1:
                name_search = st.text_input("Name", placeholder="Juan Dela Cruz")
                batch_search = st.text_input("Batch", placeholder="95-S")
            with col2:
                chapter_search = st.text_input("Chapter", placeholder="UP Diliman")
                profession_search = st.text_input("Profession", placeholder="Engineer")
            with col3:
                location_search = st.text_input("Location", placeholder="Makati")
                
            search_submitted = st.form_submit_button("🔍 Search Directory")
        
        if search_submitted:
            search_params = {
                'name': name_search if name_search else None,
                'batch': batch_search if batch_search else None,
                'chapter': chapter_search if chapter_search else None,
                'profession': profession_search if profession_search else None,
                'location': location_search if location_search else None
            }
            
            # Remove None values
            search_params = {k: v for k, v in search_params.items() if v}
            
            if search_params:
                with st.spinner("Searching directory..."):
                    try:
                        results = st.session_state.db_manager.search_members(search_params)
                        display_directory_results(results)
                    except Exception as e:
                        st.error(f"Search error: {e}")
            else:
                st.warning("Please enter at least one search criteria.")
    
    with demo_tab:
        st.header("🎯 Try These Demo Queries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Professional Services")
            demo_queries = [
                "I need a lawyer in Makati",
                "Find doctors in Manila", 
                "Do we have engineers in BGC?",
                "Looking for accountants"
            ]
            
            for query in demo_queries:
                if st.button(f"Try: '{query}'", key=f"demo_{query}"):
                    st.session_state.prof_search = query
                    st.rerun()
        
        with col2:
            st.subheader("Sample Data Included")
            st.write("**Sample Members:**")
            st.write("• Juan Dela Cruz - Lawyer (Makati)")
            st.write("• Maria Santos - Doctor (Manila)")  
            st.write("• Robert Garcia - Engineer (BGC)")
            
            st.info("💡 **For Production**: Connect to your actual member database with thousands of records!")

def display_professional_results(results, query):
    """Display professional services search results."""
    if not results:
        st.warning("No professional matches found for your query.")
        st.info("💡 Try rephrasing your query or broadening your criteria.")
        return
    
    st.success(f"Found {len(results)} professional matches")
    
    for i, result in enumerate(results):
        with st.expander(f"🎯 {result['name']} - {result['profession']}", expanded=i < 3):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Basic info
                st.write(f"**🎓 Profession**: {result['profession']}")
                if result['company']:
                    st.write(f"**🏢 Company**: {result['company']}")
                if result['work_location']:
                    st.write(f"**📍 Work Location**: {result['work_location']}")
                if result['batch']:
                    st.write(f"**🎯 Batch**: {result['batch']}")
                if result['chapter']:
                    st.write(f"**🏫 Chapter**: {result['chapter']}")
                
                # Match reasons
                if result.get('match_reasons'):
                    st.write("**✨ Why this match:**")
                    for reason in result['match_reasons']:
                        st.write(f"  • {reason}")
            
            with col2:
                # Contact info
                st.write("**📞 Contact Information**")
                if result['email']:
                    st.write(f"📧 {result['email']}")
                if result['mobile']:
                    st.write(f"📱 {result['mobile']}")
                
                # Confidence metrics
                confidence = result.get('confidence_score', 0)
                st.metric("Confidence", f"{confidence:.1%}")

def display_directory_results(results):
    """Display directory search results."""
    if not results:
        st.warning("No members found matching your criteria.")
        return
    
    st.success(f"Found {len(results)} members")
    
    # Convert to DataFrame for better display
    df_data = []
    for member in results:
        df_data.append({
            'Name': member.get('full_name', ''),
            'Nickname': member.get('nickname', ''),
            'Email': member.get('primary_email', ''),
            'Mobile': member.get('mobile_phone', ''),
            'Profession': member.get('current_profession', ''),
            'Company': member.get('current_company', ''),
            'Batch': member.get('batch_normalized', ''),
            'Chapter': member.get('school_chapter', '')
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()