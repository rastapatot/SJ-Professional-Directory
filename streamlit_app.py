# SJ Professional Directory - Streamlit Application
# ============================================================================

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime, date
import json
import time

# Configure page
st.set_page_config(
    page_title="SJ Professional Directory",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import our modules
from config import Config, DATABASE_PATH, RAW_FILES_DIR
from database import DatabaseManager
from data_processor import DataProcessor
from query_processor import QueryProcessor
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager(DATABASE_PATH)
if 'query_processor' not in st.session_state:
    st.session_state.query_processor = QueryProcessor(st.session_state.db_manager)
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = DataProcessor(st.session_state.db_manager)

def check_database():
    """Check if database exists and is accessible."""
    if not DATABASE_PATH.exists():
        st.error("Database not found! Please initialize the system first.")
        if st.button("🗄️ Create Database"):
            with st.spinner("Creating database..."):
                try:
                    st.session_state.db_manager.create_database()
                    st.success("Database created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create database: {e}")
        return False
    
    # Test connection
    if not st.session_state.db_manager.test_connection():
        st.error("Cannot connect to database!")
        return False
    
    return True

def main_search_interface():
    """Main search interface."""
    st.title("🏢 SJ Professional Directory")
    st.markdown("*Your intelligent fraternity directory - Ask in plain English!*")
    
    # Enhanced conversational search
    st.header("💬 Ask Me Anything")
    st.markdown("**Try asking**: *Who lives in Makati?*, *Show me everyone from batch 95-S*, *I need a lawyer in BGC*, *Who plays basketball?*, *Anyone interested in photography?*, *How many members do we have?*")
    
    # Main search input
    query = st.text_input(
        "Ask your question in plain English:",
        placeholder="Who lives in Quezon City? / I need a doctor / Who plays tennis? / Show me batch 95-S...",
        key="natural_search",
        help="Examples: 'Who lives in Makati', 'I need a lawyer', 'Who plays basketball', 'Anyone into photography', 'Show me batch 95-S'"
    )
    
    if query:
        with st.spinner("Understanding your question..."):
            try:
                results = st.session_state.query_processor.search_natural_language(query)
                display_enhanced_results(results, query)
            except Exception as e:
                st.error(f"Search error: {e}")
                st.info("💡 Try rephrasing your question or use the detailed search below.")
    
    st.divider()
    
    # Detailed search tabs for advanced users
    with st.expander("🔧 Advanced Search Options", expanded=False):
        search_tab, directory_tab = st.tabs(["🔍 Professional Services", "📋 Member Directory"])
        
        with search_tab:
            st.subheader("Find Professional Help")
            st.markdown("**Examples**: *I need a family lawyer in Bulacan*, *Do we have a cardiologist at Heart Center?*")
            
            # Search input
            prof_query = st.text_input(
                "What kind of professional help do you need?",
                placeholder="I need a lawyer in Makati...",
                key="prof_search"
            )
            
            # Search options
            col1, col2 = st.columns([3, 1])
            with col2:
                urgency = st.selectbox("Urgency", ["Normal", "Urgent"], key="urgency")
            
            if prof_query:
                with st.spinner("Searching for professionals..."):
                    try:
                        results = st.session_state.query_processor.search_professional_services(prof_query)
                        display_professional_results(results, prof_query)
                    except Exception as e:
                        st.error(f"Search error: {e}")
        
        with directory_tab:
            st.subheader("Member Directory Search")
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

def display_enhanced_results(results, query):
    """Display enhanced search results with better formatting."""
    if not results:
        st.warning("No matches found for your query.")
        st.info("💡 Try rephrasing your question or using different keywords.")
        return
    
    # Check if this is a demographic summary query
    if results and results[0].get('demographic_summary'):
        summary = results[0]['demographic_summary']
        st.success(f"Found {summary['total_count']} total members")
        
        # Show summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🏙️ Top Locations")
            for location, count in summary['top_locations']:
                if location != 'Unknown':
                    st.write(f"• **{location}**: {count} members")
        
        with col2:
            st.subheader("💼 Top Professions")
            for profession, count in summary['top_professions']:
                if profession != 'Unknown':
                    st.write(f"• **{profession}**: {count} members")
        
        with col3:
            st.subheader("🎓 Top Batches")
            for batch, count in summary['top_batches']:
                if batch != 'Unknown':
                    st.write(f"• **{batch}**: {count} members")
        
        st.divider()
        st.subheader("All Members")
    
    # Determine query type for appropriate display
    query_type = results[0].get('query_type', 'general') if results else 'general'
    
    if query_type == 'location_search':
        st.success(f"Found {len(results)} members in the specified location")
    elif query_type == 'batch_search':
        st.success(f"Found {len(results)} members from the specified batch")
    else:
        st.success(f"Found {len(results)} matches")
    
    # Display results
    for i, result in enumerate(results):
        # Create a more informative title
        title_parts = []
        if result.get('name'):
            title_parts.append(f"👤 {result['name']}")
        if result.get('profession') and result['profession'] != 'N/A':
            title_parts.append(f"💼 {result['profession']}")
        if result.get('home_location') and result['home_location'] != 'N/A':
            title_parts.append(f"🏠 {result['home_location']}")
        elif result.get('work_location') and result['work_location'] != 'N/A':
            title_parts.append(f"🏢 {result['work_location']}")
        
        title = " | ".join(title_parts) if title_parts else f"Member {i+1}"
        
        with st.expander(title, expanded=i < 5):  # Show first 5 expanded
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Basic information
                st.write(f"**👤 Name**: {result.get('name', 'N/A')}")
                
                if result.get('profession') and result['profession'] != 'N/A':
                    st.write(f"**💼 Profession**: {result['profession']}")
                
                if result.get('company') and result['company'] != 'N/A':
                    st.write(f"**🏢 Company**: {result['company']}")
                
                # Location information
                if result.get('home_location') and result['home_location'] != 'N/A':
                    st.write(f"**🏠 Home**: {result['home_location']}")
                
                if result.get('work_location') and result['work_location'] != 'N/A':
                    st.write(f"**🏢 Work**: {result['work_location']}")
                
                # Academic information
                if result.get('batch') and result['batch'] != 'N/A':
                    st.write(f"**🎓 Batch**: {result['batch']}")
                
                if result.get('chapter') and result['chapter'] != 'N/A':
                    st.write(f"**🏫 Chapter**: {result['chapter']}")
                
                # Show interests if this is an interest-based search
                if result.get('query_type') == 'interest_search':
                    if result.get('interests') and result['interests'] != 'N/A':
                        st.write(f"**🎯 Interests**: {result['interests']}")
                    if result.get('sports') and result['sports'] != 'N/A':
                        st.write(f"**⚽ Sports**: {result['sports']}")
                
                # Match reasons
                if result.get('match_reasons'):
                    st.write("**✨ Why this match:**")
                    for reason in result['match_reasons']:
                        st.write(f"  • {reason}")
            
            with col2:
                # Contact information
                st.write("**📞 Contact Information**")
                if result.get('email') and result['email'] != 'N/A':
                    st.write(f"📧 {result['email']}")
                if result.get('mobile') and result['mobile'] != 'N/A':
                    st.write(f"📱 {result['mobile']}")
                
                # Confidence metrics
                confidence = result.get('confidence_score', 0)
                if confidence > 0:
                    st.metric("Data Confidence", f"{confidence:.1%}")
                
                # Address details
                if result.get('home_address') and result['home_address'] != 'N/A':
                    with st.expander("🏠 Home Address"):
                        st.write(result['home_address'])
                
                if result.get('work_address') and result['work_address'] != 'N/A':
                    with st.expander("🏢 Work Address"):
                        st.write(result['work_address'])

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
                
                # Data vintage
                vintage = result.get('data_vintage')
                if vintage:
                    st.write(f"📅 Data from: {vintage}")
                
                # Action buttons
                if result['email']:
                    mailto_link = f"mailto:{result['email']}?subject=Professional Inquiry via SJ Directory"
                    st.markdown(f"[📧 Send Email]({mailto_link})")

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
            'Chapter': member.get('school_chapter', ''),
            'Confidence': f"{member.get('confidence_score', 0):.1%}"
        })
    
    df = pd.DataFrame(df_data)
    
    # Display with clickable rows
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Show detailed view for selected member
    if selected_indices and len(selected_indices['selection']['rows']) > 0:
        selected_idx = selected_indices['selection']['rows'][0]
        selected_member = results[selected_idx]
        show_member_detail(selected_member)

