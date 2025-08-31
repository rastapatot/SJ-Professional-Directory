-- ============================================================================
-- SJ PROFESSIONAL DIRECTORY DATABASE SCHEMA
-- ============================================================================
-- Complete schema with normalization, audit trails, and AI inference support
-- Created: 2024-08-31
-- ============================================================================

-- ============================================================================
-- CORE MEMBER INFORMATION TABLE
-- ============================================================================
CREATE TABLE members (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- ========================================================================
    -- PERSONAL INFORMATION (Normalized)
    -- ========================================================================
    full_name TEXT NOT NULL,
    full_name_normalized TEXT, -- lowercase, standardized format for matching
    nickname TEXT,
    nickname_normalized TEXT,
    birth_date DATE,
    
    -- ========================================================================  
    -- ACADEMIC INFORMATION (Normalized)
    -- ========================================================================
    school_chapter TEXT,
    school_chapter_normalized TEXT, -- "UP Diliman", "UST", etc.
    
    -- Batch Information (Original + Normalized)
    batch_original TEXT,           -- "95-S", "Batch 93-B", etc. (as written)
    batch_year INTEGER,            -- 1995, 1993 (4-digit normalized)
    batch_semester TEXT,           -- 'S', 'B', 'G', 'E' (extracted letter)
    batch_sub_number INTEGER,      -- 1, 2 (for cases like "S1", "S2")
    batch_normalized TEXT,         -- "1995-S" (standardized format)
    batch_decade INTEGER,          -- 1990, 2000 (for grouping)
    batch_era TEXT,               -- "90s", "2000s" (for queries)
    
    course TEXT,
    course_normalized TEXT,
    
    -- Batchmates (comma-separated list for now)
    batchmates TEXT,
    
    -- ========================================================================
    -- CONTACT INFORMATION (with data vintage)
    -- ========================================================================
    primary_email TEXT,
    primary_email_collected_date DATE,
    secondary_email TEXT,
    secondary_email_collected_date DATE,
    
    home_phone TEXT,
    home_phone_collected_date DATE,
    mobile_phone TEXT,
    mobile_phone_collected_date DATE,
    office_phone TEXT,
    office_phone_collected_date DATE,
    
    -- ========================================================================
    -- ADDRESS INFORMATION (Normalized with vintage)
    -- ========================================================================
    -- Home Address
    home_address_full TEXT,              -- full address as provided
    home_address_city TEXT,              -- extracted city
    home_address_city_normalized TEXT,   -- "Makati City" -> "Makati"
    home_address_provincial TEXT,        -- provincial/permanent address
    home_address_collected_date DATE,
    
    -- Office Address  
    office_address_full TEXT,            -- full office address
    office_address_city TEXT,            -- extracted office city
    office_address_city_normalized TEXT, -- normalized office city
    office_address_collected_date DATE,
    
    -- Geographic coding for queries
    home_region TEXT,                    -- Metro Manila, Region 1, etc.
    office_region TEXT,
    
    -- ========================================================================
    -- PROFESSIONAL INFORMATION (with vintage)
    -- ========================================================================
    current_profession TEXT,
    current_profession_normalized TEXT,   -- "Doctor" -> "Medical Doctor"
    profession_collected_date DATE,
    
    current_company TEXT,
    current_company_normalized TEXT,
    company_collected_date DATE,
    
    job_title TEXT,
    job_title_collected_date DATE,
    
    -- Professional Services (for matching)
    services_offered TEXT,               -- JSON array of services
    practice_areas TEXT,                 -- JSON array of specializations
    willing_to_help_members BOOLEAN DEFAULT TRUE,
    
    -- ========================================================================
    -- ORGANIZATIONAL INFORMATION
    -- ========================================================================
    positions_held TEXT,                 -- fraternity positions held
    positions_collected_date DATE,
    member_status TEXT DEFAULT 'active', -- active, alumni, inactive, deceased
    membership_start_date DATE,
    
    -- ========================================================================
    -- AI INFERENCE RESULTS (with confidence scores)
    -- ========================================================================
    inferred_profession TEXT,
    inferred_profession_confidence REAL,
    inferred_profession_source TEXT,     -- "email_domain", "company_name", etc.
    
    inferred_specialization TEXT,
    inferred_specialization_confidence REAL,
    
    inferred_service_category TEXT,      -- "Legal", "Medical", "Business", etc.
    inferred_service_category_confidence REAL,
    
    inferred_work_location TEXT,
    inferred_work_location_confidence REAL,
    
    -- Professional address type inference
    address_type_home TEXT,              -- "residential", "business", "mixed"
    address_type_office TEXT,            -- "professional", "residential", "unknown"
    
    -- ========================================================================
    -- DATA PROVENANCE & VINTAGE
    -- ========================================================================
    original_data_collected_date DATE,   -- when source data was originally collected
    estimated_data_vintage DATE,         -- estimated age of the information
    source_file_name TEXT,               -- which file this record came from
    source_file_creation_date DATE,      -- file creation timestamp
    source_file_modified_date DATE,      -- file last modified timestamp
    
    -- ========================================================================
    -- RECORD MANAGEMENT & AUDIT TRAIL
    -- ========================================================================
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system_import',
    imported_from_source TEXT,           -- specific source identification
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT DEFAULT 'system',
    last_verified_date DATE,             -- when data was last verified as correct
    
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_duplicate BOOLEAN DEFAULT FALSE,  -- marked as duplicate of another record
    primary_record_id INTEGER,           -- if duplicate, points to primary record
    
    -- Data quality indicators
    data_completeness_score REAL,        -- 0.0-1.0 based on filled fields
    data_freshness_score REAL,          -- 0.0-1.0 based on age
    confidence_score REAL,              -- overall confidence in record accuracy
    
    -- Search optimization
    search_text TEXT,                    -- combined searchable text for FTS
    
    FOREIGN KEY (primary_record_id) REFERENCES members(id)
);

