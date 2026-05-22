"""
Workspace management API endpoints.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, RoleChecker
from oneroof.api.models import (
    Workspace, Client, ComplianceTemplate, ComplianceItem, 
    DocumentRequest, User, ClientUser
)


router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


# Pydantic schemas
class WorkspaceCreate(BaseModel):
    client_id: int
    name: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: int
    client_id: int
    name: str
    is_active: bool
    is_frozen: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceTemplateCreate(BaseModel):
    name: str
    compliance_type: str  # gst, tds, roc, income_tax
    frequency: str  # monthly, quarterly, yearly
    description: Optional[str] = None
    required_documents: List[str] = []
    workflow_steps: List[dict] = []
    reminder_days: List[int] = [-5, -2, 0]


class ComplianceTemplateResponse(BaseModel):
    id: int
    name: str
    compliance_type: str
    frequency: str
    required_documents: List[str]
    workflow_steps: List[dict]
    is_active: bool

    class Config:
        from_attributes = True


# Workspace endpoints
@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new client workspace (Partner/Manager only)."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    # Verify client belongs to firm
    result = await db.execute(
        select(Client).where(
            Client.id == workspace_data.client_id,
            Client.firm_id == current_user["firm_id"]
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check if workspace already exists
    result = await db.execute(
        select(Workspace).where(Workspace.client_id == workspace_data.client_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Workspace already exists for this client")
    
    # Create workspace
    workspace = Workspace(
        client_id=workspace_data.client_id,
        name=workspace_data.name or f"{client.name} Workspace",
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    
    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get workspace details."""
    db = await anext(get_db())
    result = await db.execute(
        select(Workspace, Client)
        .join(Client, Workspace.client_id == Client.id)
        .where(Workspace.id == workspace_id, Client.firm_id == current_user["firm_id"])
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return WorkspaceResponse.model_validate(workspace)


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List all workspaces for the firm."""
    db = await anext(get_db())
    result = await db.execute(
        select(Workspace)
        .join(Client, Workspace.client_id == Client.id)
        .where(Client.firm_id == current_user["firm_id"])
        .offset(skip)
        .limit(limit)
    )
    workspaces = result.scalars().all()
    
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.post("/{workspace_id}/freeze")
async def freeze_workspace(
    workspace_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Freeze workspace for client exit workflow (Partner only)."""
    if current_user["role"] != "partner":
        raise HTTPException(status_code=403, detail="Partner access required")
    
    db = await anext(get_db())
    
    result = await db.execute(
        select(Workspace, Client)
        .join(Client, Workspace.client_id == Client.id)
        .where(Workspace.id == workspace_id, Client.firm_id == current_user["firm_id"])
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace, client = row
    
    # Freeze workspace and client
    workspace.is_frozen = True
    workspace.frozen_at = datetime.utcnow()
    client.is_frozen = True
    
    await db.commit()
    
    return {"message": "Workspace frozen successfully"}


@router.post("/{workspace_id}/archive")
async def archive_workspace(
    workspace_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Archive workspace for compliance retention (Partner only)."""
    if current_user["role"] != "partner":
        raise HTTPException(status_code=403, detail="Partner access required")
    
    db = await anext(get_db())
    
    # Generate handover package
    result = await db.execute(
        select(Workspace)
        .where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # TODO: Generate export package with all filings, approvals, notices, etc.
    
    return {
        "message": "Archive package generated",
        "workspace_id": workspace_id,
        "status": "archived"
    }


# Compliance templates
@router.post("/templates", response_model=ComplianceTemplateResponse)
async def create_compliance_template(
    template_data: ComplianceTemplateCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a compliance template (Partner only)."""
    if current_user["role"] != "partner":
        raise HTTPException(status_code=403, detail="Partner access required")
    
    db = await anext(get_db())
    
    template = ComplianceTemplate(
        firm_id=current_user["firm_id"],
        name=template_data.name,
        compliance_type=template_data.compliance_type,
        frequency=template_data.frequency,
        description=template_data.description,
        required_documents=template_data.required_documents,
        workflow_steps=template_data.workflow_steps,
        reminder_days=template_data.reminder_days,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return ComplianceTemplateResponse.model_validate(template)


@router.get("/templates", response_model=List[ComplianceTemplateResponse])
async def list_compliance_templates(
    current_user: dict = Depends(get_current_user)
):
    """List compliance templates for the firm."""
    db = await anext(get_db())
    result = await db.execute(
        select(ComplianceTemplate)
        .where(ComplianceTemplate.firm_id == current_user["firm_id"])
    )
    templates = result.scalars().all()
    
    return [ComplianceTemplateResponse.model_validate(t) for t in templates]


# Auto-generate compliance items from templates
@router.post("/{workspace_id}/generate-compliance")
async def generate_compliance_items(
    workspace_id: int,
    period: str,  # e.g., "April 2026"
    current_user: dict = Depends(get_current_user)
):
    """Auto-generate compliance items based on client compliance types."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    # Get workspace and client
    result = await db.execute(
        select(Workspace, Client)
        .join(Client, Workspace.client_id == Client.id)
        .where(Workspace.id == workspace_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace, client = row
    
    # Get applicable templates
    compliance_types = client.compliance_types or {}
    generated = []
    
    for compliance_type, enabled in compliance_types.items():
        if not enabled:
            continue
        
        result = await db.execute(
            select(ComplianceTemplate)
            .where(
                ComplianceTemplate.firm_id == current_user["firm_id"],
                ComplianceTemplate.compliance_type == compliance_type,
                ComplianceTemplate.is_active == True
            )
        )
        templates = result.scalars().all()
        
        for template in templates:
            # Calculate due date based on frequency
            from datetime import timedelta
            due_date = datetime.utcnow() + timedelta(days=30)  # Placeholder
            
            # Create compliance item
            item = ComplianceItem(
                workspace_id=workspace_id,
                template_id=template.id,
                name=f"{template.name} - {period}",
                compliance_type=template.compliance_type,
                period=period,
                status="pending",
                due_date=due_date,
                workflow_steps=template.workflow_steps,
                is_recurring=True,
                recurrence_pattern=template.frequency,
            )
            db.add(item)
            
            # Create document requests from template
            for doc in template.required_documents:
                request = DocumentRequest(
                    compliance_item_id=None,  # Will be set after flush
                    title=doc,
                    status="pending",
                    due_date=due_date,
                )
                db.add(request)
            
            generated.append(template.name)
    
    await db.commit()
    
    return {
        "message": f"Generated {len(generated)} compliance items",
        "templates": generated
    }