def show_member_detail(member):
    """Show detailed member information."""
    st.divider()
    st.subheader(f"👤 {member['full_name']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Personal Information**")
        if member.get('nickname'):
            st.write(f"Nickname: {member['nickname']}")
        if member.get('batch_normalized'):
            st.write(f"Batch: {member['batch_normalized']}")
        if member.get('school_chapter'):
            st.write(f"Chapter: {member['school_chapter']}")
    
    with col2:
        st.write("**Professional Information**")
        if member.get('current_profession'):
            st.write(f"Profession: {member['current_profession']}")
        if member.get('current_company'):
            st.write(f"Company: {member['current_company']}")
        if member.get('office_address_city_normalized'):
            st.write(f"Work Location: {member['office_address_city_normalized']}")
    
    with col3:
        st.write("**Contact Information**")
        if member.get('primary_email'):
            st.write(f"📧 {member['primary_email']}")
        if member.get('mobile_phone'):
            st.write(f"📱 {member['mobile_phone']}")
        if member.get('home_phone'):
            st.write(f"🏠 {member['home_phone']}")
        if member.get('home_address_city_normalized'):
            st.write(f"Home: {member['home_address_city_normalized']}")

def show_member_editor(member):
    """Show member edit interface in admin panel."""
    st.divider()
    st.subheader(f"✏️ Edit Member: {member['full_name']}")
    
    # Show member ID and basic info
    col1, col2 = st.columns([1, 3])
    with col1:
        st.info(f"**Member ID**: {member['id']}")
        st.info(f"**Created**: {member.get('created_at', 'Unknown')[:10]}")
        st.info(f"**Confidence**: {member.get('confidence_score', 0):.1%}")
    
    with col2:
        # Edit form
        with st.form(f"edit_member_{member['id']}"):
            st.write("**📝 Edit Information**")
            
            # Personal Information
            col_a, col_b = st.columns(2)
            with col_a:
                new_name = st.text_input("Full Name", value=member.get('full_name', ''))
                new_nickname = st.text_input("Nickname", value=member.get('nickname', '') or '')
                new_batch = st.text_input("Batch", value=member.get('batch_original', '') or '')
                new_chapter = st.text_input("Chapter", value=member.get('school_chapter', '') or '')
            
            with col_b:
                new_email = st.text_input("Primary Email", value=member.get('primary_email', '') or '')
                new_mobile = st.text_input("Mobile Phone", value=member.get('mobile_phone', '') or '')
                new_home_phone = st.text_input("Home Phone", value=member.get('home_phone', '') or '')
                new_profession = st.text_input("Profession", value=member.get('current_profession', '') or '')
            
            # Addresses
            st.write("**🏠 Addresses**")
            col_c, col_d = st.columns(2)
            with col_c:
                new_home_address = st.text_area("Home Address", value=member.get('home_address_full', '') or '', height=100)
            with col_d:
                new_office_address = st.text_area("Office Address", value=member.get('office_address_full', '') or '', height=100)
            
            # Company information
            new_company = st.text_input("Company", value=member.get('current_company', '') or '')
            
            # Professional Information
            st.write("**💼 Professional Information**")
            col_e, col_f = st.columns(2)
            with col_e:
                new_job_title = st.text_input("Job Title", value=member.get('job_title', '') or '')
                new_linkedin = st.text_input("LinkedIn Profile", value=member.get('linkedin_profile', '') or '')
            with col_f:
                new_services_offered = st.text_area("Services Offered", value=member.get('services_offered', '') or '', height=60)
                new_practice_areas = st.text_area("Practice Areas/Specializations", value=member.get('practice_areas', '') or '', height=60)
            
            # Personal Interests & Hobbies
            st.write("**🎯 Interests & Hobbies**")
            col_g, col_h = st.columns(2)
            with col_g:
                new_interests = st.text_area("Interests & Hobbies", 
                                           value=member.get('interests_hobbies', '') or '', 
                                           placeholder="Photography, cooking, reading, traveling...",
                                           height=80)
                new_volunteer_work = st.text_area("Volunteer Work", 
                                                value=member.get('volunteer_work', '') or '',
                                                placeholder="NGO work, community service...",
                                                height=60)
            with col_h:
                new_sports = st.text_area("Sports & Activities", 
                                        value=member.get('sports_activities', '') or '',
                                        placeholder="Basketball, tennis, running, cycling...",
                                        height=80)
                new_social_clubs = st.text_area("Social Clubs/Organizations", 
                                               value=member.get('social_clubs', '') or '',
                                               placeholder="Rotary, Lions Club, Country Club...",
                                               height=60)
            
            # Academic Information
            st.write("**🎓 Academic Information**")
            col_i, col_j = st.columns(2)
            with col_i:
                new_course = st.text_input("Course/Degree", value=member.get('course', '') or '')
                new_positions_held = st.text_area("Fraternity Positions Held", 
                                                value=member.get('positions_held', '') or '',
                                                placeholder="President, VP, Secretary...",
                                                height=60)
            with col_j:
                new_member_status = st.selectbox("Member Status", 
                                                options=['active', 'alumni', 'inactive', 'deceased'],
                                                index=['active', 'alumni', 'inactive', 'deceased'].index(member.get('member_status', 'active')))
                new_community_involvement = st.text_area("Community Involvement", 
                                                        value=member.get('community_involvement', '') or '',
                                                        placeholder="Board memberships, community roles...",
                                                        height=60)
            
            # Additional Contact Information
            st.write("**📞 Additional Contact**")
            col_k, col_l = st.columns(2)
            with col_k:
                new_secondary_email = st.text_input("Secondary Email", value=member.get('secondary_email', '') or '')
                new_office_phone = st.text_input("Office Phone", value=member.get('office_phone', '') or '')
            with col_l:
                new_birth_date = st.date_input("Birth Date", 
                                             value=None if not member.get('birth_date') else 
                                             datetime.strptime(member.get('birth_date', ''), '%Y-%m-%d').date() if member.get('birth_date') else None)
                # Willing to help members checkbox
                new_willing_to_help = st.checkbox("Willing to help other members", 
                                                 value=member.get('willing_to_help_members', True))
            
            # Notes section
            new_notes = st.text_area("Admin Notes", placeholder="Add any admin notes about this member...", height=80)
            
            # Submit button
            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                save_changes = st.form_submit_button("💾 Save Changes", type="primary")
            with col_cancel:
                view_history = st.form_submit_button("📝 View Change History")
            
            if save_changes:
                # Prepare updates
                updates = {}
                
                # Only update fields that have changed
                if new_name != member.get('full_name', ''):
                    updates['full_name'] = new_name
                    updates['full_name_normalized'] = new_name.lower().strip()
                
                if new_nickname != (member.get('nickname') or ''):
                    updates['nickname'] = new_nickname if new_nickname else None
                
                if new_batch != (member.get('batch_original') or ''):
                    updates['batch_original'] = new_batch if new_batch else None
                    # Re-normalize batch if changed
                    if new_batch:
                        from text_processor import TextProcessor
                        tp = TextProcessor()
                        batch_info = tp.normalize_batch(new_batch)
                        updates.update(batch_info)
                
                if new_chapter != (member.get('school_chapter') or ''):
                    updates['school_chapter'] = new_chapter if new_chapter else None
                
                if new_email != (member.get('primary_email') or ''):
                    updates['primary_email'] = new_email if new_email else None
                
                if new_mobile != (member.get('mobile_phone') or ''):
                    updates['mobile_phone'] = new_mobile if new_mobile else None
                
                if new_home_phone != (member.get('home_phone') or ''):
                    updates['home_phone'] = new_home_phone if new_home_phone else None
                
                if new_profession != (member.get('current_profession') or ''):
                    updates['current_profession'] = new_profession if new_profession else None
                    if new_profession:
                        updates['current_profession_normalized'] = new_profession.lower()
                
                if new_company != (member.get('current_company') or ''):
                    updates['current_company'] = new_company if new_company else None
                
                if new_home_address != (member.get('home_address_full') or ''):
                    updates['home_address_full'] = new_home_address if new_home_address else None
                
                if new_office_address != (member.get('office_address_full') or ''):
                    updates['office_address_full'] = new_office_address if new_office_address else None
                
                # Professional Information
                if new_job_title != (member.get('job_title') or ''):
                    updates['job_title'] = new_job_title if new_job_title else None
                
                if new_linkedin != (member.get('linkedin_profile') or ''):
                    updates['linkedin_profile'] = new_linkedin if new_linkedin else None
                
                if new_services_offered != (member.get('services_offered') or ''):
                    updates['services_offered'] = new_services_offered if new_services_offered else None
                
                if new_practice_areas != (member.get('practice_areas') or ''):
                    updates['practice_areas'] = new_practice_areas if new_practice_areas else None
                
                # Personal Interests & Hobbies
                if new_interests != (member.get('interests_hobbies') or ''):
                    updates['interests_hobbies'] = new_interests if new_interests else None
                    if new_interests:
                        updates['interests_hobbies_normalized'] = new_interests.lower()
                
                if new_sports != (member.get('sports_activities') or ''):
                    updates['sports_activities'] = new_sports if new_sports else None
                    if new_sports:
                        updates['sports_activities_normalized'] = new_sports.lower()
                
                if new_volunteer_work != (member.get('volunteer_work') or ''):
                    updates['volunteer_work'] = new_volunteer_work if new_volunteer_work else None
                
                if new_social_clubs != (member.get('social_clubs') or ''):
                    updates['social_clubs'] = new_social_clubs if new_social_clubs else None
                
                # Academic Information
                if new_course != (member.get('course') or ''):
                    updates['course'] = new_course if new_course else None
                    if new_course:
                        updates['course_normalized'] = new_course.lower()
                
                if new_positions_held != (member.get('positions_held') or ''):
                    updates['positions_held'] = new_positions_held if new_positions_held else None
                
                if new_member_status != (member.get('member_status') or 'active'):
                    updates['member_status'] = new_member_status
                
                if new_community_involvement != (member.get('community_involvement') or ''):
                    updates['community_involvement'] = new_community_involvement if new_community_involvement else None
                
                # Additional Contact Information
                if new_secondary_email != (member.get('secondary_email') or ''):
                    updates['secondary_email'] = new_secondary_email if new_secondary_email else None
                
                if new_office_phone != (member.get('office_phone') or ''):
                    updates['office_phone'] = new_office_phone if new_office_phone else None
                
                # Birth date handling
                current_birth_date = member.get('birth_date')
                new_birth_date_str = new_birth_date.strftime('%Y-%m-%d') if new_birth_date else None
                if new_birth_date_str != current_birth_date:
                    updates['birth_date'] = new_birth_date_str
                
                # Willing to help checkbox
                if new_willing_to_help != member.get('willing_to_help_members', True):
                    updates['willing_to_help_members'] = new_willing_to_help
                
                # Save changes if any
                if updates:
                    try:
                        updates['updated_by'] = 'admin_manual_edit'
                        success = st.session_state.db_manager.update_member(member['id'], updates)
                        
                        if success:
                            st.success(f"✅ Successfully updated {len(updates)} fields for {new_name}")
                            
                            # Log the changes
                            for field, new_value in updates.items():
                                if field not in ['updated_by']:
                                    old_value = member.get(field)
                                    st.session_state.db_manager.log_change(
                                        member['id'], field, old_value, new_value,
                                        'UPDATE', 'admin_manual_edit'
                                    )
                            
                            st.info("🔄 Refresh the page to see updated information")
                        else:
                            st.error("❌ Failed to update member")
                            
                    except Exception as e:
                        st.error(f"❌ Error updating member: {e}")
                else:
                    st.info("ℹ️ No changes detected")
    
    # Show change history
    if 'view_history' in locals() and view_history:
        show_member_history(member['id'])

