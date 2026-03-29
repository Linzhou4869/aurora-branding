# Purchase Order Approval Workflow

Automated workflow for high-value purchase order approvals with dual-signature requirements.

## Quick Start

### Threshold Trigger
- **Dual Signature Required:** PO amount > **$50,000**
- **Executive Approval Required:** PO amount > **$250,000**

### Running the Workflow

```bash
# Run the workflow engine
python3 workflows/po_approval_workflow.py

# Check workflow status
python3 -c "
from workflows.po_approval_workflow import POApprovalWorkflow
wf = POApprovalWorkflow()
print(wf.get_po_status('PO-2026-002'))
"
```

## Directory Structure

```
workflows/
├── README.md                              # This file
├── PO_APPROVAL_WORKFLOW_DESIGN.md         # Detailed workflow design document
├── po_approval_workflow.py                # Main workflow engine (Python)
├── config/
│   └── po_approval_config.json            # Workflow configuration
├── schema/
│   └── po_approval_schema.sql             # Database schema (MySQL/PostgreSQL)
├── templates/                             # Email notification templates
├── logs/                                  # Workflow execution logs
└── data/                                  # Runtime data (SQLite/JSON for testing)
    ├── purchase_orders.json
    ├── approval_signatures.json
    ├── notification_drafts.json
    └── approval_audit_log.json
```

## Approval Tiers

| Tier | Amount Range | Signatures | Approvers | SLA |
|------|--------------|------------|-----------|-----|
| 1 | ≤ $50,000 | 1 | Department Manager | 2 days |
| 2 | $50,001 - $250,000 | 2 | Dept Manager + Finance Director | 5 days |
| 3 | > $250,000 | 3 | Dept Manager + Finance Director + CFO | 7 days |

## Workflow States

```
DRAFT → PENDING_APPROVAL → WAITING_FIRST_SIG → WAITING_SECOND_SIG → APPROVED → RELEASED
                                                    ↓
                                               REJECTED
```

## Key Features

### Automatic Notification Drafts
When a PO exceeds $50,000, the workflow automatically:
1. Determines approval tier based on amount
2. Creates approval signature records for required approvers
3. Generates notification draft emails for first approver
4. Logs all actions to audit trail

### Dual-Signature Enforcement
- POs > $50,000 require **2 signatures** before release
- POs > $250,000 require **3 signatures** (including CFO)
- Second approver notified only after first approval
- Status cannot change to `RELEASED` until all signatures collected

### SLA Tracking
- Automatic reminders at 50% of SLA
- Escalation warnings at 75% of SLA
- Manager escalation at 100% of SLA
- Auto-delegation to backup at 150% of SLA

### Audit Trail
All events logged with:
- Timestamp
- User ID and role
- IP address
- Old/new values for state changes
- Metadata

## API Reference

### Submit PO for Approval

```python
from workflows.po_approval_workflow import POApprovalWorkflow

workflow = POApprovalWorkflow()

result = workflow.submit_po_for_approval(
    po_id='PO-2026-001',
    user_id='USER-001',
    ip_address='192.168.1.100'
)

# Result:
# {
#   'success': True,
#   'approval_tier': 'TIER_2',
#   'required_signatures': 2,
#   'requires_dual_signature': True,
#   'approvers': [...],
#   'notification_drafts': [...]
# }
```

### Process Approval

```python
result = workflow.approve_signature(
    signature_id='SIG-UUID',
    approver_id='IT-MGR-001',
    ip_address='192.168.1.100'
)

# Result:
# {
#   'success': True,
#   'signatures_complete': 1,
#   'signatures_required': 2,
#   'next_action': 'waiting_second_signature',
#   'notification_drafts': [...]
# }
```

### Process Rejection

```python
result = workflow.reject_signature(
    signature_id='SIG-UUID',
    approver_id='IT-MGR-001',
    reason='Budget exceeded for Q1',
    ip_address='192.168.1.100'
)
```

### Release Approved PO

```python
result = workflow.release_po(
    po_id='PO-2026-001',
    user_id='PROC-MGR-001',
    ip_address='192.168.1.100'
)
```

### Check Pending POs (Reminders/Escalations)

```python
result = workflow.check_pending_pos()

# Result:
# {
#   'pending_signatures': 6,
#   'reminders_created': 2,
#   'escalations_created': 1,
#   ...
# }
```

## Configuration

Edit `config/po_approval_config.json` to customize:

- Approval thresholds
- SLA durations
- Approver assignments
- Notification templates
- Escalation rules

## Database Setup

For production deployment:

```bash
# Run schema on MySQL/PostgreSQL
mysql -u user -p database < workflows/schema/po_approval_schema.sql
```

## Testing

```bash
# Run workflow with sample data
python3 workflows/po_approval_workflow.py

# Check generated notification drafts
cat workflows/data/notification_drafts.json | python3 -m json.tool

# Check approval signatures
cat workflows/data/approval_signatures.json | python3 -m json.tool

# Check audit log
cat workflows/data/approval_audit_log.json | python3 -m json.tool
```

## Integration

### Cron Job for SLA Monitoring

```bash
# Add to crontab - run every hour
0 * * * * cd /path/to/workspace && python3 -c "
from workflows.po_approval_workflow import POApprovalWorkflow
wf = POApprovalWorkflow()
result = wf.check_pending_pos()
print(f'Reminders: {result[\"reminders_created\"]}, Escalations: {result[\"escalations_created\"]}')
" >> workflows/logs/sla_monitor.log 2>&1
```

### Webhook Integration

```python
# Example: Flask endpoint for approval actions
from flask import Flask, request, jsonify
from workflows.po_approval_workflow import POApprovalWorkflow

app = Flask(__name__)
workflow = POApprovalWorkflow()

@app.route('/api/approve', methods=['POST'])
def approve():
    data = request.json
    result = workflow.approve_signature(
        signature_id=data['signature_id'],
        approver_id=data['approver_id'],
        ip_address=request.remote_addr
    )
    return jsonify(result)
```

## Troubleshooting

### PO Stuck in Approval
1. Check `workflows/data/approval_signatures.json` for pending signatures
2. Run `check_pending_pos()` to trigger escalations
3. Verify approver is active in `approvers` table

### Notification Not Sent
1. Check `workflows/data/notification_drafts.json` for draft creation
2. Verify email/SMS integration configuration
3. Check `workflows/logs/po_approval_workflow.log` for errors

### Audit Log Missing Entries
1. Verify database connection
2. Check `workflows/logs/po_approval_workflow.log` for errors
3. Ensure audit logging is enabled in config

## Support

For issues or questions:
- Workflow Admin: workflow-admin@[COMPANY].com
- Procurement: procurement@[COMPANY].com
- Finance: finance@[COMPANY].com

---

**Version:** 1.0  
**Effective Date:** 2026-04-01  
**Owner:** Procurement & Finance Department
