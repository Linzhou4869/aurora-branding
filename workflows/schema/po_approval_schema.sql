-- Purchase Order Approval Workflow Database Schema
-- Version: 1.0
-- Effective Date: 2026-04-01
-- Database: MySQL 8.0+ / PostgreSQL 14+

-- ============================================================================
-- PURCHASE ORDERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS purchase_orders (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
    vendor_id VARCHAR(36) NOT NULL COMMENT 'Reference to vendors table',
    amount DECIMAL(15, 2) NOT NULL COMMENT 'PO total amount',
    currency VARCHAR(3) DEFAULT 'USD' COMMENT 'ISO currency code',
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT' COMMENT 'PO status (enum: DRAFT, PENDING_APPROVAL, WAITING_FIRST_SIG, WAITING_SECOND_SIG, APPROVED, RELEASED, REJECTED, CANCELLED)',
    department VARCHAR(100) COMMENT 'Requesting department',
    creator_id VARCHAR(36) NOT NULL COMMENT 'User who created the PO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    submitted_at TIMESTAMP NULL COMMENT 'When submitted for approval',
    approved_at TIMESTAMP NULL COMMENT 'When fully approved',
    released_at TIMESTAMP NULL COMMENT 'When released to vendor',
    approval_tier INTEGER DEFAULT 1 COMMENT 'Approval tier (1=single, 2=dual, 3=executive)',
    required_signatures INTEGER DEFAULT 1 COMMENT 'Number of signatures required',
    current_signature_count INTEGER DEFAULT 0 COMMENT 'Number of signatures collected',
    metadata JSON COMMENT 'Additional PO metadata',

    INDEX idx_status (status),
    INDEX idx_vendor_id (vendor_id),
    INDEX idx_creator_id (creator_id),
    INDEX idx_amount (amount),
    INDEX idx_approval_tier (approval_tier),
    INDEX idx_submitted_at (submitted_at),

    CONSTRAINT chk_status CHECK (status IN ('DRAFT', 'PENDING_APPROVAL', 'WAITING_FIRST_SIG', 'WAITING_SECOND_SIG', 'APPROVED', 'RELEASED', 'REJECTED', 'CANCELLED')),
    CONSTRAINT chk_amount CHECK (amount >= 0),
    CONSTRAINT chk_tier CHECK (approval_tier IN (1, 2, 3)),
    CONSTRAINT chk_signatures CHECK (required_signatures >= 1 AND current_signature_count <= required_signatures)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Purchase orders with approval workflow tracking';


-- ============================================================================
-- APPROVAL SIGNATURES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS approval_signatures (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
    purchase_order_id VARCHAR(36) NOT NULL COMMENT 'Reference to purchase_orders',
    approver_id VARCHAR(36) NOT NULL COMMENT 'User ID of approver',
    approver_role VARCHAR(100) NOT NULL COMMENT 'Role of approver (department_manager, finance_director, cfo)',
    signature_order INTEGER NOT NULL COMMENT 'Order of this signature in workflow',
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' COMMENT 'Signature status (PENDING, COMPLETED, DELEGATED, REJECTED)',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When approval was requested',
    responded_at TIMESTAMP NULL COMMENT 'When approver responded',
    signature_data JSON COMMENT 'Signature metadata (IP, timestamp, etc.)',
    delegation_from VARCHAR(36) NULL COMMENT 'If delegated, original approver ID',
    rejection_reason TEXT NULL COMMENT 'If rejected, reason provided',

    INDEX idx_po_id (purchase_order_id),
    INDEX idx_approver_id (approver_id),
    INDEX idx_status (status),
    INDEX idx_signature_order (signature_order),
    INDEX idx_requested_at (requested_at),

    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,

    CONSTRAINT chk_sig_status CHECK (status IN ('PENDING', 'COMPLETED', 'DELEGATED', 'REJECTED')),
    CONSTRAINT chk_sig_order CHECK (signature_order >= 1),
    UNIQUE KEY uk_po_signature_order (purchase_order_id, signature_order) COMMENT 'One signature per order per PO'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Approval signatures for purchase order workflow';


-- ============================================================================
-- APPROVAL AUDIT LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS approval_audit_log (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
    purchase_order_id VARCHAR(36) NOT NULL COMMENT 'Reference to purchase_orders',
    event_type VARCHAR(100) NOT NULL COMMENT 'Type of event logged',
    user_id VARCHAR(36) NULL COMMENT 'User who triggered the event',
    user_role VARCHAR(100) NULL COMMENT 'Role of user',
    old_value TEXT NULL COMMENT 'Previous value (for state changes)',
    new_value TEXT NULL COMMENT 'New value (for state changes)',
    metadata JSON NULL COMMENT 'Additional event metadata',
    ip_address VARCHAR(45) NULL COMMENT 'IP address of user (IPv4/IPv6)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Event timestamp',

    INDEX idx_po_id (purchase_order_id),
    INDEX idx_event_type (event_type),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,

    CONSTRAINT chk_event_type CHECK (event_type IN (
        'po_created',
        'po_submitted_for_approval',
        'approval_requested',
        'signature_applied',
        'approval_delegated',
        'rejected',
        'status_changed',
        'escalation_triggered',
        'auto_delegate',
        'po_released',
        'notification_draft_created',
        'notification_sent'
    ))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Audit log for purchase order approval workflow';


-- ============================================================================
-- APPROVERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS approvers (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key (same as user_id)',
    user_id VARCHAR(36) NOT NULL UNIQUE COMMENT 'Reference to users table',
    name VARCHAR(200) NOT NULL COMMENT 'Full name of approver',
    email VARCHAR(255) NOT NULL COMMENT 'Email address',
    role VARCHAR(100) NOT NULL COMMENT 'Approval role',
    department VARCHAR(100) NULL COMMENT 'Department if role-specific',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether approver is active',
    is_backup BOOLEAN DEFAULT FALSE COMMENT 'Whether this is a backup approver',
    backup_for VARCHAR(36) NULL COMMENT 'If backup, primary approver ID',
    delegation_allowed BOOLEAN DEFAULT TRUE COMMENT 'Whether can delegate approvals',
    max_approval_amount DECIMAL(15, 2) NULL COMMENT 'Maximum amount this approver can approve',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_role (role),
    INDEX idx_department (department),
    INDEX idx_is_active (is_active),
    INDEX idx_backup_for (backup_for),

    FOREIGN KEY (backup_for) REFERENCES approvers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Configured approvers for workflow';


-- ============================================================================
-- NOTIFICATION DRAFTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_drafts (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
    template_id VARCHAR(100) NOT NULL COMMENT 'Notification template ID',
    recipient_ids JSON NOT NULL COMMENT 'Array of recipient user IDs',
    cc_ids JSON DEFAULT '[]' COMMENT 'Array of CC user IDs',
    subject VARCHAR(500) NOT NULL COMMENT 'Email subject',
    body TEXT NOT NULL COMMENT 'Email body (HTML or plain text)',
    channel VARCHAR(50) DEFAULT 'email' COMMENT 'Delivery channel (email, sms, in_app)',
    priority VARCHAR(20) DEFAULT 'normal' COMMENT 'Priority (low, normal, high, urgent)',
    po_id VARCHAR(36) NOT NULL COMMENT 'Related purchase order ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Draft creation timestamp',
    sent_at TIMESTAMP NULL COMMENT 'When notification was sent',
    metadata JSON NULL COMMENT 'Additional metadata',

    INDEX idx_po_id (po_id),
    INDEX idx_template_id (template_id),
    INDEX idx_channel (channel),
    INDEX idx_priority (priority),
    INDEX idx_sent_at (sent_at),

    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,

    CONSTRAINT chk_channel CHECK (channel IN ('email', 'sms', 'in_app', 'email_sms')),
    CONSTRAINT chk_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Notification drafts for approval workflow';


-- ============================================================================
-- NOTIFICATION SENT LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_sent_log (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
    notification_draft_id VARCHAR(36) NOT NULL COMMENT 'Reference to notification_drafts',
    recipient_id VARCHAR(36) NOT NULL COMMENT 'User who received notification',
    channel VARCHAR(50) NOT NULL COMMENT 'Channel used',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When sent',
    delivered_at TIMESTAMP NULL COMMENT 'When delivered',
    opened_at TIMESTAMP NULL COMMENT 'When opened (if tracked)',
    status VARCHAR(50) DEFAULT 'sent' COMMENT 'Delivery status',
    error_message TEXT NULL COMMENT 'Error if delivery failed',
    metadata JSON NULL COMMENT 'Provider-specific metadata',

    INDEX idx_draft_id (notification_draft_id),
    INDEX idx_recipient_id (recipient_id),
    INDEX idx_sent_at (sent_at),
    INDEX idx_status (status),

    FOREIGN KEY (notification_draft_id) REFERENCES notification_drafts(id) ON DELETE CASCADE,

    CONSTRAINT chk_sent_status CHECK (status IN ('pending', 'sent', 'delivered', 'opened', 'failed', 'bounced'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Log of sent notifications';


-- ============================================================================
-- WORKFLOW CONFIGURATION TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_config (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT 'Configuration key',
    config_value JSON NOT NULL COMMENT 'Configuration value',
    version VARCHAR(20) NOT NULL COMMENT 'Configuration version',
    effective_date DATE NOT NULL COMMENT 'When this config becomes effective',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether config is active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(36) NULL COMMENT 'User who created',
    updated_by VARCHAR(36) NULL COMMENT 'User who last updated',

    INDEX idx_config_key (config_key),
    INDEX idx_is_active (is_active),
    INDEX idx_effective_date (effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Workflow configuration settings';


-- ============================================================================
-- SLA TRACKING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sla_tracking (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
    purchase_order_id VARCHAR(36) NOT NULL COMMENT 'Reference to purchase_orders',
    signature_id VARCHAR(36) NOT NULL COMMENT 'Reference to approval_signatures',
    tier INTEGER NOT NULL COMMENT 'Approval tier',
    deadline TIMESTAMP NOT NULL COMMENT 'SLA deadline',
    reminder_sent_at TIMESTAMP NULL COMMENT 'When reminder was sent',
    escalation_sent_at TIMESTAMP NULL COMMENT 'When escalation was sent',
    auto_delegated_at TIMESTAMP NULL COMMENT 'When auto-delegated',
    is_breached BOOLEAN DEFAULT FALSE COMMENT 'Whether SLA was breached',
    breach_duration_seconds INTEGER NULL COMMENT 'Duration of breach if applicable',

    INDEX idx_po_id (purchase_order_id),
    INDEX idx_signature_id (signature_id),
    INDEX idx_deadline (deadline),
    INDEX idx_is_breached (is_breached),

    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (signature_id) REFERENCES approval_signatures(id) ON DELETE CASCADE,

    CONSTRAINT chk_tier CHECK (tier IN (1, 2, 3))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='SLA tracking for approval deadlines';


-- ============================================================================
-- INITIAL DATA: DEFAULT APPROVERS
-- ============================================================================

-- Department Managers
INSERT INTO approvers (id, user_id, name, email, role, department, is_backup, delegation_allowed) VALUES
    ('PROC-MGR-001', 'PROC-MGR-001', 'Jane Smith', 'jane.smith@company.com', 'department_manager', 'Procurement', FALSE, TRUE),
    ('OPS-MGR-001', 'OPS-MGR-001', 'John Doe', 'john.doe@company.com', 'department_manager', 'Operations', FALSE, TRUE),
    ('IT-MGR-001', 'IT-MGR-001', 'Alice Johnson', 'alice.johnson@company.com', 'department_manager', 'IT', FALSE, TRUE),
    ('MKT-MGR-001', 'MKT-MGR-001', 'Bob Williams', 'bob.williams@company.com', 'department_manager', 'Marketing', FALSE, TRUE),
    ('RD-MGR-001', 'RD-MGR-001', 'Carol Brown', 'carol.brown@company.com', 'department_manager', 'R&D', FALSE, TRUE);

-- Finance Directors
INSERT INTO approvers (id, user_id, name, email, role, is_backup, delegation_allowed) VALUES
    ('FINANCE-001', 'FINANCE-001', 'David Lee', 'david.lee@company.com', 'finance_director', FALSE, TRUE),
    ('FINANCE-002', 'FINANCE-002', 'Emma Wilson', 'emma.wilson@company.com', 'finance_director', TRUE, TRUE);

-- CFO
INSERT INTO approvers (id, user_id, name, email, role, is_backup, delegation_allowed, max_approval_amount) VALUES
    ('CFO-001', 'CFO-001', 'Frank Miller', 'frank.miller@company.com', 'cfo', FALSE, FALSE, NULL),
    ('CEO-001', 'CEO-001', 'Grace Chen', 'grace.chen@company.com', 'cfo', TRUE, FALSE, NULL);

-- Backup Approvers (Senior Team Leads)
INSERT INTO approvers (id, user_id, name, email, role, department, is_backup, backup_for, delegation_allowed) VALUES
    ('PROC-LEAD-001', 'PROC-LEAD-001', 'Henry Taylor', 'henry.taylor@company.com', 'senior_team_lead', 'Procurement', TRUE, 'PROC-MGR-001', FALSE),
    ('OPS-LEAD-001', 'OPS-LEAD-001', 'Ivy Martinez', 'ivy.martinez@company.com', 'senior_team_lead', 'Operations', TRUE, 'OPS-MGR-001', FALSE),
    ('IT-LEAD-001', 'IT-LEAD-001', 'Jack Anderson', 'jack.anderson@company.com', 'senior_team_lead', 'IT', TRUE, 'IT-MGR-001', FALSE),
    ('MKT-LEAD-001', 'MKT-LEAD-001', 'Kelly Thomas', 'kelly.thomas@company.com', 'senior_team_lead', 'Marketing', TRUE, 'MKT-MGR-001', FALSE),
    ('RD-LEAD-001', 'RD-LEAD-001', 'Leo Garcia', 'leo.garcia@company.com', 'senior_team_lead', 'R&D', TRUE, 'RD-MGR-001', FALSE);

-- Finance Manager (backup for Finance Director)
INSERT INTO approvers (id, user_id, name, email, role, is_backup, backup_for, delegation_allowed) VALUES
    ('FINANCE-MGR-001', 'FINANCE-MGR-001', 'Maria Rodriguez', 'maria.rodriguez@company.com', 'finance_manager', TRUE, 'FINANCE-001', FALSE);


-- ============================================================================
-- INITIAL DATA: WORKFLOW CONFIGURATION
-- ============================================================================

INSERT INTO workflow_config (id, config_key, config_value, version, effective_date, is_active) VALUES
    ('CONFIG-001', 'approval_thresholds', '{
        "tier_1_max": 50000,
        "tier_2_max": 250000,
        "tier_3_min": 250001
    }', '1.0', '2026-04-01', TRUE),
    ('CONFIG-002', 'sla_settings', '{
        "tier_1_days": 2,
        "tier_2_days": 5,
        "tier_3_days": 7,
        "business_hours_only": true,
        "timezone": "UTC"
    }', '1.0', '2026-04-01', TRUE),
    ('CONFIG-003', 'escalation_settings', '{
        "reminder_at_percentage": 50,
        "warning_at_percentage": 75,
        "escalate_at_percentage": 100,
        "auto_delegate_at_percentage": 150
    }', '1.0', '2026-04-01', TRUE);


-- ============================================================================
-- VIEWS FOR REPORTING
-- ============================================================================

-- Pending Approvals View
CREATE OR REPLACE VIEW v_pending_approvals AS
SELECT
    po.id AS po_id,
    po.vendor_id,
    po.amount,
    po.currency,
    po.department,
    po.creator_id,
    po.submitted_at,
    po.approval_tier,
    po.required_signatures,
    po.current_signature_count,
    s.id AS signature_id,
    s.approver_id,
    s.approver_role,
    s.signature_order,
    s.requested_at,
    TIMESTAMPDIFF(HOUR, s.requested_at, NOW()) AS hours_pending,
    CASE
        WHEN po.approval_tier = 1 THEN 48
        WHEN po.approval_tier = 2 THEN 48
        ELSE 48
    END AS sla_hours_first_sig,
    a.name AS approver_name,
    a.email AS approver_email
FROM purchase_orders po
JOIN approval_signatures s ON po.id = s.purchase_order_id
LEFT JOIN approvers a ON s.approver_id = a.id
WHERE po.status IN ('WAITING_FIRST_SIG', 'WAITING_SECOND_SIG')
  AND s.status = 'PENDING'
ORDER BY s.requested_at ASC;


-- Approval Dashboard View
CREATE OR REPLACE VIEW v_approval_dashboard AS
SELECT
    po.id AS po_id,
    po.vendor_id,
    po.amount,
    po.status,
    po.approval_tier,
    po.required_signatures,
    po.current_signature_count,
    po.submitted_at,
    po.approved_at,
    po.released_at,
    CASE
        WHEN po.status = 'RELEASED' THEN 'Complete'
        WHEN po.status = 'APPROVED' THEN 'Ready for Release'
        WHEN po.status = 'REJECTED' THEN 'Rejected'
        WHEN po.status = 'CANCELLED' THEN 'Cancelled'
        WHEN TIMESTAMPDIFF(HOUR, po.submitted_at, NOW()) >
            CASE po.approval_tier
                WHEN 1 THEN 48
                WHEN 2 THEN 120
                ELSE 168
            END THEN 'Overdue'
        ELSE 'On Track'
    END AS sla_status,
    GROUP_CONCAT(
        CONCAT(s.approver_role, ':', s.status)
        ORDER BY s.signature_order SEPARATOR ' | '
    ) AS signature_status
FROM purchase_orders po
LEFT JOIN approval_signatures s ON po.id = s.purchase_order_id
WHERE po.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
GROUP BY po.id
ORDER BY po.submitted_at DESC;


-- ============================================================================
-- STORED PROCEDURE: SUBMIT PO FOR APPROVAL
-- ============================================================================

DELIMITER //

CREATE PROCEDURE sp_submit_po_for_approval(
    IN p_po_id VARCHAR(36),
    IN p_user_id VARCHAR(36),
    IN p_ip_address VARCHAR(45),
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(500)
)
BEGIN
    DECLARE v_amount DECIMAL(15,2);
    DECLARE v_status VARCHAR(50);
    DECLARE v_tier INTEGER;
    DECLARE v_required_sigs INTEGER;
    DECLARE v_old_status VARCHAR(50);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_success = FALSE;
        SET p_message = 'Database error occurred';
        ROLLBACK;
    END;

    START TRANSACTION;

    -- Get PO details
    SELECT amount, status INTO v_amount, v_status
    FROM purchase_orders
    WHERE id = p_po_id;

    IF v_status IS NULL THEN
        SET p_success = FALSE;
        SET p_message = 'PO not found';
        ROLLBACK;
    ELSEIF v_status != 'DRAFT' THEN
        SET p_success = FALSE;
        SET p_message = CONCAT('PO is not in DRAFT status: ', v_status);
        ROLLBACK;
    ELSE
        -- Determine tier
        IF v_amount <= 50000 THEN
            SET v_tier = 1;
            SET v_required_sigs = 1;
        ELSEIF v_amount <= 250000 THEN
            SET v_tier = 2;
            SET v_required_sigs = 2;
        ELSE
            SET v_tier = 3;
            SET v_required_sigs = 3;
        END IF;

        SET v_old_status = v_status;

        -- Update PO
        UPDATE purchase_orders
        SET status = 'PENDING_APPROVAL',
            approval_tier = v_tier,
            required_signatures = v_required_sigs,
            submitted_at = NOW()
        WHERE id = p_po_id;

        -- Create audit log
        INSERT INTO approval_audit_log (id, purchase_order_id, event_type, user_id, old_value, new_value, ip_address)
        VALUES (UUID(), p_po_id, 'po_submitted_for_approval', p_user_id, v_old_status, 'PENDING_APPROVAL', p_ip_address);

        -- TODO: Create signature records based on department and tier

        SET p_success = TRUE;
        SET p_message = CONCAT('PO submitted. Tier: ', v_tier, ', Signatures required: ', v_required_sigs);

        COMMIT;
    END IF;
END //

DELIMITER ;


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update approval_tier when amount changes (for DRAFT POs)
CREATE TRIGGER trg_po_amount_update
BEFORE UPDATE ON purchase_orders
FOR EACH ROW
BEGIN
    IF NEW.status = 'DRAFT' AND OLD.amount != NEW.amount THEN
        IF NEW.amount <= 50000 THEN
            SET NEW.approval_tier = 1;
            SET NEW.required_signatures = 1;
        ELSEIF NEW.amount <= 250000 THEN
            SET NEW.approval_tier = 2;
            SET NEW.required_signatures = 2;
        ELSE
            SET NEW.approval_tier = 3;
            SET NEW.required_signatures = 3;
        END IF;
    END IF;
END;


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
