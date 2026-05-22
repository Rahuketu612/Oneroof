"""
Dashboard API endpoints - role-based views.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, RoleChecker
from oneroof.api.models import (
    ComplianceItem, Workspace, Client, DocumentRequest, 
    Approval, Notice, AuditLog, User, ClientUser
)


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Response schemas
class DashboardSummary(BaseModel):
    total_workspaces: int
    active_compliances: int
    pending_approvals: int
    overdue_items: int
    upcoming_deadlines: int
    pending_notices: int


class ComplianceStatusCount(BaseModel):
    status: str
    count: int


class StaffWorkload(BaseModel):
    user_id: int
    user_name: str
    assigned_items: int
    completed_items: int
    pending_items: int


class ClientRiskItem(BaseModel):
    client_id: int
    client_name: str
    risk_score: int
    overdue_count: int
    pending_approvals: int


class UpcomingDeadline(BaseModel):
    compliance_item_id: int
    compliance_name: str
    client_name: str
    due_date: datetime
    days_until_due: int
    status: str


class PartnerDashboard(BaseModel):
    summary: DashboardSummary
    compliance_status: list[ComplianceStatusCount]
    staff_workload: list[StaffWorkload]
    client_risks: list[ClientRiskItem]
    upcoming_deadlines: list[UpcomingDeadline]


class StaffDashboard(BaseModel):
    assigned_items: list
    pending_reviews: list
    upcoming_deadlines: list
    recent_approvals: list


class ClientDashboard(BaseModel):
    pending_uploads: list
    upcoming_due_dates: list
    pending_approvals: list
    active_notices: list


# Partner Dashboard
@router.get("/partner", response_model=PartnerDashboard)
async def get_partner_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get partner dashboard with overview."""
    if current_user["role"] != "partner":
        raise HTTPException(status_code=403, detail="Partner access required")
    
    db = await anext(get_db())
    firm_id = current_user["firm_id"]
    
    # Summary counts
    total_workspaces = await db.scalar(
        select(func.count(Workspace.id))
        .join(Client, Workspace.client_id == Client.id)
        .where(Client.firm_id == firm_id)
    ) or 0
    
    active_compliances = await db.scalar(
        select(func.count(ComplianceItem.id))
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            Client.firm_id == firm_id,
            ComplianceItem.status.in_(["pending", "in_progress", "review", "approved"])
        )
    ) or 0
    
    pending_approvals = await db.scalar(
        select(func.count(Approval.id))
        .where(Approval.status == "pending")
    ) or 0
    
    overdue_items = await db.scalar(
        select(func.count(ComplianceItem.id))
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            Client.firm_id == firm_id,
            ComplianceItem.due_date < datetime.utcnow(),
            ComplianceItem.status.notin_(["filed", "completed"])
        )
    ) or 0
    
    upcoming_deadlines = await db.scalar(
        select(func.count(ComplianceItem.id))
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            Client.firm_id == firm_id,
            ComplianceItem.due_date <= datetime.utcnow() + timedelta(days=7),
            ComplianceItem.status.in_(["pending", "in_progress"])
        )
    ) or 0
    
    pending_notices = await db.scalar(
        select(func.count(Notice.id))
        .join(Workspace, Notice.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            Client.firm_id == firm_id,
            Notice.status.in_(["received", "drafting", "review", "partner_review"])
        )
    ) or 0
    
    summary = DashboardSummary(
        total_workspaces=total_workspaces,
        active_compliances=active_compliances,
        pending_approvals=pending_approvals,
        overdue_items=overdue_items,
        upcoming_deadlines=upcoming_deadlines,
        pending_notices=pending_notices
    )
    
    # Compliance status breakdown
    status_result = await db.execute(
        select(ComplianceItem.status, func.count(ComplianceItem.id))
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(Client.firm_id == firm_id)
        .group_by(ComplianceItem.status)
    )
    compliance_status = [
        ComplianceStatusCount(status=status, count=count)
        for status, count in status_result.all()
    ]
    
    # Staff workload
    staff_result = await db.execute(
        select(User.id, User.first_name, User.last_name)
        .where(User.firm_id == firm_id, User.role == "staff")
    )
    staff_workload = []
    for user_id, first_name, last_name in staff_result.all():
        assigned = await db.scalar(
            select(func.count(ComplianceItem.id))
            .where(ComplianceItem.assigned_to_user_id == user_id)
        ) or 0
        completed = await db.scalar(
            select(func.count(ComplianceItem.id))
            .where(
                ComplianceItem.assigned_to_user_id == user_id,
                ComplianceItem.status.in_(["filed", "completed"])
            )
        ) or 0
        staff_workload.append(StaffWorkload(
            user_id=user_id,
            user_name=f"{first_name} {last_name}",
            assigned_items=assigned,
            completed_items=completed,
            pending_items=assigned - completed
        ))
    
    # Client risks
    clients_result = await db.execute(
        select(Client.id, Client.name)
        .where(Client.firm_id == firm_id, Client.is_active == True)
    )
    client_risks = []
    for client_id, client_name in clients_result.all():
        overdue_count = await db.scalar(
            select(func.count(ComplianceItem.id))
            .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
            .where(
                Workspace.client_id == client_id,
                ComplianceItem.due_date < datetime.utcnow(),
                ComplianceItem.status.notin_(["filed", "completed"])
            )
        ) or 0
        pending_approval = await db.scalar(
            select(func.count(Approval.id))
            .join(ComplianceItem, Approval.compliance_item_id == ComplianceItem.id)
            .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
            .where(
                Workspace.client_id == client_id,
                Approval.status == "pending"
            )
        ) or 0
        
        risk_score = min(100, (overdue_count * 20) + (pending_approval * 10))
        client_risks.append(ClientRiskItem(
            client_id=client_id,
            client_name=client_name,
            risk_score=risk_score,
            overdue_count=overdue_count,
            pending_approvals=pending_approval
        ))
    
    # Upcoming deadlines
    deadline_result = await db.execute(
        select(ComplianceItem, Client.name)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            Client.firm_id == firm_id,
            ComplianceItem.due_date <= datetime.utcnow() + timedelta(days=7),
            ComplianceItem.status.in_(["pending", "in_progress"])
        )
        .order_by(ComplianceItem.due_date)
        .limit(10)
    )
    upcoming_deadlines = []
    for item, client_name in deadline_result.all():
        days_until = (item.due_date - datetime.utcnow()).days
        upcoming_deadlines.append(UpcomingDeadline(
            compliance_item_id=item.id,
            compliance_name=item.name,
            client_name=client_name,
            due_date=item.due_date,
            days_until_due=days_until,
            status=item.status
        ))
    
    return PartnerDashboard(
        summary=summary,
        compliance_status=compliance_status,
        staff_workload=staff_workload,
        client_risks=client_risks,
        upcoming_deadlines=upcoming_deadlines
    )