-- ============================================================================
-- MEMBER CHANGE HISTORY TABLE
-- ============================================================================
CREATE TABLE member_change_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    
    -- What Changed
    field_name TEXT NOT NULL,            -- which field was changed
    old_value TEXT,                      -- previous value
    new_value TEXT,                      -- new value
    old_collected_date DATE,             -- when old data was originally collected
    new_collected_date DATE,             -- when new data was collected
    
    -- Change Classification
    change_type TEXT NOT NULL,           -- 'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'INFER'
    change_reason TEXT,                  -- 'data_import', 'manual_update', 'duplicate_merge', 'ai_inference', 'verification'
    
    -- Change Metadata
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT,                     -- user or system identifier
    source_file TEXT,                    -- which file triggered the change
    confidence_score REAL,              -- confidence in the change (for AI inferences)
    
    -- Impact Assessment
    affects_queries BOOLEAN DEFAULT FALSE, -- does this change affect search results?
    verified BOOLEAN DEFAULT FALSE,      -- has this change been verified?
    
    FOREIGN KEY (member_id) REFERENCES members(id)
);

-- ============================================================================
-- DATA SOURCES AND IMPORT TRACKING
-- ============================================================================
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT,
    file_type TEXT,                      -- 'excel', 'word', 'access', 'text'
    file_size INTEGER,
    file_creation_date DATE,
    file_modified_date DATE,
    
    -- Data Vintage Assessment
    estimated_data_collection_date DATE, -- when we think the data was collected
    data_vintage_notes TEXT,             -- human notes about data age
    data_quality_assessment TEXT,        -- notes about data quality
    
    -- Processing Information
    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_by TEXT,
    processing_status TEXT,              -- 'pending', 'processing', 'completed', 'failed'
    
    -- Statistics
    total_records_found INTEGER,
    records_imported INTEGER,
    records_updated INTEGER,
    records_skipped INTEGER,
    duplicates_found INTEGER,
    
    processing_notes TEXT
);

-- ============================================================================
-- IMPORT BATCHES (for tracking individual import runs)
-- ============================================================================
CREATE TABLE import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_name TEXT,                     -- descriptive name for this import
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imported_by TEXT,
    
    -- Source Information
    source_files TEXT,                   -- JSON array of files processed
    import_type TEXT,                    -- 'initial', 'update', 'merge', 'verification'
    
    -- Results
    total_files_processed INTEGER,
    total_records_processed INTEGER,
    records_created INTEGER,
    records_updated INTEGER,
    records_merged INTEGER,
    records_skipped INTEGER,
    errors_encountered INTEGER,
    
    -- Status
    import_status TEXT,                  -- 'success', 'partial', 'failed'
    completion_time TIMESTAMP,
    processing_duration_seconds INTEGER,
    
    notes TEXT,
    error_log TEXT                       -- JSON array of error messages
);

