#!/usr/bin/env python3
"""
Purchase Order Approval Workflow Engine

Automated workflow for high-value purchase order approvals with dual-signature requirements.
Triggers notification drafts when PO amount exceeds $50,000 threshold.

Author: OpenClaw Workflow Engine
Version: 1.0
Effective Date: 2026-04-01
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflows/logs/po_approval_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('POApprovalWorkflow')


class POStatus(Enum):
    """Purchase Order Status States"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    WAITING_FIRST_SIG = "WAITING_FIRST_SIG"
    WAITING_SECOND_SIG = "WAITING_SECOND_SIG"
    APPROVED = "APPROVED"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ApprovalTier(Enum):
    """Approval Tiers based on PO Amount"""
    TIER_1 = 1  # ≤ $50,000
    TIER_2 = 2  # $50,001 - $250,000
    TIER_3 = 3  # > $250,001


class SignatureStatus(Enum):
    """Signature Status"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    DELEGATED = "DELEGATED"
    REJECTED = "REJECTED"


@dataclass
class PurchaseOrder:
    """Purchase Order Data Model"""
    id: str
    vendor_id: str
    amount: float
    currency: str = "USD"
    status: str = POStatus.DRAFT.value
    department: str = ""
    creator_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    submitted_at: Optional[str] = None
    approved_at: Optional[str] = None
    released_at: Optional[str] = None
    approval_tier: int = 1
    required_signatures: int = 1
    current_signature_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PurchaseOrder':
        return cls(**data)


@dataclass
class ApprovalSignature:
    """Approval Signature Data Model"""
    id: str
    purchase_order_id: str
    approver_id: str
    approver_role: str
    signature_order: int
    status: str = SignatureStatus.PENDING.value
    requested_at: str = ""
    responded_at: Optional[str] = None
    signature_data: Dict[str, Any] = field(default_factory=dict)
    delegation_from: Optional[str] = None
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationDraft:
    """Notification Draft Data Model"""
    id: str
    template_id: str
    recipient_ids: List[str]
    cc_ids: List[str]
    subject: str
    body: str
    channel: str
    priority: str
    po_id: str
    created_at: str = ""
    sent_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditLogEntry:
    """Audit Log Entry Data Model"""
    id: str
    purchase_order_id: str
    event_type: str
    user_id: Optional[str]
    user_role: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    created_at: str = ""


class WorkflowConfig:
    """Workflow Configuration Loader"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise

    def get_threshold_for_amount(self, amount: float) -> ApprovalTier:
        """Determine approval tier based on PO amount"""
        thresholds = self.config['thresholds']

        if amount <= thresholds['tier_1']['max_amount']:
            return ApprovalTier.TIER_1
        elif amount <= thresholds['tier_2']['max_amount']:
            return ApprovalTier.TIER_2
        else:
            return ApprovalTier.TIER_3

    def get_required_signatures(self, tier: ApprovalTier) -> int:
        """Get required signature count for tier"""
        tier_key = f'tier_{tier.value}'
        return self.config['thresholds'][tier_key]['required_signatures']

    def get_approver_roles(self, tier: ApprovalTier) -> List[str]:
        """Get approver roles for tier"""
        tier_key = f'tier_{tier.value}'
        return self.config['thresholds'][tier_key]['approver_roles']

    def get_sla_days(self, tier: ApprovalTier) -> int:
        """Get SLA in days for tier"""
        tier_key = f'tier_{tier.value}'
        return self.config['thresholds'][tier_key]['sla_days']

    def get_notification_template(self, template_id: str) -> Dict[str, Any]:
        """Get notification template configuration"""
        return self.config['notifications']['templates'].get(template_id, {})


