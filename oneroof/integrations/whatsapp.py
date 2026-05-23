"""
WhatsApp Integration Module for OneRoof
Maps WhatsApp messages to compliance requests, stores evidence, maintains structured communication.
"""

from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import select

from oneroof.core.database import AsyncSessionLocal
from oneroof.api.models import (
    Workspace, Client, ClientUser, ComplianceItem, 
    DocumentRequest, Communication, AuditLog
)


class WhatsAppMessageType(str, Enum):
    """Types of WhatsApp messages."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"


@dataclass
class WhatsAppMessage:
    """Structured WhatsApp message data."""
    message_id: str
    from_number: str
    to_number: str
    message_type: WhatsAppMessageType
    content: str
    timestamp: datetime
    media_url: Optional[str] = None
    media_caption: Optional[str] = None


# Keywords for compliance mapping
COMPLIANCE_KEYWORDS = {
    "gstr": "gst", "gst": "gst", "tds": "tds", "return": "income_tax",
    "filing": "income_tax", "roc": "roc", "annual": "income_tax", "audit": "income_tax",
}

DOCUMENT_KEYWORDS = [
    "uploading", "upload", "attached", "sending", "bank statement", 
    "sales register", "purchase register", "invoice", "receipt", " challan", "form",
    "itr", "balance sheet", "p&l", "audit report",
]


class WhatsAppIntegration:
    """WhatsApp Business API Integration - Captures and maps messages to compliance context."""
    
    @staticmethod
    async def process_incoming_message(message: WhatsAppMessage) -> dict:
        """Process incoming WhatsApp message, map to compliance item, create communication."""
        async with AsyncSessionLocal() as db:
            # Find client by phone number
            result = await db.execute(
                select(ClientUser).where(ClientUser.phone == message.from_number)
            )
            client_user = result.scalar_one_or_none()
            
            if not client_user:
                return {"success": False, "error": "Client user not found", "message_id": message.message_id}
            
            # Get workspace
            result = await db.execute(
                select(Workspace).where(Workspace.client_id == client_user.client_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                return {"success": False, "error": "Workspace not found", "message_id": message.message_id}
            
            # Find related compliance item
            compliance_item = await WhatsAppIntegration._find_related_compliance(
                db, workspace.id, message.content
            )
            
            # Find related document request
            document_request = await WhatsAppIntegration._find_related_document_request(
                db, compliance_item, message.content
            )
            
            # Determine communication type
            comm_type = WhatsAppIntegration._determine_communication_type(message)
            
            # Create structured communication
            communication = Communication(
                workspace_id=workspace.id,
                compliance_item_id=compliance_item.id if compliance_item else None,
                communication_type=comm_type,
                message=WhatsAppIntegration._format_message_content(message),
                sender_type="client_user",
                sender_id=client_user.id,
            )
            db.add(communication)
            
            # Create audit log
            audit = AuditLog(
                client_user_id=client_user.id,
                action="whatsapp_message",
                resource_type="communication",
                workspace_id=workspace.id,
                details={
                    "message_id": message.message_id,
                    "message_type": message.message_type.value,
                    "compliance_item_id": compliance_item.id if compliance_item else None,
                    "mapped": compliance_item is not None,
                }
            )
            db.add(audit)
            
            await db.commit()
            
            return {
                "success": True,
                "message_id": message.message_id,
                "workspace_id": workspace.id,
                "compliance_item_id": compliance_item.id if compliance_item else None,
                "communication_id": communication.id,
            }
    
    @staticmethod
    async def _find_related_compliance(db, workspace_id: int, content: str) -> Optional[ComplianceItem]:
        """Find compliance item related to message content."""
        content_lower = content.lower()
        
        # Check for compliance type keywords
        compliance_type = None
        for keyword, ctype in COMPLIANCE_KEYWORDS.items():
            if keyword in content_lower:
                compliance_type = ctype
                break
        
        # Find matching compliance item
        result = await db.execute(
            select(ComplianceItem).where(
                ComplianceItem.workspace_id == workspace_id,
                ComplianceItem.status.in_(["pending", "in_progress"])
            )
        )
        items = result.scalars().all()
        
        for item in items:
            if compliance_type and item.compliance_type == compliance_type:
                return item
            if any(k in item.name.lower() for k in COMPLIANCE_KEYWORDS.keys()):
                return item
        
        return None
    
    @staticmethod
    async def _find_related_document_request(db, compliance_item, content: str) -> Optional[DocumentRequest]:
        """Find document request related to message content."""
        if not compliance_item:
            return None
        
        result = await db.execute(
            select(DocumentRequest).where(
                DocumentRequest.compliance_item_id == compliance_item.id,
                DocumentRequest.status.in_(["pending", "incomplete"])
            )
        )
        requests = result.scalars().all()
        
        for req in requests:
            req_lower = req.title.lower()
            if any(kw in req_lower and kw in content.lower() for kw in DOCUMENT_KEYWORDS):
                return req
        
        return None
    
    @staticmethod
    def _determine_communication_type(message: WhatsAppMessage) -> str:
        """Determine communication type from message."""
        content_lower = message.content.lower()
        
        if any(w in content_lower for w in ["uploading", "upload", "attached", "sending"]):
            return "upload"
        elif any(w in content_lower for w in ["approved", "ok", "yes", "done"]):
            return "approval"
        elif any(w in content_lower for w in ["filed", "submitted"]):
            return "filing"
        return "comment"
    
    @staticmethod
    def _format_message_content(message: WhatsAppMessage) -> str:
        """Format message content for storage."""
        content = f"[WhatsApp - {message.message_type.value}]"
        if message.media_url:
            content += f"\nMedia: {message.media_url}"
            if message.media_caption:
                content += f"\nCaption: {message.media_caption}"
        content += f"\n{message.content}"
        return content


class WhatsAppWebhookHandler:
    """Handles WhatsApp Business API webhooks."""
    
    @staticmethod
    async def handle_message_webhook(payload: dict) -> dict:
        """Process incoming webhook from WhatsApp Business API."""
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return {"processed": 0}
            
            processed = 0
            for msg in messages:
                message = WhatsAppMessage(
                    message_id=msg.get("id", ""),
                    from_number=msg.get("from", ""),
                    to_number=msg.get("to", ""),
                    message_type=WhatsAppMessageType(msg.get("type", "text")),
                    content=msg.get("text", {}).get("body", ""),
                    timestamp=datetime.fromtimestamp(int(msg.get("timestamp", 0))),
                )
                
                result = await WhatsAppIntegration.process_incoming_message(message)
                if result.get("success"):
                    processed += 1
            
            return {"processed": processed}
        except Exception as e:
            return {"error": str(e), "processed": 0}