-- ============================================================================
-- DUPLICATE DETECTION AND MERGING
-- ============================================================================
CREATE TABLE duplicate_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT,                     -- descriptive name for the duplicate group
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    -- Primary record (the one we keep)
    primary_member_id INTEGER NOT NULL,
    
    -- Duplicate detection metadata
    detection_method TEXT,               -- 'name_similarity', 'email_match', 'manual', etc.
    confidence_score REAL,              -- how confident we are these are duplicates
    
    -- Status
    merge_status TEXT DEFAULT 'pending', -- 'pending', 'merged', 'rejected'
    merged_at TIMESTAMP,
    merged_by TEXT,
    
    merge_notes TEXT,
    
    FOREIGN KEY (primary_member_id) REFERENCES members(id)
);

CREATE TABLE duplicate_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    duplicate_group_id INTEGER NOT NULL,
    duplicate_member_id INTEGER NOT NULL,
    
    -- Why this was flagged as duplicate
    matching_fields TEXT,                -- JSON array of fields that matched
    similarity_score REAL,              -- similarity score for this match
    
    -- What fields to merge
    fields_to_merge TEXT,                -- JSON object mapping fields to merge
    merge_strategy TEXT,                 -- 'keep_newest', 'keep_both', 'manual_review'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (duplicate_group_id) REFERENCES duplicate_groups(id),
    FOREIGN KEY (duplicate_member_id) REFERENCES members(id)
);

-- ============================================================================
-- PROFESSIONAL SERVICES CLASSIFICATION
-- ============================================================================
CREATE TABLE service_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL,         -- "Legal", "Medical", "Business", etc.
    parent_category_id INTEGER,          -- for hierarchical categories
    description TEXT,
    keywords TEXT,                       -- JSON array of keywords for matching
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_category_id) REFERENCES service_categories(id)
);

CREATE TABLE member_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    service_category_id INTEGER NOT NULL,
    
    -- Service Details
    service_description TEXT,
    specializations TEXT,                -- JSON array of specializations
    years_experience INTEGER,
    
    -- Availability
    available_for_consultation BOOLEAN DEFAULT TRUE,
    preferred_contact_method TEXT,       -- 'email', 'phone', 'both'
    consultation_fee_range TEXT,         -- 'free', 'low', 'medium', 'high', 'varies'
    
    -- Geographic Service Area
    service_locations TEXT,              -- JSON array of cities/regions served
    willing_to_travel BOOLEAN DEFAULT FALSE,
    remote_consultation BOOLEAN DEFAULT FALSE,
    
    -- Data Source
    source TEXT,                         -- 'inferred', 'manual', 'verified'
    confidence_score REAL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    verified_by TEXT,
    
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (service_category_id) REFERENCES service_categories(id)
);

-- ============================================================================
-- QUERY LOG (for improving AI responses)
-- ============================================================================
CREATE TABLE query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    query_type TEXT,                     -- 'directory_search', 'professional_service', 'contact_lookup'
    
    -- Query Processing
    processed_query TEXT,                -- normalized/processed version
    extracted_profession TEXT,
    extracted_location TEXT,
    extracted_specialization TEXT,
    
    -- Results
    results_count INTEGER,
    result_member_ids TEXT,              -- JSON array of member IDs returned
    
    -- User Interaction
    query_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_session_id TEXT,
    user_ip TEXT,
    
    -- Feedback
    user_rating INTEGER,                 -- 1-5 rating of result quality
    user_feedback TEXT,
    clicked_results TEXT,                -- JSON array of which results user clicked
    
    -- Performance
    processing_time_ms INTEGER,
    search_method TEXT                   -- which search algorithm was used
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary search indexes
CREATE INDEX idx_members_name ON members(full_name_normalized);
CREATE INDEX idx_members_email ON members(primary_email);
CREATE INDEX idx_members_batch ON members(batch_normalized);
CREATE INDEX idx_members_chapter ON members(school_chapter_normalized);
CREATE INDEX idx_members_profession ON members(current_profession_normalized);
CREATE INDEX idx_members_company ON members(current_company_normalized);
CREATE INDEX idx_members_location ON members(home_address_city_normalized, office_address_city_normalized);

-- Data quality indexes
CREATE INDEX idx_members_active ON members(is_active);
CREATE INDEX idx_members_duplicate ON members(is_duplicate);
CREATE INDEX idx_members_data_vintage ON members(estimated_data_vintage);
CREATE INDEX idx_members_confidence ON members(confidence_score);

