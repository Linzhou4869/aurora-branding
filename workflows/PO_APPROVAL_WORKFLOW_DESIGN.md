# Purchase Order Approval Workflow Configuration

**Document ID:** PO-WF-CONFIG-001  
**Version:** 1.0  
**Effective Date:** 2026-04-01  
**Owner:** Procurement & Finance Department

---

## Workflow Overview

Automated approval workflow for purchase orders exceeding defined thresholds, ensuring proper financial controls and dual-signature requirements.

---

## Threshold Configuration

### Approval Tiers

| Tier | Amount Range | Signatures Required | Approver Roles | SLA |
|------|--------------|---------------------|----------------|-----|
| **Tier 1** | $0 - $50,000 | 1 | Department Manager | 2 business days |
| **Tier 2** | $50,001 - $250,000 | 2 | Department Manager + Finance Director | 3 business days |
| **Tier 3** | $250,001+ | 3 | Department Manager + Finance Director + CFO | 5 business days |

### Threshold Values

```json
{
  "thresholds": {
    "single_signature_max": 50000,
    "dual_signature_min": 50001,
    "dual_signature_max": 250000,
    "executive_approval_min": 250001
  }
}
```

---

## Approver Configuration

### Role-Based Approvers

| Role | Default Approvers | Backup Approvers | Delegation Allowed |
|------|-------------------|------------------|-------------------|
| Department Manager | [CONFIGURED PER DEPT] | Senior Team Lead | Yes, to Senior Team Lead |
| Finance Director | [FINANCE-001] | [FINANCE-002] | Yes, to Finance Manager |
| CFO | [CFO-001] | [CEO-001] | No |

### Department Mappings

| Department | Department Manager | Backup |
|------------|-------------------|--------|
| Procurement | [PROC-MGR-001] | [PROC-LEAD-001] |
| Operations | [OPS-MGR-001] | [OPS-LEAD-001] |
| IT | [IT-MGR-001] | [IT-LEAD-001] |
| Marketing | [MKT-MGR-001] | [MKT-LEAD-001] |
| R&D | [RD-MGR-001] | [RD-LEAD-001] |

---

## Workflow States

### State Machine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PURCHASE ORDER APPROVAL STATE MACHINE                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐    create     ┌──────────────┐    auto-approve          │
│   │  DRAFT   │ ────────────> │ PENDING_     │ ──────────────>         │
│   └──────────┘               │ APPROVAL     │     (if ≤ $50K)         │
│                              └──────────────┘                          │
│                                    │                                    │
│                          amount > $50K │                                │
│                                    ▼                                    │
│                              ┌──────────────┐                          │
│                          ┌─> │ WAITING_     │                          │
│                          │   │ FIRST_SIG    │                          │
│                          │   └──────────────┘                          │
│                          │         │                                    │
│                          │   signature_1 │                              │
│                          │         ▼                                    │
│                          │   ┌──────────────┐                          │
│                          │   │ WAITING_     │                          │
│                          │   │ SECOND_SIG   │                          │
│                          │   └──────────────┘                          │
│                          │         │                                    │
│                          │   signature_2 │                              │
│                          │         ▼                                    │
│                          │   ┌──────────────┐                          │
│                          └── │   APPROVED   │ <─────────┐              │
│                              └──────────────┘          │              │
│                                    │                    │              │
│                              release │                  │              │
│                                    ▼                    │              │
│                              ┌──────────────┐          │              │
│                              │   RELEASED   │          │              │
│                              └──────────────┘          │              │
│                                    ▲                    │              │
│                                    │                    │              │
│                              ┌──────────────┐          │              │
│                          ┌── │   REJECTED   │ <────────┘              │
│                          │   └──────────────┘   reject at any         │
│                          │                      signature step        │
│                          │                                            │
│                          └────────────────────────────────────┐        │
│                                                               │        │
│                              ┌──────────────┐                │        │
│                              │   CANCELLED  │ <──────────────┘        │
│                              └──────────────┘   creator cancels       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### State Definitions

| State | Description | Allowed Actions |
|-------|-------------|-----------------|
| `DRAFT` | PO being prepared | submit, cancel |
| `PENDING_APPROVAL` | Awaiting workflow assignment | auto-assign |
| `WAITING_FIRST_SIG` | First approver reviewing | approve, reject, delegate |
| `WAITING_SECOND_SIG` | Second approver reviewing | approve, reject, delegate |
| `APPROVED` | All signatures obtained | release |
| `RELEASED` | PO sent to vendor | (terminal) |
| `REJECTED` | Approval denied | revise, cancel |
| `CANCELLED` | PO cancelled by creator | (terminal) |

---

## Notification Configuration

### Notification Channels

| Event | Primary Channel | Backup Channel | Escalation |
|-------|-----------------|----------------|------------|
| Approval Request | Email | In-app notification | SMS (after 24h) |
| Approval Reminder | Email | In-app notification | SMS (after 48h) |
| Approval Escalation | Email + SMS | Phone call | Manager notification |
| Approval Completed | Email | In-app notification | None |
| Rejection | Email | In-app notification | None |

