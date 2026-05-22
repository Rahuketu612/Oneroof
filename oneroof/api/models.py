"""
Database models for OneRoof.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey,
    Text, Enum, JSON, Float, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from oneroof.core.database import Base


class Firm(Base):
    """Firm/Organization model."""
    __tablename__ = "firms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="firm", cascade="all, delete-orphan")
    workspaces: Mapped[List["Workspace"]] = relationship("Workspace", back_populates="firm", cascade="all, delete-orphan")


class User(Base):
    """Firm user model (Partner, Manager, Staff)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firm_id: Mapped[int] = mapped_column(Integer, ForeignKey("firms.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # partner, manager, staff
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    firm: Mapped["Firm"] = relationship("Firm", back_populates="users")
    assigned_tasks: Mapped[List["ComplianceItem"]] = relationship("ComplianceItem", back_populates="assigned_to_user")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        UniqueConstraint("firm_id", "email", name="unique_firm_user_email"),
        Index("idx_user_email", "email"),
    )


class Client(Base):
    """Client organization model."""
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firm_id: Mapped[int] = mapped_column(Integer, ForeignKey("firms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # proprietorship, partnership, pvt_ltd, llp, etc.
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compliance_types: Mapped[dict] = mapped_column(JSON, default=dict)  # gst, tds, roc, income_tax, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)  # For exit workflow
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    workspaces: Mapped[List["Workspace"]] = relationship("Workspace", back_populates="client", cascade="all, delete-orphan")
    client_users: Mapped[List["ClientUser"]] = relationship("ClientUser", back_populates="client", cascade="all, delete-orphan")


class ClientUser(Base):
    """Client user model (Admin, User, Viewer)."""
    __tablename__ = "client_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # client_admin, client_user, client_viewer
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invite_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invite_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="client_users")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="client_user")
    document_uploads: Mapped[List["Document"]] = relationship("Document", back_populates="uploaded_by_client_user")

    __table_args__ = (
        UniqueConstraint("client_id", "email", name="unique_client_user_email"),
    )


class Workspace(Base):
    """Client workspace model - one per client."""
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)  # For exit workflow
    frozen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="workspaces")
    compliance_items: Mapped[List["ComplianceItem"]] = relationship("ComplianceItem", back_populates="workspace", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    notices: Mapped[List["Notice"]] = relationship("Notice", back_populates="workspace", cascade="all, delete-orphan")
    communications: Mapped[List["Communication"]] = relationship("Communication", back_populates="workspace")


class ComplianceTemplate(Base):
    """Compliance template for auto-generating workflows."""
    __tablename__ = "compliance_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firm_id: Mapped[int] = mapped_column(Integer, ForeignKey("firms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    compliance_type: Mapped[str] = mapped_column(String(50), nullable=False)  # gst, tds, roc, income_tax
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly, quarterly, yearly
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_documents: Mapped[dict] = mapped_column(JSON, default=list)
    workflow_steps: Mapped[dict] = mapped_column(JSON, default=list)
    reminder_days: Mapped[dict] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ComplianceItem(Base):
    """Individual compliance item/task."""
    __tablename__ = "compliance_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("compliance_templates.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    compliance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "April 2026"
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, in_progress, review, approved, filed, overdue
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, urgent
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    workflow_steps: Mapped[dict] = mapped_column(JSON, default=list)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True)
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    filed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acknowledgment_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="compliance_items")
    template: Mapped[Optional["ComplianceTemplate"]] = relationship("ComplianceTemplate")
    assigned_to_user: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks")
    requests: Mapped[List["DocumentRequest"]] = relationship("DocumentRequest", back_populates="compliance_item")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="compliance_item")

    __table_args__ = (
        Index("idx_compliance_due_date", "due_date"),
        Index("idx_compliance_status", "status"),
    )


class DocumentRequest(Base):
    """Document request from firm to client."""
    __tablename__ = "document_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    compliance_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("compliance_items.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, submitted, accepted, incomplete, clarification_needed, rejected
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    compliance_item: Mapped["ComplianceItem"] = relationship("ComplianceItem", back_populates="requests")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="request")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="request")


