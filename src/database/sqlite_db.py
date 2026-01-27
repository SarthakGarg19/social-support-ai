"""
SQLite Database Manager for Social Support Application

This module handles all structured data storage including applicant information,
assessments, and document metadata.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from ..config import settings


class SQLiteManager:
    """
    Manages SQLite database operations for the application.
    
    Handles:
    - Applicant records
    - Assessment results
    - Document metadata
    - Application workflow state
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize SQLite database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or settings.sqlite_db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Applicants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applicants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    emirates_id TEXT,
                    family_size INTEGER,
                    monthly_income REAL,
                    employment_status TEXT,
                    contact_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Assessments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    applicant_id TEXT NOT NULL,
                    eligibility_score REAL,
                    decision TEXT,
                    reasoning TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (applicant_id) REFERENCES applicants(id)
                )
            """)
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    applicant_id TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    file_path TEXT,
                    extracted_data TEXT,
                    validation_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (applicant_id) REFERENCES applicants(id)
                )
            """)
            
            # Workflow state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_state (
                    id TEXT PRIMARY KEY,
                    applicant_id TEXT NOT NULL,
                    current_stage TEXT,
                    stage_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (applicant_id) REFERENCES applicants(id)
                )
            """)
    
    def create_applicant(self, applicant_data: Dict[str, Any]) -> str:
        """
        Create a new applicant record.
        
        Args:
            applicant_data: Dictionary containing applicant information
            
        Returns:
            Applicant ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            applicant_id = applicant_data.get('id', f"APP_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            cursor.execute("""
                INSERT INTO applicants (id, name, emirates_id, family_size, 
                                      monthly_income, employment_status, contact_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                applicant_id,
                applicant_data.get('name'),
                applicant_data.get('emirates_id'),
                applicant_data.get('family_size'),
                applicant_data.get('monthly_income'),
                applicant_data.get('employment_status'),
                json.dumps(applicant_data.get('contact_info', {}))
            ))
            
            return applicant_id
    
    def get_applicant(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve applicant information by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applicants WHERE id = ?", (applicant_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def save_document(self, doc_data: Dict[str, Any]) -> str:
        """
        Save document metadata.
        
        Args:
            doc_data: Document information including type, path, extracted data
            
        Returns:
            Document ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            doc_id = doc_data.get('id', f"DOC_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
            
            cursor.execute("""
                INSERT INTO documents (id, applicant_id, doc_type, file_path, 
                                     extracted_data, validation_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                doc_data.get('applicant_id'),
                doc_data.get('doc_type'),
                doc_data.get('file_path'),
                json.dumps(doc_data.get('extracted_data', {})),
                doc_data.get('validation_status', 'pending')
            ))
            
            return doc_id
    
    def save_assessment(self, assessment_data: Dict[str, Any]) -> str:
        """
        Save assessment results.
        
        Args:
            assessment_data: Assessment results including score, decision, reasoning
            
        Returns:
            Assessment ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            assessment_id = assessment_data.get('id', f"ASS_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            cursor.execute("""
                INSERT INTO assessments (id, applicant_id, eligibility_score, 
                                       decision, reasoning, recommendations)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                assessment_id,
                assessment_data.get('applicant_id'),
                assessment_data.get('eligibility_score'),
                assessment_data.get('decision'),
                assessment_data.get('reasoning'),
                json.dumps(assessment_data.get('recommendations', []))
            ))
            
            return assessment_id
    
    def get_assessment(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve assessment for an applicant."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM assessments WHERE applicant_id = ? ORDER BY created_at DESC LIMIT 1",
                (applicant_id,)
            )
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                if result.get('recommendations'):
                    result['recommendations'] = json.loads(result['recommendations'])
                return result
            return None
    
    def update_workflow_state(self, applicant_id: str, stage: str, stage_data: Dict[str, Any]):
        """Update workflow state for an applicant."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if workflow state exists
            cursor.execute(
                "SELECT id FROM workflow_state WHERE applicant_id = ?",
                (applicant_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE workflow_state 
                    SET current_stage = ?, stage_data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE applicant_id = ?
                """, (stage, json.dumps(stage_data), applicant_id))
            else:
                state_id = f"WF_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                cursor.execute("""
                    INSERT INTO workflow_state (id, applicant_id, current_stage, stage_data)
                    VALUES (?, ?, ?, ?)
                """, (state_id, applicant_id, stage, json.dumps(stage_data)))
    
    def get_workflow_state(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state for an applicant."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workflow_state WHERE applicant_id = ?",
                (applicant_id,)
            )
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                if result.get('stage_data'):
                    result['stage_data'] = json.loads(result['stage_data'])
                return result
            return None


# Global database instance
db_manager = SQLiteManager()
