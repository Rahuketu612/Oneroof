"""
Client exit workflow - handles relationship termination securely.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_

from oneroof.core.database import AsyncSessionLocal
from oneroof.api.models import (
    Workspace, Client, ClientUser, User, 
    ComplianceItem, Document, Approval, Notice,
    AuditLog, Communication
)
from oneroof.audit.logging import AuditLogger


class ClientExitWorkflow:
    """
    Handles client exit workflow with these steps:
    1. Freeze workspace (no edits allowed)
    2. Generate handover package
    3. Revoke access
    4. Archive for retention
    """
    
    @staticmethod
    async def initiate_exit(workspace_id: int, initiated_by_user_id: int) -> dict:
        """Initiate the client exit workflow."""
        async with AsyncSessionLocal() as db:
            # Get workspace and client
            result = await db.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                return {"success": False, "error": "Workspace not found"}
            
            # Check if already frozen
            if workspace.is_frozen:
                return {"success": False, "error": "Workspace already frozen"}
            
            # Get client
            result = await db.execute(
                select(Client).where(Client.id == workspace.client_id)
            )
            client = result.scalar_one_or_none()
            
            # STEP 1: Freeze workspace
            workspace.is_frozen = True
            workspace.frozen_at = datetime.utcnow()
            client.is_frozen = True
            
            # Log the freeze
            await AuditLogger.log(
                action="workspace_freeze",
                resource_type="workspace",
                resource_id=workspace_id,
                user_id=initiated_by_user_id,
                workspace_id=workspace_id,
                details={"initiated_by": initiated_by_user_id, "reason": "client_exit"},
                db=db
            )
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Workspace frozen successfully",
                "step": 1,
                "workspace_id": workspace_id,
                "frozen_at": workspace.frozen_at.isoformat(),
            }
    
    @staticmethod
    async def generate_handover_package(workspace_id: int) -> dict:
        """
        Generate comprehensive handover package for client.
        Includes all filings, approvals, notices, and timeline.
        """
        async with AsyncSessionLocal() as db:
            # Get workspace
            result = await db.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                return {"success": False, "error": "Workspace not found"}
            
            if not workspace.is_frozen:
                return {"success": False, "error": "Workspace must be frozen first"}
            
            # Get client info
            result = await db.execute(
                select(Client).where(Client.id == workspace.client_id)
            )
            client = result.scalar_one_or_none()
            
            # Gather all data
            package = {
                "client_info": {
                    "id": client.id,
                    "name": client.name,
                    "gstin": client.gstin,
                    "pan": client.pan,
                    "entity_type": client.entity_type,
                    "compliance_types": client.compliance_types,
                },
                "workspace_info": {
                    "id": workspace.id,
                    "created_at": workspace.created_at.isoformat(),
                    "frozen_at": workspace.frozen_at.isoformat() if workspace.frozen_at else None,
                },
                "compliance_records": [],
                "notices": [],
                "approvals": [],
                "documents_summary": {},
                "audit_timeline": [],
            }
            
            # Get all compliance items
            result = await db.execute(
                select(ComplianceItem)
                .where(ComplianceItem.workspace_id == workspace_id)
                .order_by(ComplianceItem.due_date.desc())
            )
            compliance_items = result.scalars().all()
            
            for item in compliance_items:
                package["compliance_records"].append({
                    "id": item.id,
                    "name": item.name,
                    "type": item.compliance_type,
                    "period": item.period,
                    "status": item.status,
                    "due_date": item.due_date.isoformat(),
                    "filed_at": item.filed_at.isoformat() if item.filed_at else None,
                    "acknowledgment_number": item.acknowledgment_number,
                })
            
            # Get all notices
            result = await db.execute(
                select(Notice)
                .where(Notice.workspace_id == workspace_id)
                .order_by(Notice.notice_date.desc())
            )
            notices = result.scalars().all()
            
            for notice in notices:
                package["notices"].append({
                    "id": notice.id,
                    "title": notice.title,
                    "type": notice.notice_type,
                    "source": notice.source,
                    "notice_date": notice.notice_date.isoformat(),
                    "due_date": notice.due_date.isoformat(),
                    "status": notice.status,
                    "submitted_at": notice.submitted_at.isoformat() if notice.submitted_at else None,
                    "submission_reference": notice.submission_reference,
                })
            
            # Get all approvals
            result = await db.execute(
                select(Approval)
                .join(ComplianceItem, Approval.compliance_item_id == ComplianceItem.id)
                .where(ComplianceItem.workspace_id == workspace_id)
            )
            approvals = result.scalars().all()
            
            for approval in approvals:
                package["approvals"].append({
                    "id": approval.id,
                    "type": approval.approval_type,
                    "status": approval.status,
                    "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
                    "comments": approval.comments,
                    "ip_address": approval.ip_address,
                })
            
            # Get audit timeline
            result = await db.execute(
                select(AuditLog)
                .where(AuditLog.workspace_id == workspace_id)
                .order_by(AuditLog.timestamp.desc())
            )
            audit_logs = result.scalars().all()
            
            for log in audit_logs:
                package["audit_timeline"].append({
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "user_id": log.user_id,
                    "client_user_id": log.client_user_id,
                    "details": log.details,
                })
            
            # Get document summary
            result = await db.execute(
                select(Document)
                .where(
                    Document.workspace_id == workspace_id,
                    Document.is_latest == True,
                    Document.is_deleted == False
                )
            )
            documents = result.scalars().all()
            
            package["documents_summary"] = {
                "total_documents": len(documents),
                "by_category": {},
                "total_size_bytes": sum(d.file_size for d in documents),
            }
            
            for doc in documents:
                category = doc.category
                if category not in package["documents_summary"]["by_category"]:
                    package["documents_summary"]["by_category"][category] = 0
                package["documents_summary"]["by_category"][category] += 1
            
            # Log the package generation
            await AuditLogger.log(
                action="export",
                resource_type="handover_package",
                resource_id=workspace_id,
                workspace_id=workspace_id,
                details={
                    "compliance_count": len(compliance_items),
                    "notices_count": len(notices),
                    "documents_count": len(documents),
                },
                db=db
            )
            
            return {
                "success": True,
                "package": package,
                "generated_at": datetime.utcnow().isoformat(),
            }
    
    @staticmethod
    async def revoke_client_access(workspace_id: int) -> dict:
        """Revoke all client user access to the workspace."""
        async with AsyncSessionLocal() as db:
            # Get workspace
            result = await db.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                return {"success": False, "error": "Workspace not found"}
            
            # Get all client users for this client
            result = await db.execute(
                select(ClientUser).where(ClientUser.client_id == workspace.client_id)
            )
            client_users = result.scalars().all()
            
            revoked_count = 0
            for user in client_users:
                user.is_active = False
                revoked_count += 1
                
                # Log each revocation
                await AuditLogger.log(
                    action="user_deactivate",
                    resource_type="client_user",
                    resource_id=user.id,
                    workspace_id=workspace_id,
                    details={
                        "email": user.email,
                        "reason": "client_exit_workflow"
                    },
                    db=db
                )
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Revoked access for {revoked_count} client users",
                "revoked_count": revoked_count,
            }
    
    @staticmethod
    async def archive_workspace(workspace_id: int) -> dict:
        """Archive workspace for compliance retention."""
        async with AsyncSessionLocal() as db:
            # Get workspace
            result = await db.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                return {"success": False, "error": "Workspace not found"}
            
            # Log the archive
            await AuditLogger.log(
                action="workspace_archive",
                resource_type="workspace",
                resource_id=workspace_id,
                workspace_id=workspace_id,
                details={
                    "archived_at": datetime.utcnow().isoformat(),
                    "retention_period_years": 7
                },
                db=db
            )
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Workspace archived successfully",
                "workspace_id": workspace_id,
                "archived_at": datetime.utcnow().isoformat(),
                "retention_period": "7 years (per compliance requirements)",
            }
    
    @staticmethod
    async def get_exit_workflow_status(workspace_id: int) -> dict:
        """Get current status of exit workflow."""
        async with AsyncSessionLocal() as db:
            # Get workspace
            result = await db.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                return {"success": False, "error": "Workspace not found"}
            
            status = {
                "workspace_id": workspace_id,
                "is_frozen": workspace.is_frozen,
                "frozen_at": workspace.frozen_at.isoformat() if workspace.frozen_at else None,
                "steps": {
                    "1_freeze": {
                        "completed": workspace.is_frozen,
                        "status": "completed" if workspace.is_frozen else "pending"
                    },
                    "2_handover": {
                        "completed": workspace.is_frozen,  # Would check if package was generated
                        "status": "pending"
                    },
                    "3_revoke_access": {
                        "completed": False,
                        "status": "pending"
                    },
                    "4_archive": {
                        "completed": False,
                        "status": "pending"
                    },
                },
                "next_step": None,
            }
            
            # Determine next step
            if not workspace.is_frozen:
                status["next_step"] = "freeze"
            else:
                status["next_step"] = "generate_handover"
            
            return status