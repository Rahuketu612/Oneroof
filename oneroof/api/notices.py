"""
Notice management API endpoints with version control.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, RoleChecker
from oneroof.api.models import Notice, NoticeVersion, Workspace, Client, Document


router = APIRouter(prefix="/notices", tags=["Notices"])


# Pydantic schemas
class NoticeCreate(BaseModel):
    workspace_id: int
    title: str
    notice_type: str  # gst, tds, income_tax, roc, other
    source: str  # department, sender
    notice_date: datetime
    due_date: datetime
    description: Optional[str] = None
    response_required: bool = True
    response_deadline: Optional[datetime] = None
    assigned_to_user_id: Optional[int] = None


class NoticeUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to_user_id: Optional[int] = None
    response_deadline: Optional[datetime] = None


class NoticeVersionCreate(BaseModel):
    content: str
    document_ids: List[int] = []


class NoticeResponse(BaseModel):
    id: int
    workspace_id: int
    title: str
    notice_type: str
    source: str
    notice_date: datetime
    due_date: datetime
    status: str
    response_required: bool
    current_step: int
    workflow_steps: List[dict]
    assigned_to_user_id: Optional[int]
    submitted_at: Optional[datetime]
    submission_reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NoticeVersionResponse(BaseModel):
    id: int
    notice_id: int
    version: int
    content: str
    document_ids: List[int]
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Default notice workflow steps
DEFAULT_NOTICE_WORKFLOW = [
    {"step": 1, "name": "Received", "roles": ["system"], "action": "Upload and acknowledge notice"},
    {"step": 2, "name": "Drafting", "roles": ["staff"], "action": "Prepare response draft"},
    {"step": 3, "name": "Manager Review", "roles": ["manager"], "action": "Review draft response"},
    {"step": 4, "name": "Partner Review", "roles": ["partner"], "action": "Partner approval"},
    {"step": 5, "name": "Client Approval", "roles": ["client_admin"], "action": "Client final approval"},
    {"step": 6, "name": "Submission", "roles": ["staff"], "action": "Submit response"},
]


# Create notice
@router.post("/", response_model=NoticeResponse)
async def create_notice(
    notice_data: NoticeCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new notice."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager", "staff", "client_user", "client_admin"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    # Verify workspace access
    result = await db.execute(
        select(Workspace, Client)
        .join(Client, Workspace.client_id == Client.id)
        .where(Workspace.id == notice_data.workspace_id)
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    notice = Notice(
        workspace_id=notice_data.workspace_id,
        title=notice_data.title,
        notice_type=notice_data.notice_type,
        source=notice_data.source,
        notice_date=notice_data.notice_date,
        due_date=notice_data.due_date,
        description=notice_data.description,
        response_required=notice_data.response_required,
        response_deadline=notice_data.response_deadline or notice_data.due_date,
        status="received",
        workflow_steps=DEFAULT_NOTICE_WORKFLOW,
        assigned_to_user_id=notice_data.assigned_to_user_id,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    
    return NoticeResponse.model_validate(notice)


# Get notice
@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get notice details."""
    db = await anext(get_db())
    result = await db.execute(
        select(Notice).where(Notice.id == notice_id)
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    return NoticeResponse.model_validate(notice)


# List notices
@router.get("/", response_model=List[NoticeResponse])
async def list_notices(
    workspace_id: Optional[int] = None,
    status: Optional[str] = None,
    notice_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List notices with filters."""
    db = await anext(get_db())
    
    query = select(Notice)
    if workspace_id:
        query = query.where(Notice.workspace_id == workspace_id)
    if status:
        query = query.where(Notice.status == status)
    if notice_type:
        query = query.where(Notice.notice_type == notice_type)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    notices = result.scalars().all()
    
    return [NoticeResponse.model_validate(n) for n in notices]


# Update notice
@router.patch("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    update_data: NoticeUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update notice status or details."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Notice).where(Notice.id == notice_id)
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(notice, field, value)
    
    await db.commit()
    await db.refresh(notice)
    
    return NoticeResponse.model_validate(notice)


# Advance notice workflow
@router.post("/{notice_id}/advance-step")
async def advance_notice_step(
    notice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Advance to the next notice workflow step."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Notice).where(Notice.id == notice_id)
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    workflow_steps = notice.workflow_steps or DEFAULT_NOTICE_WORKFLOW
    if notice.current_step < len(workflow_steps) - 1:
        notice.current_step += 1
        
        # Update status based on step
        current_step_info = workflow_steps[notice.current_step]
        if current_step_info["name"] == "Submission":
            notice.status = "submitted"
            notice.submitted_at = datetime.utcnow()
        elif current_step_info["name"] == "Client Approval":
            notice.status = "client_approval"
        elif current_step_info["name"] == "Manager Review":
            notice.status = "manager_review"
        elif current_step_info["name"] == "Partner Review":
            notice.status = "partner_review"
    
    await db.commit()
    
    return {
        "message": "Step advanced",
        "current_step": notice.current_step,
        "status": notice.status
    }


# Create notice version (draft response)
@router.post("/{notice_id}/versions", response_model=NoticeVersionResponse)
async def create_notice_version(
    notice_id: int,
    version_data: NoticeVersionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new version of notice response."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager", "staff"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    result = await db.execute(
        select(Notice).where(Notice.id == notice_id)
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    # Get next version number
    result = await db.execute(
        select(NoticeVersion)
        .where(NoticeVersion.notice_id == notice_id)
        .order_by(NoticeVersion.version.desc())
    )
    last_version = result.scalar_one_or_none()
    next_version = (last_version.version + 1) if last_version else 1
    
    notice_version = NoticeVersion(
        notice_id=notice_id,
        version=next_version,
        content=version_data.content,
        document_ids=version_data.document_ids,
        created_by_user_id=int(current_user["user_id"]),
    )
    db.add(notice_version)
    await db.commit()
    await db.refresh(notice_version)
    
    return NoticeVersionResponse.model_validate(notice_version)


# Get notice versions
@router.get("/{notice_id}/versions", response_model=List[NoticeVersionResponse])
async def get_notice_versions(
    notice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all versions of notice response."""
    db = await anext(get_db())
    result = await db.execute(
        select(NoticeVersion)
        .where(NoticeVersion.notice_id == notice_id)
        .order_by(NoticeVersion.version)
    )
    versions = result.scalars().all()
    
    return [NoticeVersionResponse.model_validate(v) for v in versions]


# Submit notice response
@router.post("/{notice_id}/submit")
async def submit_notice(
    notice_id: int,
    submission_reference: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark notice as submitted with reference."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager", "staff"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    result = await db.execute(
        select(Notice).where(Notice.id == notice_id)
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    notice.status = "submitted"
    notice.submitted_at = datetime.utcnow()
    notice.submission_reference = submission_reference
    
    await db.commit()
    
    return {
        "message": "Notice submitted",
        "submission_reference": submission_reference,
        "submitted_at": notice.submitted_at
    }


# Close notice
@router.post("/{notice_id}/close")
async def close_notice(
    notice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Close notice after submission."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Notice).where(Notice.id == notice_id)
    )
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    notice.status = "closed"
    
    await db.commit()
    
    return {"message": "Notice closed"}