# Manager Dashboard
@router.get("/manager")
async def get_manager_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get manager dashboard."""
    if current_user["role"] not in ["partner", "manager"]:
        raise HTTPException(status_code=403, detail="Manager access required")
    
    db = await anext(get_db())
    
    # Items requiring manager review
    review_items_result = await db.execute(
        select(ComplianceItem, Client.name, Workspace.name)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(ComplianceItem.status == "review")
        .limit(20)
    )
    
    review_items = []
    for item, client_name, workspace_name in review_items_result.all():
        review_items.append({
            "id": item.id,
            "name": item.name,
            "client": client_name,
            "workspace": workspace_name,
            "due_date": item.due_date,
            "period": item.period
        })
    
    # Pending document requests
    pending_requests_result = await db.execute(
        select(DocumentRequest, ComplianceItem.name, Client.name)
        .join(ComplianceItem, DocumentRequest.compliance_item_id == ComplianceItem.id)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(DocumentRequest.status.in_(["incomplete", "clarification_needed"]))
        .limit(20)
    )
    
    pending_requests = []
    for req, compliance_name, client_name in pending_requests_result.all():
        pending_requests.append({
            "id": req.id,
            "title": req.title,
            "compliance": compliance_name,
            "client": client_name,
            "due_date": req.due_date,
            "status": req.status
        })
    
    return {
        "review_items": review_items,
        "pending_requests": pending_requests,
        "message": "Manager dashboard data"
    }


# Staff Dashboard
@router.get("/staff", response_model=StaffDashboard)
async def get_staff_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get staff dashboard."""
    db = await anext(get_db())
    user_id = int(current_user["user_id"])
    
    # Assigned items
    assigned_result = await db.execute(
        select(ComplianceItem, Client.name)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            ComplianceItem.assigned_to_user_id == user_id,
            ComplianceItem.status.in_(["pending", "in_progress"])
        )
        .order_by(ComplianceItem.due_date)
    )
    assigned_items = [
        {
            "id": item.id,
            "name": item.name,
            "client": client_name,
            "due_date": item.due_date,
            "status": item.status
        }
        for item, client_name in assigned_result.all()
    ]
    
    # Pending reviews (items needing staff review)
    reviews_result = await db.execute(
        select(ComplianceItem, Client.name)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(ComplianceItem.status == "in_progress")
        .limit(10)
    )
    pending_reviews = [
        {
            "id": item.id,
            "name": item.name,
            "client": client_name,
            "due_date": item.due_date
        }
        for item, client_name in reviews_result.all()
    ]
    
    # Upcoming deadlines
    deadline_result = await db.execute(
        select(ComplianceItem, Client.name)
        .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
        .join(Client, Workspace.client_id == Client.id)
        .where(
            ComplianceItem.assigned_to_user_id == user_id,
            ComplianceItem.due_date <= datetime.utcnow() + timedelta(days=5),
            ComplianceItem.status.in_(["pending", "in_progress"])
        )
        .order_by(ComplianceItem.due_date)
        .limit(10)
    )
    upcoming_deadlines = [
        {
            "id": item.id,
            "name": item.name,
            "client": client_name,
            "due_date": item.due_date,
            "days_until": (item.due_date - datetime.utcnow()).days
        }
        for item, client_name in deadline_result.all()
    ]
    
    return StaffDashboard(
        assigned_items=assigned_items,
        pending_reviews=pending_reviews,
        upcoming_deadlines=upcoming_deadlines,
        recent_approvals=[]
    )


