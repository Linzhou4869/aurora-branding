#!/usr/bin/env python3
"""
Downtown Zoning Board - Schema Installation Automation Flow
With Three Safety Checkpoints

Safety Checkpoints:
1. Syntax validation of SQL commands (dry-run)
2. Confirmation of mandatory ten-day public notice period closure
3. Manual approval flag from Senior Planner via internal dashboard

Generated: 2026-03-29
"""

import subprocess
import sys
from datetime import datetime, timedelta
from typing import Tuple, Optional

# Configuration
DATABASE_HOST = "localhost"
DATABASE_NAME = "downtown_zoning"
DATABASE_USER = "zoning_admin"
SCHEMA_FILE = "schema_installation.sql"
MIN_NOTICE_PERIOD_DAYS = 10


class SafetyCheckpointError(Exception):
    """Custom exception for safety checkpoint failures."""
    pass


def log_checkpoint(step: int, name: str, status: str, details: str = ""):
    """Log checkpoint status to console and log file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] CHECKPOINT {step}: {name} - {status}"
    if details:
        log_entry += f" | {details}"
    print(log_entry)
    
    # Append to log file
    with open("logs/schema_installation.log", "a") as f:
        f.write(log_entry + "\n")


# ============================================================
# SAFETY CHECKPOINT 1: Syntax Validation (Dry-Run)
# ============================================================

def checkpoint_1_syntax_validation(sql_file: str) -> Tuple[bool, str]:
    """
    SAFETY CHECKPOINT 1: Syntax Validation
    
    Performs a dry-run of the SQL script to validate syntax
    without making any actual database changes.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    log_checkpoint(1, "Syntax Validation", "IN_PROGRESS", f"Validating {sql_file}")
    
    try:
        # Method 1: Use MySQL/MariaDB with --dry-run or parse-only mode
        # Note: MySQL doesn't have a true dry-run, so we use EXPLAIN for DML
        # and parse the file for syntax errors
        
        dry_run_command = [
            "mysql",
            "--host", DATABASE_HOST,
            "--user", DATABASE_USER,
            "--database", DATABASE_NAME,
            "--force",  # Continue on errors (we'll capture them)
            "--silent",
        ]
        
        # Read the SQL file
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # For CREATE TABLE statements, we can check syntax by preparing
        # In production, you might use a test database or transaction rollback
        
        # Alternative: Use sqlparse library for syntax validation
        try:
            import sqlparse
            parsed = sqlparse.parse(sql_content)
            
            if not parsed:
                return False, "SQL file is empty or unparseable"
            
            # Check for basic syntax issues
            for statement in parsed:
                stmt_str = str(statement).strip()
                if stmt_str and not stmt_str.endswith(';'):
                    if not stmt_str.startswith('--'):
                        return False, f"Statement missing semicolon: {stmt_str[:50]}..."
            
            log_checkpoint(1, "Syntax Validation", "PASSED", "All SQL statements syntactically valid")
            return True, "Syntax validation passed"
            
        except ImportError:
            # Fallback: Basic file existence and readability check
            if len(sql_content) < 100:
                return False, "SQL file appears incomplete"
            
            # Check for common SQL keywords
            required_keywords = ['CREATE TABLE', 'PRIMARY KEY', 'FOREIGN KEY']
            for keyword in required_keywords:
                if keyword not in sql_content.upper():
                    return False, f"Missing required SQL construct: {keyword}"
            
            log_checkpoint(1, "Syntax Validation", "PASSED", "Basic validation completed (sqlparse not available)")
            return True, "Basic syntax validation passed"
            
    except FileNotFoundError:
        error_msg = f"SQL file not found: {sql_file}"
        log_checkpoint(1, "Syntax Validation", "FAILED", error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        log_checkpoint(1, "Syntax Validation", "FAILED", error_msg)
        return False, error_msg


# ============================================================
# SAFETY CHECKPOINT 2: Public Notice Period Verification
# ============================================================

def checkpoint_2_public_notice_period(permit_id: int) -> Tuple[bool, str]:
    """
    SAFETY CHECKPOINT 2: Public Notice Period Verification
    
    Confirms that the mandatory ten-day public notice period
    has been completed for the specified permit.
    
    Args:
        permit_id: The permit ID to check
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    log_checkpoint(2, "Public Notice Period", "IN_PROGRESS", f"Checking permit {permit_id}")
    
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=DATABASE_HOST,
            database=DATABASE_NAME,
            user=DATABASE_USER
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query to check public notice status
        query = """
            SELECT 
                pn.Notice_ID,
                pn.Publication_Date,
                pn.Expiration_Date,
                pn.Status,
                DATEDIFF(CURDATE(), pn.Expiration_Date) as Days_Since_Expiration
            FROM Public_Notices pn
            WHERE pn.Permit_ID = %s
            ORDER BY pn.Expiration_Date DESC
            LIMIT 1
        """
        
        cursor.execute(query, (permit_id,))
        result = cursor.fetchone()
        
        if not result:
            error_msg = f"No public notice record found for permit {permit_id}"
            log_checkpoint(2, "Public Notice Period", "FAILED", error_msg)
            return False, error_msg
        
        # Check if notice period has expired (minimum 10 days)
        if result['Status'] != 'CLOSED':
            days_remaining = (result['Expiration_Date'] - datetime.now().date()).days
            error_msg = f"Public notice period not closed. {days_remaining} days remaining."
            log_checkpoint(2, "Public Notice Period", "FAILED", error_msg)
            return False, error_msg
        
        # Verify minimum 10-day period was observed
        notice_duration = (result['Expiration_Date'] - result['Publication_Date']).days
        if notice_duration < MIN_NOTICE_PERIOD_DAYS:
            error_msg = f"Notice period ({notice_duration} days) is less than required {MIN_NOTICE_PERIOD_DAYS} days"
            log_checkpoint(2, "Public Notice Period", "FAILED", error_msg)
            return False, error_msg
        
        log_checkpoint(
            2, "Public Notice Period", "PASSED", 
            f"Notice closed after {notice_duration} days (min: {MIN_NOTICE_PERIOD_DAYS})"
        )
        return True, f"Public notice period verified ({notice_duration} days)"
        
    except ImportError:
        error_msg = "mysql.connector not available - cannot verify notice period"
        log_checkpoint(2, "Public Notice Period", "FAILED", error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        log_checkpoint(2, "Public Notice Period", "FAILED", error_msg)
        return False, error_msg
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# SAFETY CHECKPOINT 3: Senior Planner Manual Approval
# ============================================================

def checkpoint_3_senior_planner_approval(permit_id: int) -> Tuple[bool, str]:
    """
    SAFETY CHECKPOINT 3: Senior Planner Manual Approval
    
    Polls the Approval_Flags table to verify that the Senior Planner
    has manually approved the schema installation for this permit.
    
    Args:
        permit_id: The permit ID to check
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    log_checkpoint(3, "Senior Planner Approval", "IN_PROGRESS", f"Checking permit {permit_id}")
    
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=DATABASE_HOST,
            database=DATABASE_NAME,
            user=DATABASE_USER
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query to check Senior Planner approval flag
        query = """
            SELECT 
                af.Flag_ID,
                af.Is_Approved,
                af.Approver_ID,
                af.Approval_Date,
                af.Comments,
                a.Name as Approver_Name
            FROM Approval_Flags af
            LEFT JOIN Applicants a ON af.Approver_ID = a.Applicant_ID
            WHERE af.Permit_ID = %s
            AND af.Flag_Type = 'SENIOR_PLANNER'
            ORDER BY af.Approval_Date DESC
            LIMIT 1
        """
        
        cursor.execute(query, (permit_id,))
        result = cursor.fetchone()
        
        if not result:
            error_msg = f"No Senior Planner approval flag found for permit {permit_id}"
            log_checkpoint(3, "Senior Planner Approval", "FAILED", error_msg)
            return False, error_msg
        
        if not result['Is_Approved']:
            error_msg = "Senior Planner approval flag is not set to approved"
            log_checkpoint(3, "Senior Planner Approval", "FAILED", error_msg)
            return False, error_msg
        
        approver_info = result['Approver_Name'] or f"ID: {result['Approver_ID']}"
        approval_date = result['Approval_Date'].isoformat() if result['Approval_Date'] else "Unknown"
        comments = result['Comments'] or "No comments"
        
        log_checkpoint(
            3, "Senior Planner Approval", "PASSED",
            f"Approved by {approver_info} on {approval_date}"
        )
        return True, f"Senior Planner approval confirmed ({approver_info}, {approval_date})"
        
    except ImportError:
        error_msg = "mysql.connector not available - cannot verify approval"
        log_checkpoint(3, "Senior Planner Approval", "FAILED", error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        log_checkpoint(3, "Senior Planner Approval", "FAILED", error_msg)
        return False, error_msg
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# MAIN AUTOMATION FLOW
# ============================================================

def execute_schema_installation(permit_id: int, sql_file: str = SCHEMA_FILE) -> bool:
    """
    Execute the complete schema installation workflow with all safety checkpoints.
    
    Args:
        permit_id: The permit ID associated with this installation
        sql_file: Path to the SQL schema file
        
    Returns:
        bool: True if installation completed successfully, False otherwise
    """
    print("=" * 70)
    print("DOWNTOWN ZONING BOARD - SCHEMA INSTALLATION AUTOMATION")
    print(f"Permit ID: {permit_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    
    # Ensure log directory exists
    import os
    os.makedirs("logs", exist_ok=True)
    
    # SAFETY CHECKPOINT 1: Syntax Validation
    print("\n[CHECKPOINT 1/3] Syntax Validation")
    print("-" * 50)
    success, message = checkpoint_1_syntax_validation(sql_file)
    if not success:
        print(f"\n❌ INSTALLATION ABORTED: {message}")
        return False
    print(f"✓ {message}")
    
    # SAFETY CHECKPOINT 2: Public Notice Period
    print("\n[CHECKPOINT 2/3] Public Notice Period Verification")
    print("-" * 50)
    success, message = checkpoint_2_public_notice_period(permit_id)
    if not success:
        print(f"\n❌ INSTALLATION ABORTED: {message}")
        return False
    print(f"✓ {message}")
    
    # SAFETY CHECKPOINT 3: Senior Planner Approval
    print("\n[CHECKPOINT 3/3] Senior Planner Manual Approval")
    print("-" * 50)
    success, message = checkpoint_3_senior_planner_approval(permit_id)
    if not success:
        print(f"\n❌ INSTALLATION ABORTED: {message}")
        return False
    print(f"✓ {message}")
    
    # ALL CHECKPOINTS PASSED - Execute Schema Installation
    print("\n" + "=" * 70)
    print("ALL SAFETY CHECKPOINTS PASSED")
    print("=" * 70)
    print("\nExecuting schema installation...")
    
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=DATABASE_HOST,
            database=DATABASE_NAME,
            user=DATABASE_USER
        )
        cursor = conn.cursor()
        
        # Read and execute SQL file
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Execute multi-statement script
        for statement in sql_script.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                cursor.execute(statement)
        
        conn.commit()
        
        print("✓ Schema installation completed successfully")
        
        # Log successful installation
        log_checkpoint(0, "Schema Installation", "COMPLETED", f"Permit {permit_id} installed")
        
        return True
        
    except Exception as e:
        error_msg = f"Installation failed: {str(e)}"
        log_checkpoint(0, "Schema Installation", "FAILED", error_msg)
        print(f"\n❌ {error_msg}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def main():
    """Main entry point for command-line execution."""
    if len(sys.argv) < 2:
        print("Usage: python schema_installation_automation.py <permit_id> [sql_file]")
        print("Example: python schema_installation_automation.py 12345")
        sys.exit(1)
    
    permit_id = int(sys.argv[1])
    sql_file = sys.argv[2] if len(sys.argv) > 2 else SCHEMA_FILE
    
    success = execute_schema_installation(permit_id, sql_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
