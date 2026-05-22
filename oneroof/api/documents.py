"""
Document management API endpoints with versioning and encryption.
"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, RoleChecker
from oneroof.core.config import settings
from oneroof.api.models import (
    Document, Workspace, Client, ClientUser, User,
    Watermark, AuditLog, DocumentRequest
)


router = APIRouter(prefix="/documents", tags=["Documents"])


# Pydantic schemas
class DocumentResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    file_size: int
    mime_type: str
    version: int
    category: str
    sub_category: Optional[str]
    visibility: str
    is_latest: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionResponse(BaseModel):
    id: int
    name: str
    version: int
    created_at: datetime
    uploaded_by_user_id: Optional[int]
    uploaded_by_client_user_id: Optional[int]

    class Config:
        from_attributes = True


# File upload with encryption
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: int = Query(...),
    request_id: Optional[int] = Query(None),
    compliance_item_id: Optional[int] = Query(None),
    category: str = Query(...),  # compliance, financials, legal, internal
    sub_category: Optional[str] = Query(None),
    visibility: str = Query("client"),  # internal, client, all
    current_user: dict = Depends(get_current_user)
):
    """Upload a document with encryption and versioning."""
    
    # Validate file extension
    allowed_extensions = settings.ALLOWED_EXTENSIONS
    file_ext = "." + file.filename.split(".")[-1].lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {allowed_extensions}")
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Compute file hash for integrity
    file_hash = hashlib.sha256(content).hexdigest()
    
    db = await anext(get_db())
    
    # Verify workspace access
    result = await db.execute(
        select(Workspace, Client)
        .join(Client, Workspace.client_id == Client.id)
        .where(Workspace.id == workspace_id, Client.firm_id == current_user["firm_id"])
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check for existing document with same name (for versioning)
    result = await db.execute(
        select(Document)
        .where(
            Document.workspace_id == workspace_id,
            Document.name == file.filename,
            Document.is_latest == True
        )
    )
    existing_doc = result.scalar_one_or_none()
    
    # Determine uploader
    uploaded_by_user_id = None
    uploaded_by_client_user_id = None
    
    if current_user["role"] in ["partner", "manager", "staff"]:
        uploaded_by_user_id = int(current_user["user_id"])
    elif current_user.get("client_user_id"):
        uploaded_by_client_user_id = current_user["client_user_id"]
    
    # Generate unique file path
    unique_id = secrets.token_urlsafe(16)
    file_path = f"{workspace_id}/{unique_id}{file_ext}"
    
    if existing_doc:
        # Versioning: mark old as not latest
        existing_doc.is_latest = False
        new_version = existing_doc.version + 1
    else:
        new_version = 1
    
    # Create document record
    document = Document(
        workspace_id=workspace_id,
        request_id=request_id,
        compliance_item_id=compliance_item_id,
        name=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        file_hash=file_hash,
        version=new_version,
        parent_id=existing_doc.id if existing_doc else None,
        category=category,
        sub_category=sub_category,
        visibility=visibility,
        uploaded_by_user_id=uploaded_by_user_id,
        uploaded_by_client_user_id=uploaded_by_client_user_id,
    )
    db.add(document)
    
    # Create audit log
    audit = AuditLog(
        user_id=uploaded_by_user_id,
        client_user_id=uploaded_by_client_user_id,
        action="upload",
        resource_type="document",
        resource_id=None,  # Will be set after commit
        workspace_id=workspace_id,
        details={"filename": file.filename, "size": len(content), "hash": file_hash}
    )
    db.add(audit)
    
    # TODO: Encrypt and save file to storage
    # For now, create placeholder
    # encrypted_content = encrypt_file(content, settings.ENCRYPTION_KEY)
    # save_to_storage(file_path, encrypted_content)
    
    await db.commit()
    await db.refresh(document)
    
    return {
        "id": document.id,
        "name": document.name,
        "version": document.version,
        "hash": document.file_hash,
        "message": "Document uploaded successfully"
    }


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get document details."""
    db = await anext(get_db())
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all versions of a document."""
    db = await anext(get_db())
    
    # Get the root document
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get all versions
    # Either children of this document or siblings with same original name
    if document.parent_id:
        root_id = document.parent_id
    else:
        root_id = document.id
    
    result = await db.execute(
        select(Document)
        .where(
            or_(
                Document.parent_id == root_id,
                Document.id == root_id
            )
        )
        .order_by(Document.version)
    )
    versions = result.scalars().all()
    
    return [DocumentVersionResponse.model_validate(v) for v in versions]


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    watermark: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Download document with optional watermarking."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check visibility permissions
    if document.visibility == "internal" and current_user["role"] not in ["partner", "manager", "staff"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create watermark record if sensitive
    user_id = int(current_user["user_id"]) if current_user.get("user_id") else None
    client_user_id = current_user.get("client_user_id")
    
    if watermark and document.visibility in ["client", "all"]:
        watermark_text = f"Downloaded by User ID: {user_id or client_user_id} at {datetime.utcnow()}"
        watermark_record = Watermark(
            document_id=document_id,
            downloaded_by_user_id=user_id,
            downloaded_by_client_user_id=client_user_id,
            watermark_text=watermark_text,
        )
        db.add(watermark_record)
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        client_user_id=client_user_id,
        action="download",
        resource_type="document",
        resource_id=document_id,
        workspace_id=document.workspace_id,
    )
    db.add(audit)
    
    await db.commit()
    
    # TODO: Decrypt and return file
    return {
        "message": "Download link generated",
        "document_id": document_id,
        "watermarked": watermark
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a document (no overwriting)."""
    if current_user["role"] not in ["partner", "manager"]:
        raise HTTPException(status_code=403, detail="Partner/Manager access required")
    
    db = await anext(get_db())
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.is_deleted = True
    document.deleted_at = datetime.utcnow()
    
    # Audit log
    audit = AuditLog(
        user_id=int(current_user["user_id"]),
        action="delete",
        resource_type="document",
        resource_id=document_id,
        workspace_id=document.workspace_id,
    )
    db.add(audit)
    
    await db.commit()
    
    return {"message": "Document deleted"}


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    workspace_id: Optional[int] = None,
    compliance_item_id: Optional[int] = None,
    category: Optional[str] = None,
    is_latest: bool = True,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List documents with filters."""
    db = await anext(get_db())
    
    query = select(Document).where(Document.is_deleted == False)
    
    if workspace_id:
        query = query.where(Document.workspace_id == workspace_id)
    if compliance_item_id:
        query = query.where(Document.compliance_item_id == compliance_item_id)
    if category:
        query = query.where(Document.category == category)
    if is_latest:
        query = query.where(Document.is_latest == True)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [DocumentResponse.model_validate(d) for d in documents]


@router.post("/verify-integrity/{document_id}")
async def verify_document_integrity(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Verify document hash matches stored hash."""
    db = await anext(get_db())
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # TODO: Compute current file hash and compare
    stored_hash = document.file_hash
    current_hash = "placeholder_hash"  # Would compute from stored file
    
    return {
        "document_id": document_id,
        "stored_hash": stored_hash,
        "current_hash": current_hash,
        "integrity_verified": stored_hash == current_hash
    }