### Email Templates

| Template ID | Trigger | Recipients |
|-------------|---------|------------|
| `PO_APPROVAL_REQUEST` | New approval needed | Assigned approver |
| `PO_APPROVAL_REMINDER` | SLA approaching deadline | Assigned approver |
| `PO_APPROVAL_ESCALATION` | SLA exceeded | Assigned approver + Manager |
| `PO_APPROVAL_COMPLETED` | All signatures obtained | PO creator, Finance |
| `PO_REJECTED` | Approval denied | PO creator, Department Manager |

---

## SLA Configuration

### Response Time Requirements

| Tier | First Signature SLA | Second Signature SLA | Total SLA |
|------|--------------------|---------------------|-----------|
| Tier 1 (≤$50K) | 2 business days | N/A | 2 business days |
| Tier 2 ($50K-$250K) | 2 business days | 3 business days | 5 business days |
| Tier 3 (>$250K) | 2 business days | 3 business days | 7 business days |

### Escalation Rules

| Time Elapsed | Action |
|--------------|--------|
| 50% of SLA | Send reminder notification |
| 75% of SLA | Send escalation warning |
| 100% of SLA | Escalate to approver's manager |
| 125% of SLA | Escalate to department head |
| 150% of SLA | Auto-delegate to backup approver |

---

## Audit Trail Requirements

### Logged Events

| Event | Data Captured |
|-------|---------------|
| PO Created | PO ID, creator, amount, vendor, timestamp |
| Approval Requested | PO ID, approver, tier, timestamp |
| Signature Applied | PO ID, approver, signature order, timestamp, IP address |
| Approval Delegated | PO ID, original approver, delegate, reason, timestamp |
| Rejected | PO ID, approver, reason, timestamp |
| Status Changed | PO ID, old status, new status, timestamp, user |

### Retention Policy

- Active POs: Full audit trail retained
- Completed POs: 7 years (SOX compliance)
- Rejected/Cancelled POs: 3 years

---

## Database Schema

### purchase_orders Table

```sql
CREATE TABLE purchase_orders (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    department VARCHAR(100),
    creator_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP NULL,
    approved_at TIMESTAMP NULL,
    released_at TIMESTAMP NULL,
    approval_tier INTEGER DEFAULT 1,
    required_signatures INTEGER DEFAULT 1,
    current_signature_count INTEGER DEFAULT 0,
    metadata JSON
);
```

### approval_signatures Table

```sql
CREATE TABLE approval_signatures (
    id VARCHAR(36) PRIMARY KEY,
    purchase_order_id VARCHAR(36) NOT NULL,
    approver_id VARCHAR(36) NOT NULL,
    approver_role VARCHAR(100) NOT NULL,
    signature_order INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP NULL,
    signature_data JSON,
    delegation_from VARCHAR(36) NULL,
    rejection_reason TEXT NULL,
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id)
);
```

### approval_audit_log Table

```sql
CREATE TABLE approval_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    purchase_order_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(36),
    user_role VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    metadata JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id)
);
```

---

## Configuration File

See `workflows/config/po_approval_config.json` for machine-readable configuration.

---

## Error Handling

### Error Scenarios

| Error | Handling |
|-------|----------|
| Approver unavailable | Delegate to backup approver |
| System timeout | Retry with exponential backoff (max 3 attempts) |
| Database error | Log error, queue for retry, alert admin |
| Invalid PO data | Reject submission, notify creator |
| Duplicate signature | Ignore duplicate, log warning |

### Alert Configuration

| Severity | Condition | Recipients |
|----------|-----------|------------|
| Critical | System down > 1 hour | IT Ops, Finance Director |
| High | PO stuck in approval > SLA + 50% | Department Manager |
| Medium | Backup approver used | Finance, Procurement |
| Low | Reminder sent | (logged only) |

---

## Testing Requirements

### Test Scenarios

| Test Case | Expected Result |
|-----------|-----------------|
| PO = $49,999 | Single signature, auto-routed to Dept Manager |
| PO = $50,001 | Dual signature, routed to Dept Manager + Finance |
| PO = $250,001 | Triple signature, routed to Dept Manager + Finance + CFO |
| First approval | Status changes to WAITING_SECOND_SIG |
| Second approval | Status changes to APPROVED |
| Rejection at any step | Status changes to REJECTED |
| SLA exceeded | Escalation triggered |

---

**Document Control:**

| Field | Value |
|-------|-------|
| Document ID | PO-WF-CONFIG-001 |
| Version | 1.0 |
| Effective Date | 2026-04-01 |
| Owner | Procurement & Finance Department |
| Next Review | 2026-10-01 |

---

*For configuration changes, submit request to: workflow-admin@[COMPANY].com*