-- Audit trail indexes
CREATE INDEX idx_history_member ON member_change_history(member_id);
CREATE INDEX idx_history_date ON member_change_history(changed_at);
CREATE INDEX idx_history_field ON member_change_history(field_name);

-- Professional services indexes
CREATE INDEX idx_services_member ON member_services(member_id);
CREATE INDEX idx_services_category ON member_services(service_category_id);
CREATE INDEX idx_services_available ON member_services(available_for_consultation);

-- Full-text search index (if supported)
-- CREATE VIRTUAL TABLE members_fts USING fts5(full_name, profession, company, address, content=members);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active members with complete contact info
CREATE VIEW active_members AS
SELECT * FROM members 
WHERE is_active = TRUE 
  AND is_duplicate = FALSE 
  AND (primary_email IS NOT NULL OR mobile_phone IS NOT NULL);

-- Professional services directory
CREATE VIEW professional_directory AS
SELECT 
    m.id,
    m.full_name,
    m.nickname,
    m.primary_email,
    m.mobile_phone,
    m.current_profession_normalized as profession,
    m.current_company_normalized as company,
    m.office_address_city_normalized as work_location,
    m.home_address_city_normalized as home_location,
    sc.category_name as service_category,
    ms.service_description,
    ms.available_for_consultation,
    m.confidence_score,
    m.estimated_data_vintage
FROM members m
LEFT JOIN member_services ms ON m.id = ms.member_id
LEFT JOIN service_categories sc ON ms.service_category_id = sc.id
WHERE m.is_active = TRUE 
  AND m.is_duplicate = FALSE;

-- Data quality summary
CREATE VIEW data_quality_summary AS
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN primary_email IS NOT NULL THEN 1 END) as with_email,
    COUNT(CASE WHEN mobile_phone IS NOT NULL THEN 1 END) as with_mobile,
    COUNT(CASE WHEN current_profession IS NOT NULL THEN 1 END) as with_profession,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_members,
    COUNT(CASE WHEN is_duplicate = TRUE THEN 1 END) as duplicates,
    AVG(confidence_score) as avg_confidence,
    AVG(data_completeness_score) as avg_completeness
FROM members;

-- ============================================================================
-- TRIGGERS FOR AUDIT TRAIL
-- ============================================================================

-- Update timestamp trigger
CREATE TRIGGER update_member_timestamp 
AFTER UPDATE ON members
BEGIN
    UPDATE members 
    SET updated_at = CURRENT_TIMESTAMP,
        version = version + 1
    WHERE id = NEW.id;
END;

-- Change history trigger (simplified - would need more complex logic in practice)
CREATE TRIGGER log_member_changes
AFTER UPDATE ON members
FOR EACH ROW
BEGIN
    INSERT INTO member_change_history (
        member_id, 
        field_name, 
        old_value, 
        new_value, 
        change_type,
        change_reason
    )
    SELECT 
        NEW.id,
        'bulk_update', -- In practice, this would be more specific
        'multiple_fields',
        'multiple_fields',
        'UPDATE',
        'record_update';
END;

-- ============================================================================
-- INITIAL DATA SETUP
-- ============================================================================

-- Insert basic service categories
INSERT INTO service_categories (category_name, description, keywords) VALUES
('Legal', 'Legal services and law practice', '["lawyer", "attorney", "legal", "law", "counsel", "advocate"]'),
('Medical', 'Healthcare and medical services', '["doctor", "physician", "medical", "healthcare", "clinic", "hospital", "md"]'),
('Business', 'Business and financial services', '["business", "finance", "accounting", "consulting", "management", "cpa"]'),
('Engineering', 'Engineering and technical services', '["engineer", "engineering", "technical", "pe", "civil", "electrical", "mechanical"]'),
('Education', 'Educational services and academia', '["teacher", "professor", "education", "school", "university", "academic"]'),
('Government', 'Government and public service', '["government", "public", "civil service", "bureau", "department", "ministry"]'),
('IT/Technology', 'Information technology services', '["programmer", "developer", "it", "technology", "software", "computer", "tech"]'),
('Real Estate', 'Real estate and property services', '["real estate", "property", "broker", "realtor", "development"]'),
('Other', 'Other professional services', '[]');

-- ============================================================================
-- SCHEMA VERSION TRACKING
-- ============================================================================
CREATE TABLE schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES 
('1.0.0', 'Initial schema with full normalization, audit trails, and AI inference support');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================