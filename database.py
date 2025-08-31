# SJ Professional Directory - Database Manager
# ============================================================================

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import json
from contextlib import contextmanager

from config import SCHEMA_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations for the SJ Professional Directory."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper settings and automatic cleanup."""
        connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # Allow use across threads
            timeout=30.0  # 30 second timeout
        )
        connection.row_factory = sqlite3.Row  # Enable dict-like access
        connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        
        try:
            yield connection
        finally:
            connection.close()
    
    def close_connection(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def create_database(self):
        """Create database from schema file."""
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
        
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            try:
                # Execute schema using executescript for multiple statements
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Database schema created successfully")
            except Exception as e:
                conn.rollback()
                logger.error(f"Error creating database schema: {e}")
                # Try alternative method - split by semicolon
                try:
                    logger.info("Trying alternative method...")
                    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                    for statement in statements:
                        if statement and not statement.startswith('--'):
                            conn.execute(statement + ';')
                    conn.commit()
                    logger.info("Database schema created successfully (alternative method)")
                except Exception as e2:
                    conn.rollback()
                    logger.error(f"Alternative method also failed: {e2}")
                    raise e
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def insert_member(self, member_data: Dict[str, Any]) -> int:
        """Insert a new member record."""
        with self.get_connection() as conn:
            try:
                # Prepare insert statement
                columns = list(member_data.keys())
                placeholders = ['?' for _ in columns]
                values = list(member_data.values())
                
                sql = f"""
                INSERT INTO members ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                """
                
                cursor = conn.execute(sql, values)
                member_id = cursor.lastrowid
                conn.commit()
                logger.debug(f"Inserted member with ID: {member_id}")
                return member_id
            except Exception as e:
                conn.rollback()
                logger.error(f"Error inserting member: {e}")
                raise
    
    def update_member(self, member_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing member record."""
        if not updates:
            return True
        
        conn = self.get_connection()
        
        # Build SET clause
        set_clauses = [f"{col} = ?" for col in updates.keys()]
        values = list(updates.values()) + [member_id]
        
        sql = f"""
        UPDATE members 
        SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        
        try:
            cursor = conn.execute(sql, values)
            conn.commit()
            logger.debug(f"Updated member {member_id}: {cursor.rowcount} rows affected")
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating member {member_id}: {e}")
            raise
    
    def get_member_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        """Get member by ID."""
        conn = self.get_connection()
        
        sql = "SELECT * FROM members WHERE id = ? AND is_active = TRUE"
        cursor = conn.execute(sql, (member_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def search_members(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search members with various filters."""
        conn = self.get_connection()
        
        where_clauses = ["is_active = TRUE", "is_duplicate = FALSE"]
        params = []
        
        # Build dynamic WHERE clause
        if query_params.get('name'):
            where_clauses.append("full_name_normalized LIKE ?")
            params.append(f"%{query_params['name'].lower()}%")
        
        if query_params.get('profession'):
            where_clauses.append("""
                (current_profession LIKE ? 
                 OR current_profession_normalized LIKE ? 
                 OR inferred_profession LIKE ?)
            """)
            prof = f"%{query_params['profession'].lower()}%"
            params.extend([prof, prof, prof])
        
        if query_params.get('location'):
            where_clauses.append("""
                (home_address_full LIKE ?
                 OR office_address_full LIKE ?
                 OR home_address_city_normalized LIKE ? 
                 OR office_address_city_normalized LIKE ?)
            """)
            loc = f"%{query_params['location'].lower()}%"
            params.extend([loc, loc, loc, loc])
        
        if query_params.get('batch'):
            where_clauses.append("batch_normalized LIKE ?")
            params.append(f"%{query_params['batch']}%")
        
        if query_params.get('chapter'):
            where_clauses.append("school_chapter_normalized LIKE ?")
            params.append(f"%{query_params['chapter'].lower()}%")
        
        sql = f"""
        SELECT * FROM members 
        WHERE {' AND '.join(where_clauses)}
        ORDER BY confidence_score DESC, full_name
        LIMIT 100
        """
        
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def log_change(self, member_id: int, field_name: str, old_value: Any, 
                   new_value: Any, change_type: str, change_reason: str,
                   source_file: str = None, confidence_score: float = None):
        """Log a change to member data."""
        conn = self.get_connection()
        
        sql = """
        INSERT INTO member_change_history 
        (member_id, field_name, old_value, new_value, change_type, 
         change_reason, source_file, confidence_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            conn.execute(sql, (
                member_id, field_name, str(old_value) if old_value else None,
                str(new_value) if new_value else None, change_type,
                change_reason, source_file, confidence_score
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging change: {e}")
    
    def get_member_history(self, member_id: int) -> List[Dict[str, Any]]:
        """Get change history for a member."""
        conn = self.get_connection()
        
        sql = """
        SELECT * FROM member_change_history 
        WHERE member_id = ? 
        ORDER BY changed_at DESC
        """
        
        cursor = conn.execute(sql, (member_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def find_potential_duplicates(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Find potential duplicate members."""
        conn = self.get_connection()
        
        # Find members with similar names or identical emails
        sql = """
        SELECT 
            m1.id as id1, m1.full_name as name1, m1.primary_email as email1,
            m2.id as id2, m2.full_name as name2, m2.primary_email as email2,
            CASE 
                WHEN m1.primary_email = m2.primary_email THEN 'email_match'
                ELSE 'name_similarity'
            END as match_type
        FROM members m1
        JOIN members m2 ON m1.id < m2.id
        WHERE m1.is_active = TRUE AND m2.is_active = TRUE
        AND m1.is_duplicate = FALSE AND m2.is_duplicate = FALSE
        AND (
            m1.primary_email = m2.primary_email
            OR (
                m1.full_name_normalized LIKE '%' || m2.full_name_normalized || '%'
                OR m2.full_name_normalized LIKE '%' || m1.full_name_normalized || '%'
            )
        )
        LIMIT ?
        """
        
        cursor = conn.execute(sql, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def merge_duplicates(self, primary_id: int, duplicate_ids: List[int]) -> Dict[str, Any]:
        """Merge duplicate member records."""
        conn = self.get_connection()
        
        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Get primary record
            primary = self.get_member_by_id(primary_id)
            if not primary:
                raise ValueError(f"Primary member {primary_id} not found")
            
            merged_count = 0
            
            for dup_id in duplicate_ids:
                # Mark duplicate as merged
                conn.execute("""
                    UPDATE members 
                    SET is_duplicate = TRUE, primary_record_id = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (primary_id, dup_id))
                
                # Log the merge
                self.log_change(
                    dup_id, 'record_status', 'active', 'merged',
                    'MERGE', 'duplicate_merge'
                )
                
                merged_count += 1
            
            conn.commit()
            logger.info(f"Merged {merged_count} duplicates into member {primary_id}")
            
            return {
                'primary_id': primary_id,
                'merged_count': merged_count,
                'merged_ids': duplicate_ids
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error merging duplicates: {e}")
            raise
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        conn = self.get_connection()
        
        stats = {}
        
        # Basic counts
        cursor = conn.execute("SELECT COUNT(*) FROM members WHERE is_active = TRUE")
        stats['total_members'] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM members WHERE is_duplicate = TRUE")
        stats['duplicates'] = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM members 
            WHERE is_active = TRUE AND primary_email IS NOT NULL
        """)
        stats['members_with_email'] = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM members 
            WHERE is_active = TRUE AND current_profession IS NOT NULL
        """)
        stats['members_with_profession'] = cursor.fetchone()[0]
        
        # Data quality
        cursor = conn.execute("""
            SELECT AVG(confidence_score) FROM members 
            WHERE is_active = TRUE AND confidence_score IS NOT NULL
        """)
        result = cursor.fetchone()[0]
        stats['avg_confidence'] = round(result, 2) if result else 0
        
        # Recent activity
        cursor = conn.execute("""
            SELECT COUNT(*) FROM member_change_history 
            WHERE changed_at >= datetime('now', '-7 days')
        """)
        stats['changes_last_week'] = cursor.fetchone()[0]
        
        return stats
    
    def get_import_stats(self) -> List[Dict[str, Any]]:
        """Get import batch statistics."""
        conn = self.get_connection()
        
        sql = """
        SELECT * FROM import_batches 
        ORDER BY import_date DESC 
        LIMIT 10
        """
        
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get data quality summary."""
        conn = self.get_connection()
        
        # This would typically use the data_quality_summary view from schema
        sql = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN primary_email IS NOT NULL THEN 1 END) as with_email,
            COUNT(CASE WHEN mobile_phone IS NOT NULL THEN 1 END) as with_mobile,
            COUNT(CASE WHEN current_profession IS NOT NULL THEN 1 END) as with_profession,
            COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_members,
            COUNT(CASE WHEN is_duplicate = TRUE THEN 1 END) as duplicates,
            AVG(confidence_score) as avg_confidence,
            AVG(data_completeness_score) as avg_completeness
        FROM members
        """
        
        cursor = conn.execute(sql)
        row = cursor.fetchone()
        return dict(row) if row else {}
    
    def get_potential_duplicates(self) -> List[Dict[str, Any]]:
        """Get potential duplicates for manual review."""
        return self.find_potential_duplicates(50)
    
    def create_import_batch(self, batch_name: str, source_files: List[str]) -> int:
        """Create a new import batch record."""
        conn = self.get_connection()
        
        sql = """
        INSERT INTO import_batches (batch_name, source_files, import_type)
        VALUES (?, ?, 'initial')
        """
        
        cursor = conn.execute(sql, (batch_name, json.dumps(source_files)))
        batch_id = cursor.lastrowid
        conn.commit()
        return batch_id
    
    def update_import_batch(self, batch_id: int, updates: Dict[str, Any]):
        """Update import batch with results."""
        updates['completion_time'] = datetime.now().isoformat()
        self.update_record('import_batches', batch_id, updates)
    
    def update_record(self, table: str, record_id: int, updates: Dict[str, Any]):
        """Generic method to update any record."""
        if not updates:
            return
        
        conn = self.get_connection()
        
        set_clauses = [f"{col} = ?" for col in updates.keys()]
        values = list(updates.values()) + [record_id]
        
        sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?"
        
        try:
            conn.execute(sql, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating {table} record {record_id}: {e}")
            raise