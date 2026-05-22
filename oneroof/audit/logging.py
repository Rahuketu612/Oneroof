"""
Audit logging system - immutable tracking of all actions.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_, or_

from oneroof.core.database import AsyncSessionLocal
from oneroof.api.models import AuditLog, Workspace, Client


class AuditLogger:
    """Service for creating immutable audit logs."""
    
    # Action types
    ACTIONS = {
        # Authentication
        "login": "User login",
        "logout": "User logout",
        "login_failed": "Failed login attempt",
        
        # Document operations
        "upload": "Document uploaded",
        "download": "Document downloaded",
        "delete": "Document deleted",
        "view": "Document viewed",
        
        # Compliance operations
        "compliance_create": "Compliance item created",
        "compliance_update": "Compliance item updated",
        "compliance_status_change": "Compliance status changed",
        "compliance_complete": "Compliance marked as filed",
        
        # Approval operations
        "approval_request": "Approval requested",
        "approval_approve": "Approval given",
        "approval_reject": "Approval rejected",
        "approval_override": "Approval overridden",
        
        # Communication
        "send_message": "Message sent",
        "read_message": "Message read",
        
        # Workspace operations
        "workspace_create": "Workspace created",
        "workspace_freeze": "Workspace frozen",
        "workspace_archive": "Workspace archived",
        
        # Notice operations
        "notice_create": "Notice created",
        "notice_update": "Notice updated",
        "notice_submit": "Notice response submitted",
        
        # User management
        "user_create": "User created",
        "user_update": "User updated",
        "user_deactivate": "User deactivated",
        "client_user_invite": "Client user invited",
        
        # System
        "export": "Data exported",
        "settings_change": "Settings changed",
    }
    
    @staticmethod
    async def log(
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        client_user_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
        db: Optional[AsyncSessionLocal] = None
    ):
        """Create an audit log entry."""
        if db is None:
            async with AsyncSessionLocal() as session:
                return await AuditLogger._create_log(
                    action, resource_type, resource_id,
                    user_id, client_user_id, workspace_id,
                    ip_address, user_agent, details, session
                )
        else:
            return await AuditLogger._create_log(
                action, resource_type, resource_id,
                user_id, client_user_id, workspace_id,
                ip_address, user_agent, details, db
            )
    
    @staticmethod
    async def _create_log(
        action: str,
        resource_type: str,
        resource_id: Optional[int],
        user_id: Optional[int],
        client_user_id: Optional[int],
        workspace_id: Optional[int],
        ip_address: Optional[str],
        user_agent: Optional[str],
        details: Optional[dict],
        db
    ):
        """Internal method to create log entry."""
        audit_entry = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            client_user_id=client_user_id,
            workspace_id=workspace_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        await db.commit()
        return audit_entry
    
    @staticmethod
    async def get_logs(
        workspace_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Query audit logs with filters."""
        async with AsyncSessionLocal() as db:
            query = select(AuditLog)
            
            filters = []
            if workspace_id:
                filters.append(AuditLog.workspace_id == workspace_id)
            if user_id:
                filters.append(or_(AuditLog.user_id == user_id, AuditLog.client_user_id == user_id))
            if action:
                filters.append(AuditLog.action == action)
            if resource_type:
                filters.append(AuditLog.resource_type == resource_type)
            if start_date:
                filters.append(AuditLog.timestamp >= start_date)
            if end_date:
                filters.append(AuditLog.timestamp <= end_date)
            
            if filters:
                query = query.where(and_(*filters))
            
            query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
    
    @staticmethod
    async def get_workspace_timeline(
        workspace_id: int,
        limit: int = 100
    ) -> List[dict]:
        """Get comprehensive timeline for a workspace."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AuditLog)
                .where(AuditLog.workspace_id == workspace_id)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
            )
            logs = result.scalars().all()
            
            return [
                {
                    "id": log.id,
                    "timestamp": log.timestamp,
                    "action": log.action,
                    "action_description": AuditLogger.ACTIONS.get(log.action, log.action),
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "user_id": log.user_id,
                    "client_user_id": log.client_user_id,
                    "ip_address": log.ip_address,
                    "details": log.details
                }
                for log in logs
            ]
    
    @staticmethod
    async def export_logs(
        workspace_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Export audit logs for compliance/retention."""
        async with AsyncSessionLocal() as db:
            query = select(AuditLog).where(AuditLog.workspace_id == workspace_id)
            
            if start_date:
                query = query.where(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.where(AuditLog.timestamp <= end_date)
            
            query = query.order_by(AuditLog.timestamp)
            result = await db.execute(query)
            logs = result.scalars().all()
            
            return [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "user_id": log.user_id,
                    "client_user_id": log.client_user_id,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "details": log.details
                }
                for log in logs
            ]


class ComplianceTimeline:
    """Service for building compliance timeline view."""
    
    @staticmethod
    async def get_compliance_history(
        compliance_item_id: int
    ) -> List[dict]:
        """Get complete history for a compliance item."""
        async with AsyncSessionLocal() as db:
            # Get compliance item
            result = await db.execute(
                select(ComplianceItem)
                .where(ComplianceItem.id == compliance_item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return []
            
            # Get audit logs for this compliance item
            audit_result = await db.execute(
                select(AuditLog)
                .where(
                    AuditLog.resource_type == "compliance",
                    AuditLog.resource_id == compliance_item_id
                )
                .order_by(AuditLog.timestamp)
            )
            audit_logs = audit_result.scalars().all()
            
            # Get approvals
            approval_result = await db.execute(
                select(Approval).where(Approval.compliance_item_id == compliance_item_id)
            )
            approvals = approval_result.scalars().all()
            
            # Get documents uploaded
            doc_result = await db.execute(
                select(Document)
                .where(Document.compliance_item_id == compliance_item_id)
                .order_by(Document.created_at)
            )
            documents = doc_result.scalars().all()
            
            # Get communications
            comm_result = await db.execute(
                select(Communication)
                .where(Communication.compliance_item_id == compliance_item_id)
                .order_by(Communication.created_at)
            )
            communications = comm_result.scalars().all()
            
            # Build timeline
            timeline = []
            
            for log in audit_logs:
                timeline.append({
                    "type": "audit",
                    "timestamp": log.timestamp,
                    "action": log.action,
                    "details": log.details
                })
            
            for approval in approvals:
                timeline.append({
                    "type": "approval",
                    "timestamp": approval.approved_at or approval.created_at,
                    "status": approval.status,
                    "approved_by": approval.approved_by_user_id or approval.approved_by_client_user_id,
                    "comments": approval.comments,
                    "ip_address": approval.ip_address
                })
            
            for doc in documents:
                timeline.append({
                    "type": "document",
                    "timestamp": doc.created_at,
                    "action": "upload",
                    "document_name": doc.name,
                    "version": doc.version,
                    "uploaded_by": doc.uploaded_by_user_id or doc.uploaded_by_client_user_id
                })
            
            for comm in communications:
                timeline.append({
                    "type": "communication",
                    "timestamp": comm.created_at,
                    "message": comm.message,
                    "sender": comm.sender_id
                })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x["timestamp"])
            
            return timeline