class Document(Base):
    """Document model with version control."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False)
    request_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("document_requests.id"), nullable=True)
    compliance_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("compliance_items.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hash
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("documents.id"), nullable=True)  # For versioning
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # compliance, financials, legal, internal
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # gst, tds, roc, etc.
    visibility: Mapped[str] = mapped_column(String(20), default="client")  # internal, client, all
    uploaded_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_by_client_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("client_users.id"), nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="documents")
    request: Mapped[Optional["DocumentRequest"]] = relationship("DocumentRequest", back_populates="documents")
    compliance_item: Mapped[Optional["ComplianceItem"]] = relationship("ComplianceItem")
    uploaded_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[uploaded_by_user_id])
    uploaded_by_client_user: Mapped[Optional["ClientUser"]] = relationship("ClientUser", back_populates="document_uploads")
    parent: Mapped[Optional["Document"]] = relationship("Document", remote_side=[id], backref="versions")
    watermarks: Mapped[List["Watermark"]] = relationship("Watermark", back_populates="document")

    __table_args__ = (
        Index("idx_document_workspace", "workspace_id"),
        Index("idx_document_hash", "file_hash"),
    )


class Watermark(Base):
    """Watermark tracking for downloaded sensitive documents."""
    __tablename__ = "watermarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)
    downloaded_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    downloaded_by_client_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("client_users.id"), nullable=True)
    watermark_text: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="watermarks")


class Approval(Base):
    """Approval records - immutable."""
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    compliance_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("compliance_items.id"), nullable=True)
    approval_type: Mapped[str] = mapped_column(String(50), nullable=False)  # client_approval, manager_approval, partner_approval
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # pending, approved, rejected, override
    approved_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_client_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("client_users.id"), nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    device_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    compliance_item: Mapped[Optional["ComplianceItem"]] = relationship("ComplianceItem", back_populates="approvals")
    approved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_user_id])
    approved_by_client_user: Mapped[Optional["ClientUser"]] = relationship("ClientUser", back_populates="approvals")

    __table_args__ = (
        Index("idx_approval_compliance", "compliance_item_id"),
    )


class Notice(Base):
    """Notice management."""
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notice_type: Mapped[str] = mapped_column(String(50), nullable=False)  # gst, tds, income_tax, roc, other
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # department, sender
    notice_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="received")  # received, drafting, review, partner_review, client_approval, submitted, closed
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_required: Mapped[bool] = mapped_column(Boolean, default=True)
    response_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    workflow_steps: Mapped[dict] = mapped_column(JSON, default=list)
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submission_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="notices")
    assigned_to_user: Mapped[Optional["User"]] = relationship("User")
    versions: Mapped[List["NoticeVersion"]] = relationship("NoticeVersion", back_populates="notice", cascade="all, delete-orphan")


class NoticeVersion(Base):
    """Notice response versions - version controlled."""
    __tablename__ = "notice_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    notice_id: Mapped[int] = mapped_column(Integer, ForeignKey("notices.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_ids: Mapped[List[int]] = mapped_column(JSON, default=list)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    notice: Mapped["Notice"] = relationship("Notice", back_populates="versions")
    created_by_user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("notice_id", "version", name="unique_notice_version"),
    )


class Communication(Base):
    """Structured communication - must be linked to compliance item."""
    __tablename__ = "communications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False)
    compliance_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("compliance_items.id"), nullable=True)
    communication_type: Mapped[str] = mapped_column(String(50), nullable=False)  # request, upload, approval, filing, notice, comment
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)  # user, client_user, system
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="communications")
    compliance_item: Mapped[Optional["ComplianceItem"]] = relationship("ComplianceItem")

    __table_args__ = (
        Index("idx_comm_workspace", "workspace_id"),
        Index("idx_comm_compliance", "compliance_item_id"),
    )


class Comment(Base):
    """Comments on document requests."""
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("document_requests.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)  # user, client_user
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    request: Mapped["DocumentRequest"] = relationship("DocumentRequest", back_populates="comments")


class AuditLog(Base):
    """Immutable audit log - tracks everything."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    client_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("client_users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # login, upload, download, approve, etc.
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # document, compliance, approval, etc.
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_workspace", "workspace_id"),
    )


class Notification(Base):
    """User notifications."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    client_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("client_users.id"), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)  # reminder, approval_request, status_change, etc.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_notification_user", "user_id"),
        Index("idx_notification_read", "is_read"),
    )


# Import for relationship resolution
from oneroof.api.users.models import User, ClientUser