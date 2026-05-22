"""
Approval management API endpoints - immutable approvals with IP logging.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy import select

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, RoleChecker
from oneroof.api.models import Approval, ComplianceItem, Workspace, Client, ClientUser


router = APIRouter(prefix="/approvals", tags=["Approvals"])


# Pydantic schemas
class ApprovalCreate(BaseModel):
    compliance_item_id: int
    approval_type: str  # client_approval, manager_approval, partner_approval


class ApprovalAction(BaseModel):
    status: str  # approved, rejected
    comments: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    compliance_item_id: Optional[int]
    approval_type: str
    status: str
    approved_by_user_id: Optional[int]
    approved_by_client_user_id: Optional[int]
    comments: Optional[str]
    ip_address: Optional[str]
    device_info: Optional[dict]
    approved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Helper to extract IP and device info
def extract_request_info(request: Request, user_agent: Optional[str] = None) -> dict:
    """Extract IP address and device info from request."""
    client_ip = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    
    return {
        "ip_address": client_ip,
        "user_agent": user_agent or request.headers.get("User-Agent"),
    }


# Create approval request
@router.post("/", response_model=ApprovalResponse)
async def create_approval_request(
    approval_data: ApprovalCreate,
    request: Request,
    user_agent: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Create a new approval request."""
    db = await anext(get_db())
    
    # Verify compliance item exists
    result = await db.execute(
        select(ComplianceItem, Workspace, Client)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(ComplianceItem.id == approval_data.compliance_item_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    
    # Check for existing pending approval
    result = await db.execute(
        select(Approval)
        .where(
            Approval.compliance_item_id == approval_data.compliance_item_id,
            Approval.approval_type == approval_data.approval_type,
            Approval.status == "pending"
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Approval already pending")
    
    request_info = extract_request_info(request, user_agent)
    
    approval = Approval(
        compliance_item_id=approval_data.compliance_item_id,
        approval_type=approval_data.approval_type,
        status="pending",
        ip_address=request_info["ip_address"],
        user_agent=request_info["user_agent"],
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    
    return ApprovalResponse.model_validate(approval)


# Get approval request
@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get approval details."""
    db = await anext(get_db())
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    return ApprovalResponse.model_validate(approval)


# List pending approvals
@router.get("/", response_model=List[ApprovalResponse])
async def list_approvals(
    compliance_item_id: Optional[int] = None,
    status: Optional[str] = None,
    approval_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List approvals with filters."""
    db = await anext(get_db())
    
    query = select(Approval)
    if compliance_item_id:
        query = query.where(Approval.compliance_item_id == compliance_item_id)
    if status:
        query = query.where(Approval.status == status)
    if approval_type:
        query = query.where(Approval.approval_type == approval_type)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    approvals = result.scalars().all()
    
    return [ApprovalResponse.model_validate(a) for a in approvals]


# Approve/reject approval
@router.post("/{approval_id}/action", response_model=ApprovalResponse)
async def action_approval(
    approval_id: int,
    action: ApprovalAction,
    request: Request,
    user_agent: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Approve or reject an approval request."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")
    
    request_info = extract_request_info(request, user_agent)
    
    # Set approver based on role
    approved_by_user_id = None
    approved_by_client_user_id = None
    
    if current_user["role"] in ["partner", "manager", "staff"]:
        approved_by_user_id = int(current_user["user_id"])
    elif current_user.get("client_user_id"):
        approved_by_client_user_id = current_user["client_user_id"]
    
    # Update approval
    approval.status = action.status
    approval.comments = action.comments
    approval.approved_by_user_id = approved_by_user_id
    approved_by_client_user_id = approved_by_client_user_id
    approval.ip_address = request_info["ip_address"]
    approval.user_agent = request_info["user_agent"]
    approval.approved_at = datetime.utcnow()
    
    # If approved, update compliance item status
    if action.status == "approved" and approval.compliance_item_id:
        result = await db.execute(
            select(ComplianceItem).where(ComplianceItem.id == approval.compliance_item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            if approval.approval_type == "client_approval":
                item.status = "approved"
            elif approval.approval_type == "manager_approval":
                item.status = "review"
            elif approval.approval_type == "partner_approval":
                item.status = "ready_to_file"
    
    await db.commit()
    await db.refresh(approval)
    
    return ApprovalResponse.model_validate(approval)


# Override approval (Partner only)
@router.post("/{approval_id}/override")
async def override_approval(
    approval_id: int,
    comments: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Override approval with authority (Partner only)."""
    if current_user["role"] != "partner":
        raise HTTPException(status_code=403, detail="Partner access required")
    
    db = await anext(get_db())
    
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    request_info = extract_request_info(request)
    
    approval.status = "override"
    approval.comments = f"OVERRIDE: {comments}"
    approval.approved_by_user_id = int(current_user["user_id"])
    approval.ip_address = request_info["ip_address"]
    approval.approved_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Override recorded"}


# Client approval endpoint
@router.post("/client-approve/{approval_id}")
async def client_approve(
    approval_id: int,
    action: ApprovalAction,
    request: Request,
    user_agent: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Client user approval (must be client_admin for filing approval)."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.approval_type != "client_approval":
        raise HTTPException(status_code=400, detail="Not a client approval")
    
    # Verify client user is associated
    if not current_user.get("client_user_id"):
        raise HTTPException(status_code=403, detail="Client user access required")
    
    request_info = extract_request_info(request, user_agent)
    
    approval.status = action.status
    approval.comments = action.comments
    approval.approved_by_client_user_id = current_user["client_user_id"]
    approval.ip_address = request_info["ip_address"]
    approval.user_agent = request_info["user_agent"]
    approval.approved_at = datetime.utcnow()
    approval.device_info = request_info
    
    await db.commit()
    await db.refresh(approval)
    
    return {
        "message": f"Approval {action.status}",
        "approved_at": approval.approved_at
    }