"""
Document management with encryption, versioning, and secure storage.
"""

import hashlib
import secrets
import os
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path

from oneroof.core.config import settings


class DocumentEncryption:
    """Handle document encryption and decryption."""
    
    @staticmethod
    def encrypt_file(content: bytes) -> bytes:
        """
        Encrypt file content.
        In production, use proper encryption (Fernet/AES).
        For now, this is a placeholder that can be enhanced.
        """
        # TODO: Implement proper encryption
        # from cryptography.fernet import Fernet
        # key = settings.ENCRYPTION_KEY.encode()
        # f = Fernet(key)
        # return f.encrypt(content)
        return content
    
    @staticmethod
    def decrypt_file(encrypted_content: bytes) -> bytes:
        """Decrypt file content."""
        # TODO: Implement proper decryption
        return encrypted_content
    
    @staticmethod
    def compute_hash(content: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def verify_integrity(content: bytes, expected_hash: str) -> bool:
        """Verify file content matches expected hash."""
        actual_hash = DocumentEncryption.compute_hash(content)
        return actual_hash == expected_hash


class DocumentStorage:
    """Handle document storage and retrieval."""
    
    @staticmethod
    def get_storage_path(workspace_id: int, file_name: str) -> Path:
        """Generate storage path for a document."""
        # Create directory structure: uploads/{workspace_id}/{date}/{unique_id}/{filename}
        date_str = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = secrets.token_urlsafe(16)
        
        base_path = Path(settings.UPLOAD_DIR) / str(workspace_id) / date_str / unique_id
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_name = "".join(c for c in file_name if c.isalnum() or c in ".-_ ")
        return base_path / safe_name
    
    @staticmethod
    async def save_document(
        workspace_id: int,
        file_name: str,
        content: bytes
    ) -> Tuple[str, str]:
        """
        Save document to storage.
        Returns (file_path, file_hash)
        """
        # Compute hash before encryption
        file_hash = DocumentEncryption.compute_hash(content)
        
        # Get storage path
        file_path = DocumentStorage.get_storage_path(workspace_id, file_name)
        
        # Encrypt content
        encrypted_content = DocumentEncryption.encrypt_file(content)
        
        # Write to disk
        with open(file_path, 'wb') as f:
            f.write(encrypted_content)
        
        return str(file_path), file_hash
    
    @staticmethod
    async def get_document(file_path: str) -> Optional[bytes]:
        """Retrieve and decrypt document."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            with open(path, 'rb') as f:
                encrypted_content = f.read()
            
            return DocumentEncryption.decrypt_file(encrypted_content)
        except Exception:
            return None
    
    @staticmethod
    async def delete_document(file_path: str) -> bool:
        """Delete document from storage."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
            return True
        except Exception:
            return False


class DocumentVersionManager:
    """Manage document versions - no overwriting."""
    
    @staticmethod
    async def create_version(
        workspace_id: int,
        request_id: Optional[int],
        compliance_item_id: Optional[int],
        original_document_id: Optional[int],
        file_name: str,
        content: bytes,
        category: str,
        sub_category: Optional[str] = None,
        visibility: str = "client",
        uploaded_by_user_id: Optional[int] = None,
        uploaded_by_client_user_id: Optional[int] = None,
    ) -> dict:
        """
        Create a new version of a document.
        Marks previous versions as not latest.
        """
        from oneroof.core.database import AsyncSessionLocal
        from oneroof.api.models import Document
        
        async with AsyncSessionLocal() as db:
            # Check if document with same name exists
            from sqlalchemy import select, and_
            result = await db.execute(
                select(Document)
                .where(
                    Document.workspace_id == workspace_id,
                    Document.name == file_name,
                    Document.is_latest == True
                )
            )
            existing_doc = result.scalar_one_or_none()
            
            # Determine version number
            if existing_doc:
                new_version = existing_doc.version + 1
                existing_doc.is_latest = False
            else:
                new_version = 1
            
            # Save file
            file_path, file_hash = await DocumentStorage.save_document(
                workspace_id, file_name, content
            )
            
            # Create document record
            document = Document(
                workspace_id=workspace_id,
                request_id=request_id,
                compliance_item_id=compliance_item_id,
                name=file_name,
                file_path=file_path,
                file_size=len(content),
                mime_type=DocumentVersionManager._get_mime_type(file_name),
                file_hash=file_hash,
                version=new_version,
                parent_id=existing_doc.id if existing_doc else None,
                category=category,
                sub_category=sub_category,
                visibility=visibility,
                uploaded_by_user_id=uploaded_by_user_id,
                uploaded_by_client_user_id=uploaded_by_client_user_id,
                is_latest=True,
            )
            db.add(document)
            
            await db.commit()
            await db.refresh(document)
            
            return {
                "id": document.id,
                "name": document.name,
                "version": document.version,
                "file_hash": document.file_hash,
                "created_at": document.created_at.isoformat(),
            }
    
    @staticmethod
    def _get_mime_type(file_name: str) -> str:
        """Determine MIME type from file extension."""
        ext = file_name.split(".")[-1].lower() if "." in file_name else ""
        
        mime_types = {
            "pdf": "application/pdf",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "txt": "text/plain",
            "csv": "text/csv",
        }
        
        return mime_types.get(ext, "application/octet-stream")
    
    @staticmethod
    async def get_version_history(document_id: int) -> List[dict]:
        """Get all versions of a document."""
        from oneroof.core.database import AsyncSessionLocal
        from oneroof.api.models import Document
        from sqlalchemy import select, or_, and_
        
        async with AsyncSessionLocal() as db:
            # Get the document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                return []
            
            # Find root document (if this is a child)
            if doc.parent_id:
                root_id = doc.parent_id
            else:
                root_id = doc.id
            
            # Get all versions
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
            
            return [
                {
                    "id": v.id,
                    "version": v.version,
                    "name": v.name,
                    "created_at": v.created_at.isoformat(),
                    "uploaded_by": v.uploaded_by_user_id or v.uploaded_by_client_user_id,
                    "file_size": v.file_size,
                }
                for v in versions
            ]
    
    @staticmethod
    async def restore_version(version_id: int, restored_by_user_id: int) -> bool:
        """Restore a previous version as the new latest."""
        from oneroof.core.database import AsyncSessionLocal
        from oneroof.api.models import Document
        
        async with AsyncSessionLocal() as db:
            # Get the version to restore
            result = await db.execute(
                select(Document).where(Document.id == version_id)
            )
            old_version = result.scalar_one_or_none()
            
            if not old_version:
                return False
            
            # Mark current latest as not latest
            result = await db.execute(
                select(Document)
                .where(
                    Document.workspace_id == old_version.workspace_id,
                    Document.name == old_version.name,
                    Document.is_latest == True
                )
            )
            current_latest = result.scalar_one_or_none()
            
            if current_latest:
                current_latest.is_latest = False
            
            # Mark old version as latest
            old_version.is_latest = True
            
            await db.commit()
            return True


class WatermarkService:
    """Add watermarks to downloaded sensitive documents."""
    
    @staticmethod
    async def create_watermark(
        document_id: int,
        user_id: Optional[int] = None,
        client_user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """Create watermark record for document download."""
        from oneroof.core.database import AsyncSessionLocal
        from oneroof.api.models import Watermark, Document
        
        async with AsyncSessionLocal() as db:
            # Generate watermark text
            from oneroof.api.models import User, ClientUser
            
            user_info = ""
            if user_id:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    user_info = f"{user.first_name} {user.last_name}"
            elif client_user_id:
                result = await db.execute(select(ClientUser).where(ClientUser.id == client_user_id))
                client_user = result.scalar_one_or_none()
                if client_user:
                    user_info = f"{client_user.first_name} {client_user.last_name}"
            
            watermark_text = f"Downloaded by: {user_info} | Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | IP: {ip_address or 'Unknown'}"
            
            watermark = Watermark(
                document_id=document_id,
                downloaded_by_user_id=user_id,
                downloaded_by_client_user_id=client_user_id,
                watermark_text=watermark_text,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(watermark)
            await db.commit()
            
            return {
                "id": watermark.id,
                "watermark_text": watermark_text,
                "created_at": watermark.created_at.isoformat(),
            }