-- Downtown Zoning Board Database Schema
-- Special_Use_Permits Table Installation Script
-- Generated: 2026-03-29

-- ============================================================
-- SCHEMA INSTALLATION SCRIPT
-- ============================================================

-- Create Special_Use_Permits table
CREATE TABLE IF NOT EXISTS Special_Use_Permits (
    Permit_ID INT PRIMARY KEY AUTO_INCREMENT,
    Applicant_ID INT NOT NULL,
    Property_Lot_Number VARCHAR(20) NOT NULL,
    Justification_Notes TEXT NOT NULL,
    Submission_Date DATE NOT NULL,
    Status VARCHAR(50) DEFAULT 'PENDING',
    
    -- Foreign key constraints
    CONSTRAINT fk_sup_applicant 
        FOREIGN KEY (Applicant_ID) 
        REFERENCES Applicants(Applicant_ID)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_sup_property 
        FOREIGN KEY (Property_Lot_Number) 
        REFERENCES Properties(Property_Lot_Number)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    
    -- Check constraint for valid status values
    CONSTRAINT chk_sup_status 
        CHECK (Status IN ('PENDING', 'UNDER_REVIEW', 'APPROVED', 'DENIED', 'WITHDRAWN'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_permits_applicant ON Special_Use_Permits(Applicant_ID);
CREATE INDEX IF NOT EXISTS idx_permits_property ON Special_Use_Permits(Property_Lot_Number);
CREATE INDEX IF NOT EXISTS idx_permits_status ON Special_Use_Permits(Status);
CREATE INDEX IF NOT EXISTS idx_permits_submission ON Special_Use_Permits(Submission_Date);

-- Create Public_Notices table (supporting table for safety checkpoint 2)
CREATE TABLE IF NOT EXISTS Public_Notices (
    Notice_ID INT PRIMARY KEY AUTO_INCREMENT,
    Permit_ID INT NOT NULL,
    Publication_Date DATE NOT NULL,
    Expiration_Date DATE NOT NULL,
    Status VARCHAR(50) DEFAULT 'ACTIVE',
    Notice_Content VARCHAR(500),
    
    CONSTRAINT fk_pn_permit 
        FOREIGN KEY (Permit_ID) 
        REFERENCES Special_Use_Permits(Permit_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT chk_pn_status 
        CHECK (Status IN ('ACTIVE', 'EXPIRED', 'CLOSED'))
);

CREATE INDEX IF NOT EXISTS idx_notices_permit ON Public_Notices(Permit_ID);
CREATE INDEX IF NOT EXISTS idx_notices_status ON Public_Notices(Status);

-- Create Approval_Flags table (supporting table for safety checkpoint 3)
CREATE TABLE IF NOT EXISTS Approval_Flags (
    Flag_ID INT PRIMARY KEY AUTO_INCREMENT,
    Permit_ID INT NOT NULL,
    Flag_Type VARCHAR(50) NOT NULL,
    Is_Approved BOOLEAN DEFAULT FALSE,
    Approver_ID INT,
    Approval_Date DATE,
    Comments VARCHAR(500),
    
    CONSTRAINT fk_af_permit 
        FOREIGN KEY (Permit_ID) 
        REFERENCES Special_Use_Permits(Permit_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT chk_af_type 
        CHECK (Flag_Type IN ('SENIOR_PLANNER', 'BOARD_REVIEW', 'LEGAL_REVIEW', 'FINAL_APPROVAL'))
);

CREATE INDEX IF NOT EXISTS idx_flags_permit ON Approval_Flags(Permit_ID);
CREATE INDEX IF NOT EXISTS idx_flags_approved ON Approval_Flags(Is_Approved);

-- ============================================================
-- END OF SCHEMA INSTALLATION SCRIPT
-- ============================================================
