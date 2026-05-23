"""
Notification system for reminders, alerts, and user communication.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from enum import Enum

from oneroof.core.database import AsyncSessionLocal
from oneroof.api.models import Notification, User, ClientUser, ComplianceItem, Workspace


class NotificationType(str, Enum):
    """Types of notifications."""
    REMINDER = "reminder"
    APPROVAL_REQUEST = "approval_request"
    STATUS_CHANGE = "status_change"
    DEADLINE_WARNING = "deadline_warning"
    OVERDUE_ALERT = "overdue_alert"
    DOCUMENT_UPLOADED = "document_uploaded"
    COMMENT_ADDED = "comment_added"
    NOTICE_RECEIVED = "notice_received"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationService:
    """Service for creating and managing notifications."""
    
    @staticmethod
    async def create_notification(
        user_id: Optional[int] = None,
        client_user_id: Optional[int] = None,
        notification_type: NotificationType = NotificationType.SYSTEM,
        title: str = "",
        message: str = "",
        link: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> Notification:
        """Create a new notification."""
        async with AsyncSessionLocal() as db:
            notification = Notification(
                user_id=user_id,
                client_user_id=client_user_id,
                notification_type=notification_type.value,
                title=title,
                message=message,
                link=link,
            )
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            
            return notification
    
    @staticmethod
    async def notify_deadline_reminder(
        compliance_item: ComplianceItem,
        days_until: int,
    ) -> List[Notification]:
        """Send deadline reminder notifications."""
        notifications = []
        
        async with AsyncSessionLocal() as db:
            # Notify assigned staff
            if compliance_item.assigned_to_user_id:
                notification = await NotificationService.create_notification(
                    user_id=compliance_item.assigned_to_user_id,
                    notification_type=NotificationType.REMINDER,
                    title=f"Deadline Reminder: {compliance_item.name}",
                    message=f"Due in {days_until} days on {compliance_item.due_date.strftime('%d %b %Y')}",
                    link=f"/compliance/{compliance_item.id}",
                    priority=NotificationPriority.HIGH if days_until <= 2 else NotificationPriority.NORMAL,
                )
                notifications.append(notification)
            
            # Notify client admin
            result = await db.execute(
                select(Workspace).where(Workspace.id == compliance_item.workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if workspace:
                result = await db.execute(
                    select(ClientUser)
                    .where(ClientUser.client_id == workspace.client_id, ClientUser.role == "client_admin")
                )
                client_admin = result.scalar_one_or_none()
                
                if client_admin:
                    notification = await NotificationService.create_notification(
                        client_user_id=client_admin.id,
                        notification_type=NotificationType.REMINDER,
                        title=f"Action Required: {compliance_item.name}",
                        message="Please upload required documents before the deadline.",
                        link=f"/workspace/{workspace.id}/compliance/{compliance_item.id}",
                        priority=NotificationPriority.HIGH if days_until <= 2 else NotificationPriority.NORMAL,
                    )
                    notifications.append(notification)
            
            return notifications
    
    @staticmethod
    async def notify_approval_request(
        compliance_item_id: int,
        approval_type: str,
        requested_from_user_id: Optional[int] = None,
        requested_from_client_user_id: Optional[int] = None,
    ) -> Notification:
        """Notify about a pending approval request."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ComplianceItem).where(ComplianceItem.id == compliance_item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return None
            
            title = f"Approval Request: {item.name}"
            message = f"Your approval is required for {item.name} ({item.period})"
            link = f"/compliance/{compliance_item_id}/approvals"
            
            return await NotificationService.create_notification(
                user_id=requested_from_user_id,
                client_user_id=requested_from_client_user_id,
                notification_type=NotificationType.APPROVAL_REQUEST,
                title=title,
                message=message,
                link=link,
                priority=NotificationPriority.HIGH,
            )
    
    @staticmethod
    async def notify_status_change(
        compliance_item_id: int,
        old_status: str,
        new_status: str,
        changed_by_user_id: int,
    ) -> List[Notification]:
        """Notify about compliance item status change."""
        notifications = []
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ComplianceItem).where(ComplianceItem.id == compliance_item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return []
            
            # Notify assigned user if different from changer
            if item.assigned_to_user_id and item.assigned_to_user_id != changed_by_user_id:
                notification = await NotificationService.create_notification(
                    user_id=item.assigned_to_user_id,
                    notification_type=NotificationType.STATUS_CHANGE,
                    title=f"Status Updated: {item.name}",
                    message=f"Status changed from '{old_status}' to '{new_status}'",
                    link=f"/compliance/{compliance_item_id}",
                )
                notifications.append(notification)
            
            # Notify client
            result = await db.execute(
                select(Workspace).where(Workspace.id == item.workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if workspace:
                result = await db.execute(
                    select(ClientUser)
                    .where(ClientUser.client_id == workspace.client_id, ClientUser.role == "client_admin")
                )
                client_admin = result.scalar_one_or_none()
                
                if client_admin:
                    notification = await NotificationService.create_notification(
                        client_user_id=client_admin.id,
                        notification_type=NotificationType.STATUS_CHANGE,
                        title=f"Filing Update: {item.name}",
                        message=f"Status: {new_status}",
                        link=f"/workspace/{workspace.id}/compliance/{compliance_item_id}",
                    )
                    notifications.append(notification)
            
            return notifications
    
    @staticmethod
    async def notify_overdue_alert(
        compliance_item_id: int,
    ) -> List[Notification]:
        """Send overdue alert notifications."""
        notifications = []
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ComplianceItem).where(ComplianceItem.id == compliance_item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return []
            
            days_overdue = (datetime.utcnow() - item.due_date).days
            
            # Notify assigned staff with urgent priority
            if item.assigned_to_user_id:
                notification = await NotificationService.create_notification(
                    user_id=item.assigned_to_user_id,
                    notification_type=NotificationType.OVERDUE_ALERT,
                    title=f"OVERDUE: {item.name}",
                    message=f"This item is {days_overdue} days overdue! Immediate action required.",
                    link=f"/compliance/{compliance_item_id}",
                    priority=NotificationPriority.URGENT,
                )
                notifications.append(notification)
            
            return notifications
    
    @staticmethod
    async def get_user_notifications(
        user_id: Optional[int] = None,
        client_user_id: Optional[int] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[dict]:
        """Get notifications for a user."""
        async with AsyncSessionLocal() as db:
            if user_id:
                result = await db.execute(
                    select(Notification)
                    .where(Notification.user_id == user_id)
                    .order_by(Notification.created_at.desc())
                    .limit(limit)
                )
            elif client_user_id:
                result = await db.execute(
                    select(Notification)
                    .where(Notification.client_user_id == client_user_id)
                    .order_by(Notification.created_at.desc())
                    .limit(limit)
                )
            else:
                return []
            
            notifications = result.scalars().all()
            
            if unread_only:
                notifications = [n for n in notifications if not n.is_read]
            
            return [
                {
                    "id": n.id,
                    "type": n.notification_type,
                    "title": n.title,
                    "message": n.message,
                    "link": n.link,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in notifications
            ]
    
    @staticmethod
    async def mark_as_read(notification_id: int) -> bool:
        """Mark a notification as read."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notification).where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()
            
            if notification:
                notification.is_read = True
                await db.commit()
                return True
            
            return False
    
    @staticmethod
    async def mark_all_as_read(
        user_id: Optional[int] = None,
        client_user_id: Optional[int] = None,
    ) -> int:
        """Mark all notifications as read for a user."""
        async with AsyncSessionLocal() as db:
            if user_id:
                result = await db.execute(
                    select(Notification)
                    .where(Notification.user_id == user_id, Notification.is_read == False)
                )
            elif client_user_id:
                result = await db.execute(
                    select(Notification)
                    .where(Notification.client_user_id == client_user_id, Notification.is_read == False)
                )
            else:
                return 0
            
            notifications = result.scalars().all()
            count = len(notifications)
            
            for n in notifications:
                n.is_read = True
            
            await db.commit()
            return count
    
    @staticmethod
    async def get_unread_count(
        user_id: Optional[int] = None,
        client_user_id: Optional[int] = None,
    ) -> int:
        """Get count of unread notifications."""
        async with AsyncSessionLocal() as db:
            if user_id:
                result = await db.execute(
                    select(func.count(Notification.id))
                    .where(Notification.user_id == user_id, Notification.is_read == False)
                )
            elif client_user_id:
                result = await db.execute(
                    select(func.count(Notification.id))
                    .where(Notification.client_user_id == client_user_id, Notification.is_read == False)
                )
            else:
                return 0
            
            return result.scalar() or 0


# Import for count
from sqlalchemy import func