def show_member_history(member_id):
    """Show change history for a member."""
    st.divider()
    st.subheader("📝 Change History")
    
    try:
        history = st.session_state.db_manager.get_member_history(member_id)
        
        if history:
            # Convert to DataFrame for better display
            import pandas as pd
            df_data = []
            for change in history:
                df_data.append({
                    'Date': change['changed_at'][:19],  # Remove milliseconds
                    'Field': change['field_name'],
                    'Old Value': change['old_value'] or 'None',
                    'New Value': change['new_value'] or 'None',
                    'Reason': change['change_reason'],
                    'Changed By': change['changed_by'] or 'System'
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        else:
            st.info("No change history found for this member")
            
    except Exception as e:
        st.error(f"Error loading change history: {e}")

def show_add_member_form():
    """Show form to add new member."""
    st.subheader("➕ Add New Member")
    st.write("Fill in the information for the new member. Required fields are marked with *")
    
    with st.form("add_new_member"):
        # Personal Information
        st.write("**👤 Personal Information**")
        col1, col2 = st.columns(2)
        
        with col1:
            new_full_name = st.text_input("Full Name *", placeholder="Juan Dela Cruz")
            new_nickname = st.text_input("Nickname", placeholder="Johnny")
            new_batch = st.text_input("Batch", placeholder="95-S")
            new_chapter = st.selectbox("Chapter", [
                "", "UP Diliman", "UP Los Baños", "UP Cebu", "UP Iloilo", "UP Visayas",
                "UST", "FEU", "UE", "Silliman", "Lyceum Dagupan", "WMSU", "WVSU", "Fatima", "Other"
            ])
            if new_chapter == "Other":
                new_chapter = st.text_input("Specify Chapter", placeholder="Enter chapter name")
        
        with col2:
            new_course = st.text_input("Course", placeholder="Bachelor of Laws")
            new_birth_date = st.date_input("Birth Date", value=None)
            new_batchmates = st.text_input("Batchmates", placeholder="Juan Santos, Maria Garcia")
        
        st.divider()
        
        # Contact Information
        st.write("**📞 Contact Information**")
        col3, col4 = st.columns(2)
        
        with col3:
            new_email = st.text_input("Primary Email *", placeholder="juan.delacruz@email.com")
            new_secondary_email = st.text_input("Secondary Email", placeholder="johnny@company.com")
            new_mobile = st.text_input("Mobile Phone", placeholder="0917-123-4567")
        
        with col4:
            new_home_phone = st.text_input("Home Phone", placeholder="02-123-4567")
            new_office_phone = st.text_input("Office Phone", placeholder="02-987-6543")
        
        st.divider()
        
        # Professional Information
        st.write("**💼 Professional Information**")
        col5, col6 = st.columns(2)
        
        with col5:
            new_profession = st.text_input("Profession", placeholder="Lawyer")
            new_company = st.text_input("Company", placeholder="ABC Law Firm")
            new_job_title = st.text_input("Job Title", placeholder="Senior Partner")
        
        with col6:
            new_services = st.text_area("Services Offered", placeholder="Corporate Law, Family Law", height=100)
            new_willing_to_help = st.checkbox("Willing to help other members", value=True)
        
        st.divider()
        
        # Personal Interests & Hobbies
        st.write("**🎯 Interests & Hobbies**")
        col_int1, col_int2 = st.columns(2)
        
        with col_int1:
            new_interests = st.text_area("Interests & Hobbies", 
                                       placeholder="Photography, cooking, reading, traveling...",
                                       height=80)
            new_volunteer_work = st.text_area("Volunteer Work", 
                                            placeholder="NGO work, community service...",
                                            height=60)
        
        with col_int2:
            new_sports = st.text_area("Sports & Activities", 
                                    placeholder="Basketball, tennis, running, cycling...",
                                    height=80)
            new_social_clubs = st.text_area("Social Clubs/Organizations", 
                                           placeholder="Rotary, Lions Club, Country Club...",
                                           height=60)
        
        st.divider()
        
        # Address Information
        st.write("**🏠 Address Information**")
        col7, col8 = st.columns(2)
        
        with col7:
            new_home_address = st.text_area("Home Address", placeholder="123 Main St, Makati City", height=100)
            new_provincial_address = st.text_area("Provincial Address", placeholder="456 Rural Rd, Batangas", height=100)
        
        with col8:
            new_office_address = st.text_area("Office Address", placeholder="789 Business Ave, BGC, Taguig", height=100)
        
        st.divider()
        
        # Admin Notes
        st.write("**📝 Admin Information**")
        new_admin_notes = st.text_area("Admin Notes", placeholder="Any special notes about this member...", height=80)
        new_member_status = st.selectbox("Member Status", ["active", "alumni", "inactive"])
        
        # Submit button
        col_submit, col_clear = st.columns([1, 1])
        with col_submit:
            submit_new_member = st.form_submit_button("➕ Add Member", type="primary")
        with col_clear:
            clear_form = st.form_submit_button("🗑️ Clear Form")
        
        if submit_new_member:
            # Validation
            if not new_full_name.strip():
                st.error("❌ Full Name is required!")
                return
            
            if not new_email.strip():
                st.error("❌ Primary Email is required!")
                return
            
            # Check if email already exists
            existing_members = st.session_state.db_manager.search_members({'email': new_email})
            if existing_members:
                st.error(f"❌ Email {new_email} already exists for member: {existing_members[0]['full_name']}")
                return
            
            try:
                # Prepare member data
                member_data = {
                    'full_name': new_full_name.strip(),
                    'full_name_normalized': new_full_name.strip().lower(),
                    'nickname': new_nickname.strip() if new_nickname else None,
                    'primary_email': new_email.strip(),
                    'secondary_email': new_secondary_email.strip() if new_secondary_email else None,
                    'mobile_phone': new_mobile.strip() if new_mobile else None,
                    'home_phone': new_home_phone.strip() if new_home_phone else None,
                    'office_phone': new_office_phone.strip() if new_office_phone else None,
                    'current_profession': new_profession.strip() if new_profession else None,
                    'current_profession_normalized': new_profession.strip().lower() if new_profession else None,
                    'current_company': new_company.strip() if new_company else None,
                    'course': new_course.strip() if new_course else None,
                    'school_chapter': new_chapter if new_chapter else None,
                    'school_chapter_normalized': new_chapter.lower() if new_chapter else None,
                    'batchmates': new_batchmates.strip() if new_batchmates else None,
                    'home_address_full': new_home_address.strip() if new_home_address else None,
                    'office_address_full': new_office_address.strip() if new_office_address else None,
                    'member_status': new_member_status,
                    'created_by': 'admin_manual_add',
                    'source_file_name': 'admin_manual_entry',
                    'confidence_score': 1.0,  # Manual entries get high confidence
                    'data_completeness_score': 0.8,  # High completeness for manual entries
                    'birth_date': new_birth_date if new_birth_date else None,
                    'services_offered': new_services.strip() if new_services else None,
                    'willing_to_help_members': new_willing_to_help,
                    # Personal Interests & Hobbies
                    'interests_hobbies': new_interests.strip() if new_interests else None,
                    'interests_hobbies_normalized': new_interests.strip().lower() if new_interests else None,
                    'sports_activities': new_sports.strip() if new_sports else None,
                    'sports_activities_normalized': new_sports.strip().lower() if new_sports else None,
                    'volunteer_work': new_volunteer_work.strip() if new_volunteer_work else None,
                    'social_clubs': new_social_clubs.strip() if new_social_clubs else None
                }
                
                # Add batch normalization if batch is provided
                if new_batch.strip():
                    member_data['batch_original'] = new_batch.strip()
                    from text_processor import TextProcessor
                    tp = TextProcessor()
                    batch_info = tp.normalize_batch(new_batch.strip())
                    member_data.update(batch_info)
                
                # Extract city from addresses
                if new_home_address:
                    from text_processor import TextProcessor
                    tp = TextProcessor()
                    home_city = tp.extract_city(new_home_address)
                    member_data['home_address_city'] = home_city
                    member_data['home_address_city_normalized'] = tp.normalize_location(home_city)
                
                if new_office_address:
                    from text_processor import TextProcessor
                    tp = TextProcessor()
                    office_city = tp.extract_city(new_office_address)
                    member_data['office_address_city'] = office_city
                    member_data['office_address_city_normalized'] = tp.normalize_location(office_city)
                
                # Insert member
                member_id = st.session_state.db_manager.insert_member(member_data)
                
                if member_id:
                    st.success(f"✅ Successfully added new member: {new_full_name} (ID: {member_id})")
                    
                    # Log the creation
                    st.session_state.db_manager.log_change(
                        member_id, 'record_created', None, 'Member created via admin panel',
                        'INSERT', 'admin_manual_add'
                    )
                    
                    st.info("🔄 The new member is now available for searches!")
                    
                    # Show success details
                    with st.expander("📋 View Added Member Details"):
                        st.write(f"**Name**: {new_full_name}")
                        st.write(f"**Email**: {new_email}")
                        st.write(f"**Batch**: {new_batch if new_batch else 'Not specified'}")
                        st.write(f"**Chapter**: {new_chapter if new_chapter else 'Not specified'}")
                        st.write(f"**Profession**: {new_profession if new_profession else 'Not specified'}")
                        st.write(f"**Member ID**: {member_id}")
                
                else:
                    st.error("❌ Failed to add member - database error")
                    
            except Exception as e:
                st.error(f"❌ Error adding member: {e}")
                st.exception(e)
        
        if clear_form:
            st.info("🗑️ Form cleared. Refresh the page to see empty form.")

def sidebar_stats():
    """Display system statistics in sidebar."""
    st.sidebar.header("📊 System Status")
    
    try:
        stats = st.session_state.db_manager.get_system_stats()
        
        st.sidebar.metric("Total Members", stats.get('total_members', 0))
        st.sidebar.metric("With Email", stats.get('members_with_email', 0))
        st.sidebar.metric("With Profession", stats.get('members_with_profession', 0))
        st.sidebar.metric("Avg Confidence", f"{stats.get('avg_confidence', 0):.1%}")
        
        if stats.get('duplicates', 0) > 0:
            st.sidebar.warning(f"⚠️ {stats['duplicates']} potential duplicates")
        
    except Exception as e:
        st.sidebar.error("Could not load stats")

def show_all_members_interface():
    """Show all members with pagination and management options."""
    st.subheader("📋 All Members")
    
    # Initialize session state for pagination
    if 'admin_page' not in st.session_state:
        st.session_state.admin_page = 1
    if 'admin_per_page' not in st.session_state:
        st.session_state.admin_per_page = 25
    if 'admin_search' not in st.session_state:
        st.session_state.admin_search = ""
    if 'admin_include_inactive' not in st.session_state:
        st.session_state.admin_include_inactive = False
    
    # Controls row
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search members:", 
                                   value=st.session_state.admin_search,
                                   placeholder="Name, email, profession, batch...")
        if search_term != st.session_state.admin_search:
            st.session_state.admin_search = search_term
            st.session_state.admin_page = 1  # Reset to first page on new search
    
    with col2:
        per_page = st.selectbox("Per page:", [10, 25, 50, 100], 
                               index=[10, 25, 50, 100].index(st.session_state.admin_per_page))
        if per_page != st.session_state.admin_per_page:
            st.session_state.admin_per_page = per_page
            st.session_state.admin_page = 1
    
    with col3:
        include_inactive = st.checkbox("Include inactive", value=st.session_state.admin_include_inactive)
        if include_inactive != st.session_state.admin_include_inactive:
            st.session_state.admin_include_inactive = include_inactive
            st.session_state.admin_page = 1
    
    with col4:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    try:
        # Get members with pagination
        members, total_count = st.session_state.db_manager.get_all_members_paginated(
            page=st.session_state.admin_page,
            per_page=st.session_state.admin_per_page,
            search_term=st.session_state.admin_search if st.session_state.admin_search else None,
            include_inactive=st.session_state.admin_include_inactive
        )
        
        if total_count == 0:
            st.info("No members found.")
            return
        
        # Pagination info
        total_pages = (total_count + st.session_state.admin_per_page - 1) // st.session_state.admin_per_page
        start_idx = (st.session_state.admin_page - 1) * st.session_state.admin_per_page + 1
        end_idx = min(st.session_state.admin_page * st.session_state.admin_per_page, total_count)
        
        st.info(f"Showing {start_idx}-{end_idx} of {total_count} members (Page {st.session_state.admin_page} of {total_pages})")
        
        # Members table
        for idx, member in enumerate(members):
            with st.expander(
                f"{'🔴' if not member.get('is_active', True) else '🟢'} "
                f"{member.get('full_name', 'N/A')} | "
                f"{member.get('batch_normalized', 'No batch')} | "
                f"{member.get('primary_email', 'No email')}"
            ):
                # Member actions row
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**ID:** {member['id']}")
                    st.write(f"**Profession:** {member.get('current_profession', 'N/A')}")
                    st.write(f"**Location:** {member.get('home_address_city_normalized', 'N/A')}")
                    st.write(f"**Status:** {'Active' if member.get('is_active', True) else 'Inactive'}")
                
                with col2:
                    if st.button("📝 Edit", key=f"edit_{member['id']}"):
                        st.session_state[f"editing_member_{member['id']}"] = True
                        st.rerun()
                
                with col3:
                    if member.get('is_active', True):
                        if st.button("🗑️ Delete", key=f"delete_{member['id']}"):
                            if st.session_state.db_manager.delete_member(member['id']):
                                st.success(f"Member {member['full_name']} deleted successfully")
                                st.rerun()
                            else:
                                st.error("Failed to delete member")
                    else:
                        if st.button("♻️ Restore", key=f"restore_{member['id']}"):
                            if st.session_state.db_manager.restore_member(member['id']):
                                st.success(f"Member {member['full_name']} restored successfully")
                                st.rerun()
                            else:
                                st.error("Failed to restore member")
                
                with col4:
                    if st.button("👁️ View", key=f"view_{member['id']}"):
                        st.session_state[f"viewing_member_{member['id']}"] = True
                        st.rerun()
                
                # Show edit form if editing
                if st.session_state.get(f"editing_member_{member['id']}", False):
                    st.divider()
                    st.subheader(f"Editing: {member.get('full_name', 'N/A')}")
                    show_member_editor(member)
                    
                    if st.button("✅ Done Editing", key=f"done_edit_{member['id']}"):
                        st.session_state[f"editing_member_{member['id']}"] = False
                        st.rerun()
                
                # Show detailed view if viewing
                if st.session_state.get(f"viewing_member_{member['id']}", False):
                    st.divider()
                    st.subheader(f"Member Details: {member.get('full_name', 'N/A')}")
                    show_member_details(member)
                    
                    if st.button("✅ Close View", key=f"close_view_{member['id']}"):
                        st.session_state[f"viewing_member_{member['id']}"] = False
                        st.rerun()
        
        # Pagination controls
        st.divider()
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=(st.session_state.admin_page == 1)):
                st.session_state.admin_page = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ Prev", disabled=(st.session_state.admin_page == 1)):
                st.session_state.admin_page -= 1
                st.rerun()
        
        with col3:
            # Page selector
            new_page = st.selectbox(
                f"Page {st.session_state.admin_page} of {total_pages}:",
                range(1, total_pages + 1),
                index=st.session_state.admin_page - 1,
                key="page_selector"
            )
            if new_page != st.session_state.admin_page:
                st.session_state.admin_page = new_page
                st.rerun()
        
        with col4:
            if st.button("▶️ Next", disabled=(st.session_state.admin_page == total_pages)):
                st.session_state.admin_page += 1
                st.rerun()
        
        with col5:
            if st.button("⏭️ Last", disabled=(st.session_state.admin_page == total_pages)):
                st.session_state.admin_page = total_pages
                st.rerun()
                
    except Exception as e:
        st.error(f"Error loading members: {e}")

