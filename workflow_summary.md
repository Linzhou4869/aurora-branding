# Downtown Zoning Board Review - Workflow Configuration Summary

**Generated:** 2026-03-29  
**Project:** Downtown Zoning Board Review Materials  
**Status:** Configuration Complete

---

## Executive Summary

This document summarizes the configured workflow for the Downtown Zoning Board Review system, including database schema updates and automated schema installation with safety checkpoints.

---

## 1. Database Entity Relationship Diagram

### Location
`/mnt/afs_toolcall/zhoulin3/.openclaw/workspaces/gendata-worker-6/downtown_zoning_erd.md`

### Tables Configured

| Table Name | Purpose | Status |
|------------|---------|--------|
| `Applicants` | Stores applicant information | Existing |
| `Properties` | Property/lot records | Existing |
| `Zoning_Reviews` | Historical zoning review data | Existing |
| `Special_Use_Permits` | **NEW** Special use permit tracking | **Added** |
| `Public_Notices` | Public notice period tracking | Supporting |
| `Approval_Flags` | Multi-stage approval workflow | Supporting |

### New Table: Special_Use_Permits

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `Permit_ID` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique permit identifier |
| `Applicant_ID` | INT | FOREIGN KEY → Applicants | Reference to applicant |
| `Property_Lot_Number` | VARCHAR(20) | FOREIGN KEY → Properties | Reference to property lot |
| `Justification_Notes` | TEXT | NOT NULL | Detailed justification |
| `Submission_Date` | DATE | NOT NULL | Application submission date |
| `Status` | VARCHAR(50) | DEFAULT 'PENDING' | Permit status |

### Relationships

```
Applicants (1) ──────< Special_Use_Permits (>1)
Properties (1) ──────< Special_Use_Permits (>1)
Special_Use_Permits (1) ──────< Public_Notices (>1)
Special_Use_Permits (1) ──────< Approval_Flags (>1)
```

---

## 2. Schema Installation Automation Flow

### Location
`/mnt/afs_toolcall/zhoulin3/.openclaw/workspaces/gendata-worker-6/schema_installation_automation.py`

### Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCHEMA INSTALLATION WORKFLOW                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  START                                                           │
│    │                                                             │
│    ▼                                                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ CHECKPOINT 1: Syntax Validation                          │   │
│  │ • Parse SQL file for syntax errors                       │   │
│  │ • Validate required SQL constructs                       │   │
│  │ • Dry-run verification                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│    │                                                             │
│    ▼ PASS                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ CHECKPOINT 2: Public Notice Period                       │   │
│  │ • Query Public_Notices table                             │   │
│  │ • Verify 10-day minimum period closed                    │   │
│  │ • Check Status = 'CLOSED'                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│    │                                                             │
│    ▼ PASS                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ CHECKPOINT 3: Senior Planner Approval                    │   │
│  │ • Poll Approval_Flags table                              │   │
│  │ • Verify Flag_Type = 'SENIOR_PLANNER'                    │   │
│  │ • Confirm Is_Approved = TRUE                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│    │                                                             │
│    ▼ PASS                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ EXECUTE SCHEMA INSTALLATION                              │   │
│  │ • Run SQL script against database                        │   │
│  │ • Create tables and indexes                              │   │
│  │ • Log completion                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│    │                                                             │
│    ▼                                                             │
│  END                                                             │
│                                                                  │
│  [ANY CHECKPOINT FAILS → ABORT INSTALLATION]                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Safety Checkpoints Detail

### Checkpoint 1: Syntax Validation

| Attribute | Value |
|-----------|-------|
| **Purpose** | Prevent malformed SQL from executing |
| **Method** | SQL parsing and syntax verification |
| **Validation** | • File exists and readable<br>• Contains required SQL constructs<br>• Statements properly terminated |
| **Failure Action** | Abort installation, log error |
| **Log Entry** | `CHECKPOINT 1: Syntax Validation - PASSED/FAILED` |

### Checkpoint 2: Public Notice Period Verification

| Attribute | Value |
|-----------|-------|
| **Purpose** | Ensure legal compliance with 10-day public notice requirement |
| **Method** | Query `Public_Notices` table |
| **Validation** | • Notice record exists for permit<br>• Status = 'CLOSED'<br>• Duration ≥ 10 days |
| **Query** | `SELECT * FROM Public_Notices WHERE Permit_ID = ? ORDER BY Expiration_Date DESC LIMIT 1` |
| **Failure Action** | Abort installation, log remaining days |
| **Log Entry** | `CHECKPOINT 2: Public Notice Period - PASSED/FAILED` |

### Checkpoint 3: Senior Planner Manual Approval

| Attribute | Value |
|-----------|-------|
| **Purpose** | Ensure human oversight before schema changes |
| **Method** | Poll `Approval_Flags` table |
| **Validation** | • Approval flag exists<br>• Flag_Type = 'SENIOR_PLANNER'<br>• Is_Approved = TRUE |
| **Query** | `SELECT * FROM Approval_Flags WHERE Permit_ID = ? AND Flag_Type = 'SENIOR_PLANNER'` |
| **Failure Action** | Abort installation, notify planner |
| **Log Entry** | `CHECKPOINT 3: Senior Planner Approval - PASSED/FAILED` |

---

## 4. File Inventory

| File | Path | Purpose |
|------|------|---------|
| ERD Documentation | `downtown_zoning_erd.md` | Complete database schema with Mermaid diagram |
| SQL Schema | `schema_installation.sql` | Executable SQL for table creation |
| Automation Script | `schema_installation_automation.py` | Python workflow with safety checkpoints |
| Workflow Summary | `workflow_summary.md` | This document |

---

## 5. Usage Instructions

### Running the Automation

```bash
# Execute with permit ID
python3 schema_installation_automation.py <permit_id>

# Example
python3 schema_installation_automation.py 12345
```

### Manual SQL Installation (Bypass Automation)

```bash
mysql -h localhost -u zoning_admin -D downtown_zoning < schema_installation.sql
```

### Viewing Logs

```bash
# Real-time log monitoring
tail -f logs/schema_installation.log
```

---

## 6. Pending Items

### Video Processing

| Item | Status | Notes |
|------|--------|-------|
| Source File | ⚠️ **NOT FOUND** | `/shared_data/city_hall/videos/site_inspections_raw.mp4` does not exist |
| Action Required | User to provide correct path or upload file | |
| Target Output | Compressed video (~40% reduction, 1080p min) | Will use ffmpeg with H.264 encoding |

**Proposed ffmpeg command once file is located:**
```bash
ffmpeg -i site_inspections_raw.mp4 \
  -c:v libx264 -crf 23 \
  -vf "scale=-2:1080" \
  -c:a aac -b:a 128k \
  site_inspections_optimized.mp4
```

---

## 7. Approval Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Senior Planner | _________________ | _________ | __________ |
| IT Administrator | _________________ | _________ | __________ |
| Board Secretary | _________________ | _________ | __________ |

---

## 8. Contact Information

**Downtown Zoning Board**  
**Technical Support:** zoning-it@cityhall.gov  
**Documentation:** `/mnt/afs_toolcall/zhoulin3/.openclaw/workspaces/gendata-worker-6/`

---

*End of Workflow Configuration Summary*
