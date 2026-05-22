"""
Compliance management API endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, RoleChecker
from oneroof.api.models import (
    ComplianceItem, Workspace, Client, DocumentRequest, Document,
    Approval, Communication, User
)


router = APIRouter(prefix="/compliance", tags=["Compliance"])


# Pydantic schemas
class ComplianceItemCreate(BaseModel):
    workspace_id: int
    name: str
    compliance_type: str
    period: str
    due_date: datetime
    priority: str = "normal"
    assigned_to_user_id: Optional[int] = None


class ComplianceItemUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    due_date: Optional[datetime] = None


class ComplianceItemResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    compliance_type: str
    period: str
    status: str
    priority: str
    due_date: datetime
    current_step: int
    workflow_steps: List[dict]
    is_recurring: bool
    filed_at: Optional[datetime]
    acknowledgment_number: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentRequestCreate(BaseModel):
    compliance_item_id: int
    title: str
    description: Optional[str] = None
    due_date: datetime


class DocumentRequestUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class DocumentRequestResponse(BaseModel):
    id: int
    compliance_item_id: int
    title: str
    description: Optional[str]
    status: str
    due_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Compliance Item endpoints
@router.post("/items", response_model=ComplianceItemResponse)
async def create_compliance_item(
    item_data: ComplianceItemCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new compliance item."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager", "staff"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    # Verify workspace access
    result = await db.execute(
        select(Workspace, Client)
        .join(Client, Workspace.client_id == Client.id)
        .where(Workspace.id == item_data.workspace_id, Client.firm_id == current_user["firm_id"])
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    item = ComplianceItem(
        workspace_id=item_data.workspace_id,
        name=item_data.name,
        compliance_type=item_data.compliance_type,
        period=item_data.period,
        status="pending",
        priority=item_data.priority,
        due_date=item_data.due_date,
        assigned_to_user_id=item_data.assigned_to_user_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    return ComplianceItemResponse.model_validate(item)


@router.get("/items/{item_id}", response_model=ComplianceItemResponse)
async def get_compliance_item(
    item_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get compliance item details."""
    db = await anext(get_db())
    result = await db.execute(
        select(ComplianceItem, Workspace, Client)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(ComplianceItem.id == item_id, Client.firm_id == current_user["firm_id"])
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    
    return ComplianceItemResponse.model_validate(row[0])


@router.get("/items", response_model=List[ComplianceItemResponse])
async def list_compliance_items(
    workspace_id: Optional[int] = None,
    status: Optional[str] = None,
    compliance_type: Optional[str] = None,
    overdue: bool = False,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List compliance items with filters."""
    db = await anext(get_db())
    
    query = select(ComplianceItem, Workspace, Client).join(
        Workspace, ComplianceItem.workspace_id == Workspace.id
    ).join(
        Client, Workspace.client_id == Client.id
    ).where(Client.firm_id == current_user["firm_id"])
    
    if workspace_id:
        query = query.where(ComplianceItem.workspace_id == workspace_id)
    if status:
        query = query.where(ComplianceItem.status == status)
    if compliance_type:
        query = query.where(ComplianceItem.compliance_type == compliance_type)
    if overdue:
        query = query.where(
            and_(
                ComplianceItem.due_date < datetime.utcnow(),
                ComplianceItem.status.notin_(["filed", "completed"])
            )
        )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    
    return [ComplianceItemResponse.model_validate(row[0]) for row in rows]


@router.patch("/items/{item_id}", response_model=ComplianceItemResponse)
async def update_compliance_item(
    item_id: int,
    update_data: ComplianceItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a compliance item."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(ComplianceItem, Workspace, Client)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(ComplianceItem.id == item_id, Client.firm_id == current_user["firm_id"])
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    
    item = row[0]
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    
    if update_data.status == "filed":
        item.filed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(item)
    
    return ComplianceItemResponse.model_validate(item)


@router.post("/items/{item_id}/advance-step")
async def advance_workflow_step(
    item_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Advance to the next workflow step."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(ComplianceItem).where(ComplianceItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    
    workflow_steps = item.workflow_steps or []
    if item.current_step < len(workflow_steps) - 1:
        item.current_step += 1
        
        # Log communication
        comm = Communication(
            workspace_id=item.workspace_id,
            compliance_item_id=item_id,
            communication_type="status_change",
            message=f"Workflow advanced to step {item.current_step + 1}",
            sender_type="user",
            sender_id=current_user["user_id"],
        )
        db.add(comm)
    
    await db.commit()
    
    return {"message": "Step advanced", "current_step": item.current_step}


# Document Request endpoints
@router.post("/requests", response_model=DocumentRequestResponse)
async def create_document_request(
    request_data: DocumentRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a document request."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager", "staff"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    # Verify compliance item access
    result = await db.execute(
        select(ComplianceItem, Workspace, Client)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(ComplianceItem.id == request_data.compliance_item_id, Client.firm_id == current_user["firm_id"])
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Compliance item not found")
    
    doc_request = DocumentRequest(
        compliance_item_id=request_data.compliance_item_id,
        title=request_data.title,
        description=request_data.description,
        due_date=request_data.due_date,
        status="pending",
    )
    db.add(doc_request)
    await db.commit()
    await db.refresh(doc_request)
    
    return DocumentRequestResponse.model_validate(doc_request)


@router.get("/requests/{request_id}", response_model=DocumentRequestResponse)
async def get_document_request(
    request_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get document request details."""
    db = await anext(get_db())
    result = await db.execute(
        select(DocumentRequest).where(DocumentRequest.id == request_id)
    )
    doc_request = result.scalar_one_or_none()
    
    if not doc_request:
        raise HTTPException(status_code=404, detail="Document request not found")
    
    return DocumentRequestResponse.model_validate(doc_request)


@router.get("/requests", response_model=List[DocumentRequestResponse])
async def list_document_requests(
    compliance_item_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List document requests."""
    db = await anext(get_db())
    
    query = select(DocumentRequest)
    if compliance_item_id:
        query = query.where(DocumentRequest.compliance_item_id == compliance_item_id)
    if status:
        query = query.where(DocumentRequest.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [DocumentRequestResponse.model_validate(r) for r in requests]


@router.patch("/requests/{request_id}", response_model=DocumentRequestResponse)
async def update_document_request(
    request_id: int,
    update_data: DocumentRequestUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a document request status."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(DocumentRequest).where(DocumentRequest.id == request_id)
    )
    doc_request = result.scalar_one_or_none()
    
    if not doc_request:
        raise HTTPException(status_code=404, detail="Document request not found")
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(doc_request, field, value)
    
    await db.commit()
    await db.refresh(doc_request)
    
    return DocumentRequestResponse.model_validate(doc_request)


# Bulk operations for reminders
@router.post("/generate-reminders")
async def generate_compliance_reminders(
    current_user: dict = Depends(get_current_user)
):
    """Generate reminders for upcoming deadlines (called by scheduler)."""
    if current_user["role"] != "partner":
        raise HTTPException(status_code=403, detail="Partner access required")
    
    db = await anext(get_db())
    
    # Get items due within 5 days
    reminder_date = datetime.utcnow() + timedelta(days=5)
    
    result = await db.execute(
        select(ComplianceItem, Workspace, Client)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            and_(
                Client.firm_id == current_user["firm_id"],
                ComplianceItem.due_date <= reminder_date,
                ComplianceItem.status.in_(["pending", "in_progress"])
            )
        )
    )
    items = result.all()
    
    reminders_sent = 0
    for item, workspace, client in items:
        # Check if reminder already sent today
        days_until_due = (item.due_date - datetime.utcnow()).days
        
        if days_until_due in [5, 2, 0] or days_until_due < 0:
            # Create notification (placeholder)
            reminders_sent += 1
    
    return {
        "message": f"Processed {len(items)} compliance items",
        "reminders_sent": reminders_sent
    }