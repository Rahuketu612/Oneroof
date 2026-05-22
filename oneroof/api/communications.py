"""
Communication API endpoints - structured communication only.
All communication must be linked to compliance items.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, RoleChecker
from oneroof.api.models import Communication, ComplianceItem, Workspace, Client, AuditLog


router = APIRouter(prefix="/communications", tags=["Communications"])


# Pydantic schemas
class CommunicationCreate(BaseModel):
    workspace_id: int
    compliance_item_id: Optional[int] = None
    communication_type: str  # request, upload, approval, filing, notice, comment
    message: str


class CommunicationResponse(BaseModel):
    id: int
    workspace_id: int
    compliance_item_id: Optional[int]
    communication_type: str
    message: str
    sender_type: str
    sender_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# CRITICAL: All communication must be linked to compliance item
@router.post("/", response_model=CommunicationResponse)
async def create_communication(
    comm_data: CommunicationCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create structured communication.
    CRITICAL: Communication must be linked to compliance item.
    Generic messages without context are NOT allowed.
    """
    db = await anext(get_db())
    
    # Verify workspace access
    result = await db.execute(
        select(Workspace, Client)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            Workspace.id == comm_data.workspace_id,
            Client.firm_id == current_user["firm_id"]
        )
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Validate compliance_item_id is provided
    if not comm_data.compliance_item_id:
        raise HTTPException(
            status_code=400,
            detail="Communication must be linked to a compliance item. Use 'comment on [compliance name]' format."
        )
    
    # Verify compliance item exists
    result = await db.execute(
        select(ComplianceItem).where(ComplianceItem.id == comm_data.compliance_item_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Compliance item not found")
    
    # Determine sender type and ID
    sender_type = "user"
    sender_id = int(current_user["user_id"])
    
    if current_user.get("client_user_id"):
        sender_type = "client_user"
        sender_id = current_user["client_user_id"]
    
    communication = Communication(
        workspace_id=comm_data.workspace_id,
        compliance_item_id=comm_data.compliance_item_id,
        communication_type=comm_data.communication_type,
        message=comm_data.message,
        sender_type=sender_type,
        sender_id=sender_id,
    )
    db.add(communication)
    
    # Audit log
    audit = AuditLog(
        user_id=int(current_user["user_id"]) if sender_type == "user" else None,
        client_user_id=sender_id if sender_type == "client_user" else None,
        action="send_message",
        resource_type="communication",
        resource_id=None,
        workspace_id=comm_data.workspace_id,
        details={"type": comm_data.communication_type}
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(communication)
    
    return CommunicationResponse.model_validate(communication)


@router.get("/{communication_id}", response_model=CommunicationResponse)
async def get_communication(
    communication_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get communication details."""
    db = await anext(get_db())
    result = await db.execute(
        select(Communication).where(Communication.id == communication_id)
    )
    comm = result.scalar_one_or_none()
    
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    
    return CommunicationResponse.model_validate(comm)


@router.get("/", response_model=List[CommunicationResponse])
async def list_communications(
    workspace_id: Optional[int] = None,
    compliance_item_id: Optional[int] = None,
    communication_type: Optional[str] = None,
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List communications with filters."""
    db = await anext(get_db())
    
    query = select(Communication)
    
    if workspace_id:
        query = query.where(Communication.workspace_id == workspace_id)
    if compliance_item_id:
        query = query.where(Communication.compliance_item_id == compliance_item_id)
    if communication_type:
        query = query.where(Communication.communication_type == communication_type)
    if unread_only:
        query = query.where(Communication.is_read == False)
    
    query = query.order_by(Communication.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    communications = result.scalars().all()
    
    return [CommunicationResponse.model_validate(c) for c in communications]


@router.post("/{communication_id}/mark-read")
async def mark_communication_read(
    communication_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Mark communication as read."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Communication).where(Communication.id == communication_id)
    )
    comm = result.scalar_one_or_none()
    
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    
    comm.is_read = True
    await db.commit()
    
    return {"message": "Marked as read"}


@router.get("/workspace/{workspace_id}/timeline")
async def get_workspace_timeline(
    workspace_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get complete workspace timeline (audit trail view)."""
    db = await anext(get_db())
    
    # Get communications
    result = await db.execute(
        select(Communication)
        .where(Communication.workspace_id == workspace_id)
        .order_by(Communication.created_at.desc())
        .limit(100)
    )
    communications = result.scalars().all()
    
    # Get audit logs
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
    )
    audit_logs = result.scalars().all()
    
    return {
        "communications": [CommunicationResponse.model_validate(c) for c in communications],
        "audit_logs": [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "action": a.action,
                "resource_type": a.resource_type,
                "details": a.details
            }
            for a in audit_logs
        ]
    }