# Client Dashboard
@router.get("/client/{workspace_id}")
async def get_client_dashboard(
    workspace_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get client dashboard for a workspace."""
    db = await anext(get_db())
    
    # Verify client user access
    client_user_id = current_user.get("client_user_id")
    if not client_user_id:
        raise HTTPException(status_code=403, detail="Client access required")
    
    # Pending uploads
    pending_uploads_result = await db.execute(
        select(DocumentRequest, ComplianceItem.name)
        .join(ComplianceItem, DocumentRequest.compliance_item_id == ComplianceItem.id)
        .where(
            DocumentRequest.status.in_(["pending", "incomplete"]),
            ComplianceItem.workspace_id == workspace_id
        )
    )
    pending_uploads = [
        {
            "id": req.id,
            "title": req.title,
            "compliance": compliance_name,
            "due_date": req.due_date,
            "status": req.status
        }
        for req, compliance_name in pending_uploads_result.all()
    ]
    
    # Upcoming due dates
    due_dates_result = await db.execute(
        select(ComplianceItem)
        .where(
            ComplianceItem.workspace_id == workspace_id,
            ComplianceItem.due_date <= datetime.utcnow() + timedelta(days=14),
            ComplianceItem.status.in_(["pending", "in_progress"])
        )
        .order_by(ComplianceItem.due_date)
    )
    upcoming_due_dates = [
        {
            "id": item.id,
            "name": item.name,
            "due_date": item.due_date,
            "days_until": (item.due_date - datetime.utcnow()).days
        }
        for item in due_dates_result.all()
    ]
    
    # Pending approvals
    pending_approvals_result = await db.execute(
        select(Approval, ComplianceItem.name)
        .join(ComplianceItem, Approval.compliance_item_id == ComplianceItem.id)
        .where(
            Approval.status == "pending",
            Approval.approval_type == "client_approval",
            ComplianceItem.workspace_id == workspace_id
        )
    )
    pending_approvals = [
        {
            "id": approval.id,
            "compliance": compliance_name,
            "created_at": approval.created_at
        }
        for approval, compliance_name in pending_approvals_result.all()
    ]
    
    # Active notices
    notices_result = await db.execute(
        select(Notice).where(
            Notice.workspace_id == workspace_id,
            Notice.status.in_(["received", "drafting", "client_approval"])
        )
    )
    active_notices = [
        {
            "id": notice.id,
            "title": notice.title,
            "due_date": notice.due_date,
            "status": notice.status
        }
        for notice in notices_result.all()
    ]
    
    return {
        "pending_uploads": pending_uploads,
        "upcoming_due_dates": upcoming_due_dates,
        "pending_approvals": pending_approvals,
        "active_notices": active_notices
    }