class DatabaseSimulator:
    """
    Database Simulator for Workflow Engine
    
    In production, replace with actual database connections.
    This simulator uses JSON files for persistence during testing.
    """

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_table_path(self, table_name: str) -> Path:
        return self.data_dir / f"{table_name}.json"

    def _load_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Load table data from JSON file"""
        table_path = self._get_table_path(table_name)
        if not table_path.exists():
            return []
        with open(table_path, 'r') as f:
            return json.load(f)

    def _save_table(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """Save table data to JSON file"""
        table_path = self._get_table_path(table_name)
        with open(table_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def insert(self, table_name: str, record: Dict[str, Any]) -> str:
        """Insert record into table"""
        data = self._load_table(table_name)
        if 'id' not in record:
            record['id'] = str(uuid.uuid4())
        if 'created_at' not in record:
            record['created_at'] = datetime.utcnow().isoformat()
        data.append(record)
        self._save_table(table_name, data)
        logger.info(f"Inserted record into {table_name}: {record.get('id')}")
        return record['id']

    def update(self, table_name: str, record_id: str, updates: Dict[str, Any]) -> bool:
        """Update record in table"""
        data = self._load_table(table_name)
        for i, record in enumerate(data):
            if record.get('id') == record_id:
                data[i].update(updates)
                data[i]['updated_at'] = datetime.utcnow().isoformat()
                self._save_table(table_name, data)
                logger.info(f"Updated record in {table_name}: {record_id}")
                return True
        return False

    def query(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query records from table with optional filters"""
        data = self._load_table(table_name)
        if not filters:
            return data

        results = []
        for record in data:
            match = True
            for key, value in filters.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                results.append(record)
        return results

    def get_by_id(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Get single record by ID"""
        results = self.query(table_name, {'id': record_id})
        return results[0] if results else None


class NotificationGenerator:
    """Notification Draft Generator"""

    def __init__(self, config: WorkflowConfig, db: DatabaseSimulator):
        self.config = config
        self.db = db
        self.templates_dir = Path('workflows/templates')
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def _load_template(self, template_id: str) -> Dict[str, str]:
        """Load email template from file or use defaults"""
        template_path = self.templates_dir / f"{template_id}.json"

        default_templates = {
            'PO_APPROVAL_REQUEST': {
                'subject': 'Action Required: Purchase Order ${po_id} Approval (${amount})',
                'body': '''Dear ${approver_name},

A purchase order requires your approval.

PO Details:
- PO ID: ${po_id}
- Vendor: ${vendor_name}
- Amount: ${currency} ${amount}
- Department: ${department}
- Submitted By: ${creator_name}
- Submitted At: ${submitted_at}

Approval Required By: ${sla_deadline}

Please review and approve/reject at: ${approval_link}

This is an automated notification. Do not reply to this email.

---
Procurement Workflow System'''
            },
            'PO_APPROVAL_REMINDER': {
                'subject': 'Reminder: Purchase Order ${po_id} Approval Pending',
                'body': '''Dear ${approver_name},

This is a reminder that the following purchase order is still awaiting your approval:

- PO ID: ${po_id}
- Amount: ${currency} ${amount}
- Days Pending: ${days_pending}

Please review at your earliest convenience: ${approval_link}

---
Procurement Workflow System'''
            },
            'PO_APPROVAL_ESCALATION': {
                'subject': 'ESCALATION: Purchase Order ${po_id} Approval Overdue',
                'body': '''Dear ${approver_name},

ESCALATION NOTICE: The following purchase order approval is overdue.

- PO ID: ${po_id}
- Amount: ${currency} ${amount}
- Original Deadline: ${sla_deadline}
- Days Overdue: ${days_overdue}

This has been escalated to your manager.

Immediate action required: ${approval_link}

---
Procurement Workflow System'''
            },
            'PO_APPROVAL_COMPLETED': {
                'subject': 'Approved: Purchase Order ${po_id}',
                'body': '''Dear ${creator_name},

Your purchase order has been fully approved.

- PO ID: ${po_id}
- Vendor: ${vendor_name}
- Amount: ${currency} ${amount}
- Approved At: ${approved_at}
- Approved By: ${approvers}

The PO will be released to the vendor shortly.

---
Procurement Workflow System'''
            },
            'PO_REJECTED': {
                'subject': 'Rejected: Purchase Order ${po_id}',
                'body': '''Dear ${creator_name},

Your purchase order has been rejected.

- PO ID: ${po_id}
- Amount: ${currency} ${amount}
- Rejected By: ${rejector_name}
- Rejected At: ${rejected_at}
- Reason: ${rejection_reason}

Please revise and resubmit if needed.

---
Procurement Workflow System'''
            }
        }

        if template_path.exists():
            with open(template_path, 'r') as f:
                return json.load(f)
        return default_templates.get(template_id, {'subject': '', 'body': ''})

    def _render_template(self, template: Dict[str, str], variables: Dict[str, str]) -> Dict[str, str]:
        """Render template with variables"""
        rendered = {}
        for key, value in template.items():
            for var_name, var_value in variables.items():
                value = value.replace(f'${{{var_name}}}', str(var_value))
            rendered[key] = value
        return rendered

    def create_approval_request_draft(self, po: PurchaseOrder, approver_id: str,
                                       approver_name: str, signature_order: int) -> NotificationDraft:
        """Create approval request notification draft"""
        template = self._load_template('PO_APPROVAL_REQUEST')
        config_template = self.config.get_notification_template('PO_APPROVAL_REQUEST')

        tier = ApprovalTier(po.approval_tier)
        sla_deadline = (datetime.utcnow() + timedelta(days=self.config.get_sla_days(tier))).strftime('%Y-%m-%d')

        variables = {
            'po_id': po.id,
            'amount': f"${po.amount:,.2f}",
            'currency': po.currency,
            'vendor_name': po.metadata.get('vendor_name', po.vendor_id),
            'department': po.department,
            'creator_name': po.metadata.get('creator_name', po.creator_id),
            'submitted_at': po.submitted_at or po.created_at,
            'sla_deadline': sla_deadline,
            'approver_name': approver_name,
            'approval_link': f"https://procurement.[COMPANY].com/approve/{po.id}",
            'signature_order': signature_order
        }

        rendered = self._render_template(template, variables)

        draft = NotificationDraft(
            id=str(uuid.uuid4()),
            template_id='PO_APPROVAL_REQUEST',
            recipient_ids=[approver_id],
            cc_ids=[],
            subject=rendered['subject'],
            body=rendered['body'],
            channel=config_template.get('channel', 'email'),
            priority=config_template.get('priority', 'high'),
            po_id=po.id,
            created_at=datetime.utcnow().isoformat(),
            metadata={
                'signature_order': signature_order,
                'approval_tier': po.approval_tier,
                'sla_deadline': sla_deadline
            }
        )

        return draft

    def create_completion_notification_draft(self, po: PurchaseOrder,
                                              approvers: List[Dict[str, Any]]) -> NotificationDraft:
        """Create approval completion notification draft"""
        template = self._load_template('PO_APPROVAL_COMPLETED')
        config_template = self.config.get_notification_template('PO_APPROVAL_COMPLETED')

        approver_names = ', '.join([a.get('approver_name', a['approver_id']) for a in approvers])

        variables = {
            'po_id': po.id,
            'amount': f"${po.amount:,.2f}",
            'currency': po.currency,
            'vendor_name': po.metadata.get('vendor_name', po.vendor_id),
            'approved_at': po.approved_at or datetime.utcnow().isoformat(),
            'approvers': approver_names,
            'creator_name': po.metadata.get('creator_name', po.creator_id)
        }

        rendered = self._render_template(template, variables)

        draft = NotificationDraft(
            id=str(uuid.uuid4()),
            template_id='PO_APPROVAL_COMPLETED',
            recipient_ids=[po.creator_id],
            cc_ids=['finance@[COMPANY].com'],
            subject=rendered['subject'],
            body=rendered['body'],
            channel=config_template.get('channel', 'email'),
            priority=config_template.get('priority', 'normal'),
            po_id=po.id,
            created_at=datetime.utcnow().isoformat()
        )

        return draft

    def create_rejection_notification_draft(self, po: PurchaseOrder,
                                             rejector_id: str, rejector_name: str,
                                             reason: str) -> NotificationDraft:
        """Create rejection notification draft"""
        template = self._load_template('PO_REJECTED')
        config_template = self.config.get_notification_template('PO_REJECTED')

        variables = {
            'po_id': po.id,
            'amount': f"${po.amount:,.2f}",
            'currency': po.currency,
            'rejector_name': rejector_name,
            'rejected_at': datetime.utcnow().isoformat(),
            'rejection_reason': reason,
            'creator_name': po.metadata.get('creator_name', po.creator_id)
        }

        rendered = self._render_template(template, variables)

        draft = NotificationDraft(
            id=str(uuid.uuid4()),
            template_id='PO_REJECTED',
            recipient_ids=[po.creator_id],
            cc_ids=[po.metadata.get('department_manager_id', '')],
            subject=rendered['subject'],
            body=rendered['body'],
            channel=config_template.get('channel', 'email'),
            priority=config_template.get('priority', 'high'),
            po_id=po.id,
            created_at=datetime.utcnow().isoformat()
        )

        return draft

    def save_draft(self, draft: NotificationDraft) -> str:
        """Save notification draft to database"""
        return self.db.insert('notification_drafts', draft.to_dict())


class POApprovalWorkflow:
    """
    Main Purchase Order Approval Workflow Engine

    Monitors purchase orders, triggers approval workflows for high-value POs,
    manages signature collection, and generates notification drafts.
    """

    THRESHOLD_AMOUNT = 50000.00  # Dual signature threshold

    def __init__(self, config_path: str = 'workflows/config/po_approval_config.json',
                 data_dir: str = 'workflows/data'):
        self.config = WorkflowConfig(config_path)
        self.db = DatabaseSimulator(data_dir)
        self.notifications = NotificationGenerator(self.config, self.db)
        logger.info("PO Approval Workflow Engine initialized")

    def _create_audit_log(self, po_id: str, event_type: str, user_id: Optional[str] = None,
                          user_role: Optional[str] = None, old_value: Optional[str] = None,
                          new_value: Optional[str] = None, metadata: Optional[Dict] = None,
                          ip_address: Optional[str] = None) -> str:
        """Create audit log entry"""
        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            purchase_order_id=po_id,
            event_type=event_type,
            user_id=user_id,
            user_role=user_role,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata or {},
            ip_address=ip_address,
            created_at=datetime.utcnow().isoformat()
        )
        return self.db.insert('approval_audit_log', asdict(entry))

    def _determine_approval_tier(self, amount: float) -> ApprovalTier:
        """Determine approval tier based on amount"""
        return self.config.get_threshold_for_amount(amount)

    def _get_approvers_for_po(self, po: PurchaseOrder) -> List[Dict[str, str]]:
        """Get list of approvers for PO based on tier and department"""
        tier = ApprovalTier(po.approval_tier)
        roles = self.config.get_approver_roles(tier)

        approvers = []
        approver_config = self.config.config['approvers']['roles']

        for order, role in enumerate(roles, 1):
            role_config = approver_config.get(role, {})
            default_approvers = role_config.get('default_approvers', {})

            # Get approver based on department or default
            approver_id = default_approvers.get(po.department.lower(),
                                                 default_approvers.get('default', f'{role.upper()}-001'))

            approvers.append({
                'approver_id': approver_id,
                'approver_role': role,
                'signature_order': order,
                'approver_name': role_config.get('title', role)
            })

        return approvers

    def submit_po_for_approval(self, po_id: str, user_id: str,
                                ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a purchase order for approval workflow

        Returns workflow initiation result with notification drafts created
        """
        logger.info(f"Submitting PO {po_id} for approval")

        # Get PO from database
        po_data = self.db.get_by_id('purchase_orders', po_id)
        if not po_data:
            return {'success': False, 'error': 'PO not found'}

        po = PurchaseOrder.from_dict(po_data)

        # Validate PO is in DRAFT status
        if po.status != POStatus.DRAFT.value:
            return {'success': False, 'error': f'PO is not in DRAFT status: {po.status}'}

        # Determine approval tier
        tier = self._determine_approval_tier(po.amount)
        required_signatures = self.config.get_required_signatures(tier)

        # Check if dual signature required (amount > $50,000)
        requires_dual_signature = po.amount > self.THRESHOLD_AMOUNT

        # Update PO status and tier
        old_status = po.status
        po.status = POStatus.PENDING_APPROVAL.value
        po.approval_tier = tier.value
        po.required_signatures = required_signatures
        po.submitted_at = datetime.utcnow().isoformat()

        self.db.update('purchase_orders', po_id, {
            'status': po.status,
            'approval_tier': po.approval_tier,
            'required_signatures': po.required_signatures,
            'submitted_at': po.submitted_at
        })

        # Create audit log
        self._create_audit_log(
            po_id=po_id,
            event_type='po_submitted_for_approval',
            user_id=user_id,
            old_value=old_status,
            new_value=po.status,
            metadata={
                'amount': po.amount,
                'tier': tier.name,
                'requires_dual_signature': requires_dual_signature
            },
            ip_address=ip_address
        )

        # Get approvers
        approvers = self._get_approvers_for_po(po)

        # Create approval signature records
        notification_drafts = []
        for approver in approvers:
            signature = ApprovalSignature(
                id=str(uuid.uuid4()),
                purchase_order_id=po_id,
                approver_id=approver['approver_id'],
                approver_role=approver['approver_role'],
                signature_order=approver['signature_order'],
                status=SignatureStatus.PENDING.value,
                requested_at=datetime.utcnow().isoformat()
            )
            self.db.insert('approval_signatures', signature.to_dict())

            # Create notification draft for first approver only (others notified as workflow progresses)
            if approver['signature_order'] == 1:
                draft = self.notifications.create_approval_request_draft(
                    po=po,
                    approver_id=approver['approver_id'],
                    approver_name=approver['approver_name'],
                    signature_order=1
                )
                draft_id = self.notifications.save_draft(draft)
                notification_drafts.append({
                    'draft_id': draft_id,
                    'recipient': approver['approver_id'],
                    'type': 'approval_request'
                })

                # Log notification draft creation
                self._create_audit_log(
                    po_id=po_id,
                    event_type='notification_draft_created',
                    user_id='SYSTEM',
                    metadata={
                        'draft_id': draft_id,
                        'template': 'PO_APPROVAL_REQUEST',
                        'recipient': approver['approver_id']
                    }
                )

        # Update PO to waiting first signature
        po.status = POStatus.WAITING_FIRST_SIG.value
        self.db.update('purchase_orders', po_id, {'status': po.status})

        logger.info(f"PO {po_id} submitted for approval. Tier: {tier.name}, "
                    f"Signatures required: {required_signatures}, Dual signature: {requires_dual_signature}")

        return {
            'success': True,
            'po_id': po_id,
            'approval_tier': tier.name,
            'required_signatures': required_signatures,
            'requires_dual_signature': requires_dual_signature,
            'approvers': approvers,
            'notification_drafts': notification_drafts
        }

    def approve_signature(self, signature_id: str, approver_id: str,
                          ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Process an approval signature

        Returns result with next steps and any new notification drafts
        """
        logger.info(f"Processing approval for signature {signature_id} by {approver_id}")

        # Get signature record
        sig_data = self.db.get_by_id('approval_signatures', signature_id)
        if not sig_data:
            return {'success': False, 'error': 'Signature record not found'}

        signature = ApprovalSignature(**sig_data)

        # Validate approver
        if signature.approver_id != approver_id:
            return {'success': False, 'error': 'Unauthorized approver'}

        # Validate status
        if signature.status != SignatureStatus.PENDING.value:
            return {'success': False, 'error': f'Signature already completed: {signature.status}'}

        # Get PO
        po_data = self.db.get_by_id('purchase_orders', signature.purchase_order_id)
        if not po_data:
            return {'success': False, 'error': 'PO not found'}

        po = PurchaseOrder.from_dict(po_data)

        # Update signature
        signature.status = SignatureStatus.COMPLETED.value
        signature.responded_at = datetime.utcnow().isoformat()
        signature.signature_data = {
            'approved': True,
            'ip_address': ip_address,
            'timestamp': signature.responded_at
        }

        self.db.update('approval_signatures', signature_id, {
            'status': signature.status,
            'responded_at': signature.responded_at,
            'signature_data': json.dumps(signature.signature_data)
        })

        # Create audit log
        self._create_audit_log(
            po_id=po.id,
            event_type='signature_applied',
            user_id=approver_id,
            user_role=signature.approver_role,
            metadata={
                'signature_id': signature_id,
                'signature_order': signature.signature_order
            },
            ip_address=ip_address
        )

        # Update PO signature count
        po.current_signature_count += 1

        notification_drafts = []
        next_action = None

        # Check if all signatures complete
        if po.current_signature_count >= po.required_signatures:
            # All signatures complete - mark as approved
            po.status = POStatus.APPROVED.value
            po.approved_at = datetime.utcnow().isoformat()
            next_action = 'ready_for_release'

            # Get all approvers for completion notification
            all_signatures = self.db.query('approval_signatures',
                                            {'purchase_order_id': po.id})
            approvers = []
            for sig in all_signatures:
                if sig['status'] == SignatureStatus.COMPLETED.value:
                    approvers.append({
                        'approver_id': sig['approver_id'],
                        'approver_name': sig['approver_role']
                    })

            # Create completion notification draft
            draft = self.notifications.create_completion_notification_draft(po, approvers)
            draft_id = self.notifications.save_draft(draft)
            notification_drafts.append({
                'draft_id': draft_id,
                'recipient': po.creator_id,
                'type': 'approval_completed'
            })

            logger.info(f"PO {po.id} fully approved. Ready for release.")
        else:
            # More signatures needed
            if signature.signature_order == 1:
                po.status = POStatus.WAITING_SECOND_SIG.value
                next_action = 'waiting_second_signature'

                # Get next approver and create notification
                next_sig_data = self.db.query('approval_signatures', {
                    'purchase_order_id': po.id,
                    'signature_order': signature.signature_order + 1
                })

                if next_sig_data:
                    next_sig = ApprovalSignature(**next_sig_data[0])
                    approver_config = self.config.config['approvers']['roles'].get(next_sig.approver_role, {})

                    draft = self.notifications.create_approval_request_draft(
                        po=po,
                        approver_id=next_sig.approver_id,
                        approver_name=approver_config.get('title', next_sig.approver_role),
                        signature_order=next_sig.signature_order
                    )
                    draft_id = self.notifications.save_draft(draft)
                    notification_drafts.append({
                        'draft_id': draft_id,
                        'recipient': next_sig.approver_id,
                        'type': 'approval_request'
                    })

            logger.info(f"PO {po.id} signature {signature.signature_order} complete. "
                        f"Waiting for {po.required_signatures - po.current_signature_count} more.")

        # Update PO
        self.db.update('purchase_orders', po.id, {
            'status': po.status,
            'current_signature_count': po.current_signature_count,
            'approved_at': po.approved_at
        })

        return {
            'success': True,
            'signature_id': signature_id,
            'po_id': po.id,
            'signatures_complete': po.current_signature_count,
            'signatures_required': po.required_signatures,
            'next_action': next_action,
            'notification_drafts': notification_drafts
        }

    def reject_signature(self, signature_id: str, approver_id: str,
                         reason: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a rejection

        Returns result with notification drafts created
        """
        logger.info(f"Processing rejection for signature {signature_id} by {approver_id}")

        # Get signature record
        sig_data = self.db.get_by_id('approval_signatures', signature_id)
        if not sig_data:
            return {'success': False, 'error': 'Signature record not found'}

        signature = ApprovalSignature(**sig_data)

        # Validate approver
        if signature.approver_id != approver_id:
            return {'success': False, 'error': 'Unauthorized approver'}

        # Get PO
        po_data = self.db.get_by_id('purchase_orders', signature.purchase_order_id)
        if not po_data:
            return {'success': False, 'error': 'PO not found'}

        po = PurchaseOrder.from_dict(po_data)

        # Update signature
        signature.status = SignatureStatus.REJECTED.value
        signature.responded_at = datetime.utcnow().isoformat()
        signature.rejection_reason = reason

        self.db.update('approval_signatures', signature_id, {
            'status': signature.status,
            'responded_at': signature.responded_at,
            'rejection_reason': reason
        })

        # Update PO status
        old_status = po.status
        po.status = POStatus.REJECTED.value

        self.db.update('purchase_orders', po.id, {
            'status': po.status
        })

        # Create audit log
        self._create_audit_log(
            po_id=po.id,
            event_type='po_rejected',
            user_id=approver_id,
            user_role=signature.approver_role,
            old_value=old_status,
            new_value=po.status,
            metadata={'rejection_reason': reason},
            ip_address=ip_address
        )

        # Create rejection notification draft
        approver_config = self.config.config['approvers']['roles'].get(signature.approver_role, {})
        draft = self.notifications.create_rejection_notification_draft(
            po=po,
            rejector_id=approver_id,
            rejector_name=approver_config.get('title', signature.approver_role),
            reason=reason
        )
        draft_id = self.notifications.save_draft(draft)

        logger.info(f"PO {po.id} rejected by {approver_id}. Reason: {reason}")

        return {
            'success': True,
            'signature_id': signature_id,
            'po_id': po.id,
            'status': po.status,
            'notification_drafts': [{
                'draft_id': draft_id,
                'recipient': po.creator_id,
                'type': 'rejection'
            }]
        }

    def release_po(self, po_id: str, user_id: str,
                   ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Release an approved PO to vendor
        """
        logger.info(f"Releasing PO {po_id}")

        # Get PO
        po_data = self.db.get_by_id('purchase_orders', po_id)
        if not po_data:
            return {'success': False, 'error': 'PO not found'}

        po = PurchaseOrder.from_dict(po_data)

        # Validate status
        if po.status != POStatus.APPROVED.value:
            return {'success': False, 'error': f'PO not approved. Current status: {po.status}'}

        # Update status
        old_status = po.status
        po.status = POStatus.RELEASED.value
        po.released_at = datetime.utcnow().isoformat()

        self.db.update('purchase_orders', po_id, {
            'status': po.status,
            'released_at': po.released_at
        })

        # Create audit log
        self._create_audit_log(
            po_id=po_id,
            event_type='po_released',
            user_id=user_id,
            old_value=old_status,
            new_value=po.status,
            ip_address=ip_address
        )

        logger.info(f"PO {po_id} released to vendor")

        return {
            'success': True,
            'po_id': po_id,
            'status': po.status,
            'released_at': po.released_at
        }

    def check_pending_pos(self) -> Dict[str, Any]:
        """
        Check for POs pending approval and generate reminder/escalation drafts
        """
        logger.info("Checking for pending POs requiring reminders/escalations")

        # Get all pending signatures
        pending_sigs = self.db.query('approval_signatures',
                                      {'status': SignatureStatus.PENDING.value})

        reminders = []
        escalations = []
        now = datetime.utcnow()

        for sig in pending_sigs:
            # Filter out database fields not in ApprovalSignature dataclass
            sig_data = {k: v for k, v in sig.items() if k in ['id', 'purchase_order_id', 'approver_id', 
                          'approver_role', 'signature_order', 'status', 'requested_at', 
                          'responded_at', 'signature_data', 'delegation_from', 'rejection_reason']}
            signature = ApprovalSignature(**sig_data)
            requested_at = datetime.fromisoformat(signature.requested_at.replace('Z', '+00:00').replace('+00:00', ''))

            # Get PO details
            po_data = self.db.get_by_id('purchase_orders', signature.purchase_order_id)
            if not po_data:
                continue

            po = PurchaseOrder.from_dict(po_data)
            tier = ApprovalTier(po.approval_tier)
            sla_days = self.config.get_sla_days(tier)

            elapsed = now - requested_at
            elapsed_days = elapsed.total_seconds() / 86400

            # Check escalation thresholds
            escalation_config = self.config.config['notifications']['escalation']

            if elapsed_days >= sla_days * (escalation_config['escalate_at_sla_percentage'] / 100):
                # Create escalation draft
                escalations.append({
                    'po_id': po.id,
                    'signature_id': signature.id,
                    'approver_id': signature.approver_id,
                    'days_overdue': elapsed_days - sla_days
                })
            elif elapsed_days >= sla_days * (escalation_config['reminder_at_sla_percentage'] / 100):
                # Create reminder draft
                reminders.append({
                    'po_id': po.id,
                    'signature_id': signature.id,
                    'approver_id': signature.approver_id,
                    'days_pending': elapsed_days
                })

        return {
            'checked_at': now.isoformat(),
            'pending_signatures': len(pending_sigs),
            'reminders_created': len(reminders),
            'escalations_created': len(escalations),
            'reminders': reminders,
            'escalations': escalations
        }

    def get_po_status(self, po_id: str) -> Dict[str, Any]:
        """Get detailed status of a PO"""
        po_data = self.db.get_by_id('purchase_orders', po_id)
        if not po_data:
            return {'error': 'PO not found'}

        po = PurchaseOrder.from_dict(po_data)
        signatures = self.db.query('approval_signatures', {'purchase_order_id': po_id})

        return {
            'po': po.to_dict(),
            'signatures': signatures,
            'approval_progress': f"{po.current_signature_count}/{po.required_signatures}"
        }


def main():
    """Main entry point for workflow engine"""
    print("=" * 70)
    print("Purchase Order Approval Workflow Engine")
    print("=" * 70)
    print(f"Threshold for Dual Signature: ${POApprovalWorkflow.THRESHOLD_AMOUNT:,.2f}")
    print()

    # Initialize workflow engine
    workflow = POApprovalWorkflow()

    # Demo: Create sample purchase orders
    print("Creating sample purchase orders...")
    print()

    # Sample POs
    sample_pos = [
        {'id': 'PO-2026-001', 'vendor_id': 'VND-001', 'amount': 25000.00, 'department': 'IT', 'creator_id': 'USER-001'},
        {'id': 'PO-2026-002', 'vendor_id': 'VND-002', 'amount': 75000.00, 'department': 'Operations', 'creator_id': 'USER-002'},
        {'id': 'PO-2026-003', 'vendor_id': 'VND-003', 'amount': 300000.00, 'department': 'Procurement', 'creator_id': 'USER-003'},
    ]

    for po_data in sample_pos:
        # Insert PO into database
        po_data['status'] = POStatus.DRAFT.value
        po_data['created_at'] = datetime.utcnow().isoformat()
        workflow.db.insert('purchase_orders', po_data)
        print(f"Created PO: {po_data['id']} - Amount: ${po_data['amount']:,.2f}")

    print()
    print("-" * 70)
    print("Submitting POs for approval...")
    print("-" * 70)

    for po_data in sample_pos:
        print(f"\nProcessing {po_data['id']} (${po_data['amount']:,.2f}):")

        result = workflow.submit_po_for_approval(po_data['id'], 'SYSTEM')

        if result['success']:
            print(f"  ✓ Approval Tier: {result['approval_tier']}")
            print(f"  ✓ Signatures Required: {result['required_signatures']}")
            print(f"  ✓ Dual Signature Required: {result['requires_dual_signature']}")
            print(f"  ✓ Approvers: {[a['approver_role'] for a in result['approvers']]}")

            if result['notification_drafts']:
                print(f"  ✓ Notification Drafts Created: {len(result['notification_drafts'])}")
                for draft in result['notification_drafts']:
                    print(f"    - {draft['type']}: {draft['recipient']}")
        else:
            print(f"  ✗ Error: {result['error']}")

    print()
    print("-" * 70)
    print("Checking pending POs...")
    print("-" * 70)

    status = workflow.check_pending_pos()
    print(f"Pending Signatures: {status['pending_signatures']}")
    print(f"Reminders: {status['reminders_created']}")
    print(f"Escalations: {status['escalations_created']}")

    print()
    print("=" * 70)
    print("Workflow engine demo complete!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("1. Review notification drafts in: workflows/data/notification_drafts.json")
    print("2. Process approvals using: approve_signature(signature_id, approver_id)")
    print("3. Monitor audit logs in: workflows/data/approval_audit_log.json")
    print()


if __name__ == '__main__':
    main()