def show_member_details(member):
    """Show detailed view of a member (read-only)."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Basic Information**")
        st.write(f"Full Name: {member.get('full_name', 'N/A')}")
        st.write(f"Normalized Name: {member.get('full_name_normalized', 'N/A')}")
        st.write(f"Primary Email: {member.get('primary_email', 'N/A')}")
        st.write(f"Mobile Phone: {member.get('mobile_phone', 'N/A')}")
        st.write(f"Home Phone: {member.get('home_phone', 'N/A')}")
        
        st.write("**Professional Information**")
        st.write(f"Current Profession: {member.get('current_profession', 'N/A')}")
        st.write(f"Company: {member.get('current_company', 'N/A')}")
        st.write(f"LinkedIn: {member.get('linkedin_profile', 'N/A')}")
        
    with col2:
        st.write("**Address Information**")
        st.write(f"Home Address: {member.get('home_address_full', 'N/A')}")
        st.write(f"Office Address: {member.get('office_address_full', 'N/A')}")
        
        st.write("**Academic Information**")
        st.write(f"Batch: {member.get('batch_normalized', 'N/A')}")
        st.write(f"Chapter: {member.get('school_chapter_normalized', 'N/A')}")
        st.write(f"Degree: {member.get('degree_course', 'N/A')}")
        
        st.write("**Personal Interests**")
        st.write(f"Interests/Hobbies: {member.get('interests_hobbies', 'N/A')}")
        st.write(f"Sports: {member.get('sports_activities', 'N/A')}")
        st.write(f"Volunteer Work: {member.get('volunteer_work', 'N/A')}")
        st.write(f"Social Clubs: {member.get('social_clubs', 'N/A')}")
        
        st.write("**System Information**")
        st.write(f"Confidence Score: {member.get('confidence_score', 'N/A')}")
        st.write(f"Data Completeness: {member.get('data_completeness_score', 'N/A')}")
        st.write(f"Created: {member.get('created_at', 'N/A')}")
        st.write(f"Updated: {member.get('updated_at', 'N/A')}")
        st.write(f"Active: {'Yes' if member.get('is_active', True) else 'No'}")

def admin_interface():
    """Admin interface for data management."""
    st.title("⚙️ Admin Panel")
    
    # Password protection
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.warning("🔒 Admin access requires authentication")
        
        with st.form("admin_login"):
            password = st.text_input("Enter Admin Password:", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if password == "SJ92C!":
                    st.session_state.admin_authenticated = True
                    st.success("✅ Access granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
        return
    
    # Data import section
    st.header("📥 Data Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Import from Raw_Files")
        
        if RAW_FILES_DIR.exists():
            files_count = len(list(RAW_FILES_DIR.rglob("*.*")))
            st.info(f"Found {files_count} files in Raw_Files directory")
            
            if st.button("🚀 Import All Files"):
                with st.spinner("Importing data..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # This would need to be modified to show progress
                        results = st.session_state.data_processor.import_all_files()
                        progress_bar.progress(100)
                        
                        st.success("Import completed!")
                        st.json(results)
                        
                    except Exception as e:
                        st.error(f"Import failed: {e}")
        else:
            st.warning("Raw_Files directory not found")
    
    with col2:
        st.subheader("File Upload")
        uploaded_files = st.file_uploader(
            "Upload member data files",
            accept_multiple_files=True,
            type=['xls', 'xlsx', 'doc', 'docx', 'txt', 'csv']
        )
        
        if uploaded_files:
            st.info(f"Uploaded {len(uploaded_files)} files")
            # TODO: Implement file processing
    
    # Data quality section
    st.header("📈 Data Quality")
    
    try:
        quality_stats = st.session_state.db_manager.get_data_quality_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Completeness", f"{quality_stats.get('avg_completeness', 0):.1%}")
        with col2:
            st.metric("Confidence", f"{quality_stats.get('avg_confidence', 0):.1%}")
        with col3:
            st.metric("With Email", quality_stats.get('with_email', 0))
        with col4:
            st.metric("With Mobile", quality_stats.get('with_mobile', 0))
        
    except Exception as e:
        st.error(f"Could not load quality stats: {e}")
    
    # Member Management
    st.header("👤 Member Management")
    
    # Tabs for different member operations
    tab1, tab2, tab3 = st.tabs(["📋 All Members", "🔍 Search & Edit", "➕ Add New Member"])
    
    with tab1:
        show_all_members_interface()
    
    with tab2:
        st.subheader("Search and Edit Members")
        
        search_name = st.text_input("Search by name:", placeholder="Enter member name...")
        
        if search_name:
            with st.spinner("Searching members..."):
                try:
                    # Search for members
                    search_results = st.session_state.db_manager.search_members({'name': search_name})
                    
                    if search_results:
                        st.success(f"Found {len(search_results)} members")
                        
                        # Display results in a selectbox
                        member_options = {}
                        for member in search_results:
                            display_name = f"{member['full_name']} - {member.get('batch_normalized', 'No batch')} - {member.get('primary_email', 'No email')}"
                            member_options[display_name] = member
                        
                        selected_display = st.selectbox("Select member to edit:", list(member_options.keys()))
                        
                        if selected_display:
                            selected_member = member_options[selected_display]
                            show_member_editor(selected_member)
                            
                    else:
                        st.warning("No members found with that name")
                        
                except Exception as e:
                    st.error(f"Search error: {e}")
    
    with tab3:
        show_add_member_form()
    
    st.divider()
    
    # Duplicate management
    st.header("🔍 Duplicate Management")
    
    if st.button("Find Potential Duplicates"):
        with st.spinner("Searching for duplicates..."):
            try:
                duplicates = st.session_state.db_manager.get_potential_duplicates()
                
                if duplicates:
                    st.warning(f"Found {len(duplicates)} potential duplicate pairs")
                    
                    for dup in duplicates[:10]:  # Show first 10
                        with st.expander(f"Potential match: {dup['name1']} ↔ {dup['name2']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Member 1**: {dup['name1']}")
                                st.write(f"Email: {dup.get('email1', 'N/A')}")
                            with col2:
                                st.write(f"**Member 2**: {dup['name2']}")
                                st.write(f"Email: {dup.get('email2', 'N/A')}")
                            
                            if st.button(f"Merge {dup['id1']} → {dup['id2']}", key=f"merge_{dup['id1']}_{dup['id2']}"):
                                # TODO: Implement merge functionality
                                st.success("Merge scheduled (not implemented yet)")
                else:
                    st.success("No potential duplicates found!")
                    
            except Exception as e:
                st.error(f"Error finding duplicates: {e}")

def main():
    """Main application entry point."""
    # Check database first
    if not check_database():
        return
    
    # Sidebar navigation
    st.sidebar.title("🏢 SJ Directory")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🔍 Search", "⚙️ Admin", "ℹ️ About"]
    )
    
    # Show stats in sidebar
    sidebar_stats()
    
    # Route to appropriate page
    if page == "🔍 Search":
        main_search_interface()
    elif page == "⚙️ Admin":
        admin_interface()
    elif page == "ℹ️ About":
        show_about_page()
    
    # Add logout button for admin
    if page == "⚙️ Admin" and st.session_state.get('admin_authenticated', False):
        if st.sidebar.button("🚪 Logout Admin"):
            st.session_state.admin_authenticated = False
            st.rerun()

def show_about_page():
    """Show about/help page."""
    st.title("ℹ️ About SJ Professional Directory")
    
    st.markdown("""
    ## 🎯 Purpose
    Transform how fraternity members find professional help by replacing group chat queries 
    with intelligent professional services matching.
    
    ## 🔍 How to Search
    
    ### Professional Services Examples:
    - *"I need a family lawyer in Bulacan"*
    - *"Do we have a cardiologist at Heart Center?"*
    - *"Find accountants in Makati CBD"*
    - *"Looking for civil engineers in Quezon City"*
    
    ### Directory Search Examples:
    - *"Find Juan Dela Cruz"*
    - *"Show me batch 95-S members"*
    - *"List all UP Diliman brothers"*
    - *"Members from Iloilo chapter"*
    
    ## 🤖 AI Features
    - **Smart Profession Detection**: Automatically infers professions from email domains, company names
    - **Location Intelligence**: Understands work vs. home addresses
    - **Fuzzy Matching**: Finds results even with spelling variations
    - **Confidence Scoring**: Shows how reliable the match is
    
    ## 📊 Data Quality
    The system automatically:
    - Detects and merges duplicate records
    - Normalizes names, batches, and locations
    - Tracks data freshness and completeness
    - Maintains audit trails of all changes
    """)
    
    # System info
    st.header("🛠️ System Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Database**: {DATABASE_PATH}")
        st.info(f"**Data Source**: {RAW_FILES_DIR}")
    
    with col2:
        if DATABASE_PATH.exists():
            size_mb = DATABASE_PATH.stat().st_size / (1024 * 1024)
            st.info(f"**Database Size**: {size_mb:.1f} MB")
        
        st.info(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()