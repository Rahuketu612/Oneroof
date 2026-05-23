"""
Workflow automation engine for OneRoof.
Auto-generates compliance tasks, sends reminders, and manages deadlines.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_

from oneroof.core.database import AsyncSessionLocal
from oneroof.api.models import (
    Client, Workspace, ComplianceTemplate, ComplianceItem,
    DocumentRequest, Notification, ComplianceItem, ClientUser
)
from oneroof.audit.logging import AuditLogger


class ComplianceWorkflowEngine:
    """Engine for managing compliance workflows and automation."""
    
    # Default reminder schedule (days before due)
    DEFAULT_REMINDER_DAYS = {
        "gst": [-7, -3, -1, 0],
        "tds": [-10, -5, -2, 0],
        "roc": [-30, -15, -7, 0],
        "income_tax": [-30, -15, -7, 0],
    }
    
    @staticmethod
    async def generate_monthly_compliance(
        client_id: int,
        period: str,  # e.g., "May 2026"
        current_date: datetime = None
    ) -> List[ComplianceItem]:
        """Generate compliance items for a client based on their compliance types."""
        if current_date is None:
            current_date = datetime.utcnow()
        
        async with AsyncSessionLocal() as db:
            # Get client and workspace
            result = await db.execute(
                select(Client).where(Client.id == client_id)
            )
            client = result.scalar_one_or_none()
            
            if not client:
                return []
            
            result = await db.execute(
                select(Workspace).where(Workspace.client_id == client_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                return []
            
            generated_items = []
            compliance_types = client.compliance_types or {}
            
            # Get templates for each compliance type
            for compliance_type, enabled in compliance_types.items():
                if not enabled:
                    continue
                
                result = await db.execute(
                    select(ComplianceTemplate)
                    .where(
                        ComplianceTemplate.firm_id == client.firm_id,
                        ComplianceTemplate.compliance_type == compliance_type,
                        ComplianceTemplate.is_active == True
                    )
                )
                templates = result.scalars().all()
                
                for template in templates:
                    item = await ComplianceWorkflowEngine._create_compliance_item(
                        db, workspace.id, template, period, current_date
                    )
                    generated_items.append(item)
            
            await db.commit()
            return generated_items
    
    @staticmethod
    async def _create_compliance_item(db, workspace_id, template, period, current_date) -> ComplianceItem:
        """Create a single compliance item from template."""
        # Calculate due date based on frequency
        due_date = ComplianceWorkflowEngine._calculate_due_date(
            template.frequency, current_date
        )
        
        # Get default assigned user (first staff member)
        # For now, leave as null
        assigned_user_id = None
        
        item = ComplianceItem(
            workspace_id=workspace_id,
            template_id=template.id,
            name=f"{template.name} - {period}",
            compliance_type=template.compliance_type,
            period=period,
            status="pending",
            priority="normal",
            due_date=due_date,
            assigned_to_user_id=assigned_user_id,
            workflow_steps=template.workflow_steps or ComplianceWorkflowEngine._get_default_workflow_steps(template.compliance_type),
            is_recurring=True,
            recurrence_pattern=template.frequency,
        )
        db.add(item)
        
        # Flush to get item ID
        await db.flush()
        
        # Create document requests from template
        required_docs = template.required_documents or []
        reminder_days = template.reminder_days or ComplianceWorkflowEngine.DEFAULT_REMINDER_DAYS.get(
            template.compliance_type, [-5, -2, 0]
        )
        
        for doc_name in required_docs:
            request = DocumentRequest(
                compliance_item_id=item.id,
                title=doc_name,
                description=f"Required document: {doc_name}",
                status="pending",
                due_date=due_date,
            )
            db.add(request)
        
        # Log the creation
        await AuditLogger.log(
            action="compliance_create",
            resource_type="compliance",
            resource_id=item.id,
            workspace_id=workspace_id,
            details={
                "compliance_type": template.compliance_type,
                "period": period,
                "due_date": due_date.isoformat()
            },
            db=db
        )
        
        return item
    
    @staticmethod
    def _calculate_due_date(frequency: str, from_date: datetime) -> datetime:
        """Calculate next due date based on frequency."""
        if frequency == "monthly":
            # Due on 20th of next month
            if from_date.month == 12:
                return from_date.replace(year=from_date.year + 1, month=1, day=20)
            else:
                return from_date.replace(month=from_date.month + 1, day=20)
        elif frequency == "quarterly":
            # Due 20th of last month of quarter
            month = ((from_date.month - 1) // 3 + 1) * 3
            year = from_date.year if month <= 12 else from_date.year + 1
            month = month if month <= 12 else 1
            return from_date.replace(year=year, month=month, day=20)
        elif frequency == "yearly":
            # Due September 30th
            return from_date.replace(month=9, day=30)
        else:
            return from_date + timedelta(days=30)
    
    @staticmethod
    def _get_default_workflow_steps(compliance_type: str) -> List[dict]:
        """Get default workflow steps for compliance type."""
        base_steps = [
            {"step": 1, "name": "Document Collection", "roles": ["staff"], "action": "Request and collect documents from client"},
            {"step": 2, "name": "Document Review", "roles": ["staff"], "action": "Review submitted documents for completeness"},
            {"step": 3, "name": "Working Papers", "roles": ["staff"], "action": "Prepare working papers and reconciliations"},
            {"step": 4, "name": "Manager Review", "roles": ["manager"], "action": "Verify calculations and check anomalies"},
            {"step": 5, "name": "Client Approval", "roles": ["client_admin"], "action": "Client reviews and approves the filing"},
            {"step": 6, "name": "Filing", "roles": ["staff"], "action": "Submit filing and upload acknowledgment"},
        ]
        
        # GST-specific steps
        if compliance_type == "gst":
            gst_steps = [
                {"step": 1, "name": "GSTR-1 Data Collection", "roles": ["staff"], "action": "Collect sales register and e-way bills"},
                {"step": 2, "name": "GSTR-3B Preparation", "roles": ["staff"], "action": "Prepare GSTR-3B from sales data"},
                {"step": 3, "name": "Reconciliation", "roles": ["staff"], "action": "Reconcile GSTR-1 with GSTR-3B"},
                {"step": 4, "name": "Payment Calculation", "roles": ["manager"], "action": "Calculate tax liability and cash flow"},
                {"step": 5, "name": "Client Approval", "roles": ["client_admin"], "action": "Client approves tax payment and filing"},
                {"step": 6, "name": "Payment & Filing", "roles": ["staff"], "action": "Make payment and file return"},
            ]
            return gst_steps
        
        # TDS-specific steps
        if compliance_type == "tds":
            tds_steps = [
                {"step": 1, "name": "Deduction Data Collection", "roles": ["staff"], "action": "Collect payment and deduction data"},
                {"step": 2, "name": "TDS Calculation", "roles": ["staff"], "action": "Calculate TDS on each payment"},
                {"step": 3, "name": "Quarterly Filing Prep", "roles": ["staff"], "action": "Prepare Form 27Q/26Q"},
                {"step": 4, "name": "Challan Verification", "roles": ["manager"], "action": "Verify challan payments"},
                {"step": 5, "name": "Client Approval", "roles": ["client_admin"], "action": "Client approves filing"},
                {"step": 6, "name": "e-Filing", "roles": ["staff"], "action": "Upload and file TDS return"},
            ]
            return tds_steps
        
        return base_steps


class ReminderEngine:
    """Engine for generating and sending compliance reminders."""
    
    @staticmethod
    async def generate_reminders() -> int:
        """Generate reminders for upcoming deadlines."""
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            reminder_count = 0
            
            # Get all pending compliance items
            result = await db.execute(
                select(ComplianceItem)
                .where(ComplianceItem.status.in_(["pending", "in_progress"]))
            )
            items = result.scalars().all()
            
            for item in items:
                days_until_due = (item.due_date - now).days
                
                # Check if reminder should be sent
                reminder_days = [-7, -3, -1, 0]
                
                if days_until_due in reminder_days:
                    # Create notification for assigned staff
                    if item.assigned_to_user_id:
                        notification = Notification(
                            user_id=item.assigned_to_user_id,
                            notification_type="reminder",
                            title=f"Deadline Reminder: {item.name}",
                            message=f"Due in {days_until_due} days - {item.due_date.strftime('%d %b %Y')}",
                            link=f"/compliance/{item.id}",
                        )
                        db.add(notification)
                        reminder_count += 1
                    
                    # Create notification for client
                    result = await db.execute(
                        select(Workspace).where(Workspace.id == item.workspace_id)
                    )
                    workspace = result.scalar_one_or_none()
                    if workspace:
                        result = await db.execute(
                            select(ClientUser)
                            .where(ClientUser.client_id == workspace.client_id, ClientUser.role == "client_admin")
                        )
                        client_admin = result.scalar_one_or_none()
                        if client_admin:
                            notification = Notification(
                                client_user_id=client_admin.id,
                                notification_type="reminder",
                                title=f"Action Required: {item.name}",
                                message=f"Filing due in {days_until_due} days. Please upload required documents.",
                                link=f"/workspace/{workspace.id}/compliance/{item.id}",
                            )
                            db.add(notification)
                            reminder_count += 1
            
            await db.commit()
            return reminder_count
    
    @staticmethod
    async def escalate_overdue_items() -> int:
        """Escalate overdue items to managers and partners."""
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            escalation_count = 0
            
            # Find overdue items
            result = await db.execute(
                select(ComplianceItem)
                .where(
                    ComplianceItem.due_date < now,
                    ComplianceItem.status.in_(["pending", "in_progress"]),
                )
            )
            items = result.scalars().all()
            
            for item in items:
                days_overdue = (now - item.due_date).days
                
                # Only escalate if overdue by 2+ days
                if days_overdue >= 2:
                    # Notify assigned user's manager
                    # For now, just log it
                    await AuditLogger.log(
                        action="compliance_escalation",
                        resource_type="compliance",
                        resource_id=item.id,
                        workspace_id=item.workspace_id,
                        details={
                            "days_overdue": days_overdue,
                            "escalation_type": "overdue_notification"
                        },
                        db=db
                    )
                    escalation_count += 1
            
            await db.commit()
            return escalation_count


class ComplianceCalendar:
    """Calendar view for compliance deadlines."""
    
    @staticmethod
    async def get_monthly_calendar(
        year: int,
        month: int,
        firm_id: int
    ) -> List[dict]:
        """Get compliance items for a month."""
        async with AsyncSessionLocal() as db:
            from datetime import date
            start_date = datetime(year, month, 1)
            
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            result = await db.execute(
                select(ComplianceItem, Client.name)
                .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
                .join(Client, Workspace.client_id == Client.id)
                .where(
                    Client.firm_id == firm_id,
                    ComplianceItem.due_date >= start_date,
                    ComplianceItem.due_date < end_date,
                )
            )
            rows = result.all()
            
            calendar_items = []
            for item, client_name in rows:
                calendar_items.append({
                    "id": item.id,
                    "name": item.name,
                    "client": client_name,
                    "compliance_type": item.compliance_type,
                    "due_date": item.due_date.strftime("%Y-%m-%d"),
                    "due_day": item.due_date.day,
                    "status": item.status,
                    "priority": item.priority,
                    "period": item.period,
                })
            
            return calendar_items
    
    @staticmethod
    async def get_upcoming_deadlines(
        firm_id: int,
        days: int = 30
    ) -> List[dict]:
        """Get upcoming deadlines for the next N days."""
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            end_date = now + timedelta(days=days)
            
            result = await db.execute(
                select(ComplianceItem, Client.name)
                .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
                .join(Client, Workspace.client_id == Client.id)
                .where(
                    Client.firm_id == firm_id,
                    ComplianceItem.due_date >= now,
                    ComplianceItem.due_date <= end_date,
                    ComplianceItem.status.in_(["pending", "in_progress"]),
                )
                .order_by(ComplianceItem.due_date)
            )
            rows = result.all()
            
            deadlines = []
            for item, client_name in rows:
                days_until = (item.due_date - now).days
                deadlines.append({
                    "id": item.id,
                    "name": item.name,
                    "client": client_name,
                    "due_date": item.due_date.strftime("%Y-%m-%d"),
                    "days_until": days_until,
                    "status": item.status,
                    "urgency": "overdue" if days_until < 0 else "today" if days_until == 0 else "soon" if days_until <= 3 else "normal",
                })
            
            return deadlines