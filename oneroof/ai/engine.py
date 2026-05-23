"""
AI Layer for OneRoof - Notice summarization, anomaly detection, risk prediction.
"""

from datetime import datetime, timedelta
from typing import Optional, List
import re
from dataclasses import dataclass

from sqlalchemy import select, func, and_

from oneroof.core.database import AsyncSessionLocal
from oneroof.api.models import Notice, ComplianceItem, DocumentRequest, Workspace, Client


@dataclass
class AIGeneratedSummary:
    summary: str
    key_points: List[str]
    action_items: List[str]
    risk_level: str
    confidence: float


@dataclass
class ComplianceRiskAlert:
    alert_type: str
    severity: str
    message: str
    affected_items: List[int]
    recommendation: str


class NoticeSummarizer:
    """AI-powered notice summarization."""
    
    NOTICE_TYPES = {
        "gst": ["goods and services tax", "gst", "central tax"],
        "tds": ["tax deducted at source", "tds", "form 27q"],
        "income_tax": ["income tax", "itr", "a.y.", "assessment year"],
        "roc": ["registrar of companies", "roc", "companies act"],
    }
    
    @staticmethod
    async def summarize(notice_id: int) -> AIGeneratedSummary:
        """Generate AI summary of a notice."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Notice).where(Notice.id == notice_id))
            notice = result.scalar_one_or_none()
            
            if not notice:
                return AIGeneratedSummary("Notice not found", [], [], "unknown", 0.0)
            
            # Generate summary components
            notice_type = NoticeSummarizer._identify_type(notice.description or notice.title)
            risk_level = NoticeSummarizer._calculate_risk(notice)
            actions = NoticeSummarizer._generate_actions(notice)
            key_points = NoticeSummarizer._extract_points(notice.description or "")
            
            summary = f"{notice_type.upper()} Notice from {notice.source}\n"
            summary += f"Received: {notice.notice_date.strftime('%d %b %Y')}\n"
            if notice.due_date:
                days = (notice.due_date - datetime.utcnow()).days
                summary += f"Deadline: {abs(days)} days {'ago' if days < 0 else 'remaining'}"
            
            return AIGeneratedSummary(summary, key_points, actions, risk_level, 0.85)
    
    @staticmethod
    def _identify_type(text: str) -> str:
        text_lower = text.lower()
        for ntype, keywords in NoticeSummarizer.NOTICE_TYPES.items():
            if any(kw in text_lower for kw in keywords):
                return ntype
        return "other"
    
    @staticmethod
    def _calculate_risk(notice: Notice) -> str:
        score = 0
        if notice.due_date:
            days = (notice.due_date - datetime.utcnow()).days
            if days < 0: score += 50
            elif days < 7: score += 30
        
        desc = (notice.description or "").lower()
        if any(w in desc for w in ["urgent", "final", "cancellation"]):
            score += 30
        
        return "critical" if score >= 70 else "high" if score >= 40 else "medium" if score >= 20 else "low"
    
    @staticmethod
    def _generate_actions(notice: Notice) -> List[str]:
        actions = ["Prepare response"]
        if notice.due_date:
            days = (notice.due_date - datetime.utcnow()).days
            if days < 0:
                actions.insert(0, "URGENT: Deadline passed")
            else:
                actions.append(f"Due in {days} days")
        return actions[:3]
    
    @staticmethod
    def _extract_points(text: str) -> List[str]:
        points = []
        for para in text.split('\n'):
            para = para.strip()
            if 20 < len(para) < 150 and any(kw in para.lower() for kw in ["require", "must", "shall", "demand"]):
                points.append(para[:100] + "...")
        return points[:5]


class AnomalyDetection:
    """Detects anomalies in compliance data."""
    
    @staticmethod
    async def detect_compliance_anomalies(firm_id: int) -> List[dict]:
        anomalies = []
        async with AsyncSessionLocal() as db:
            # Check overdue high-priority items
            result = await db.execute(
                select(ComplianceItem, Client.name)
                .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
                .join(Client, Workspace.client_id == Client.id)
                .where(Client.firm_id == firm_id, ComplianceItem.priority == "high")
                .where(ComplianceItem.due_date < datetime.utcnow())
                .where(ComplianceItem.status.notin_(["filed", "completed"]))
            )
            for item, client_name in result.all():
                anomalies.append({
                    "type": "overdue_high_priority",
                    "severity": "critical",
                    "item_id": item.id,
                    "client_name": client_name,
                    "message": f"High priority overdue: {item.name}",
                })
            
            # Check for stale pending items
            result = await db.execute(
                select(ComplianceItem)
                .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
                .join(Client, Workspace.client_id == Client.id)
                .where(
                    Client.firm_id == firm_id,
                    ComplianceItem.status == "pending",
                    ComplianceItem.created_at < datetime.utcnow() - timedelta(days=30)
                )
            )
            for item in result.scalars().all():
                anomalies.append({
                    "type": "stale_pending",
                    "severity": "medium",
                    "item_id": item.id,
                    "message": f"Pending since {item.created_at.strftime('%d %b %Y')}: {item.name}",
                })
        return anomalies


class MissingDocumentPredictor:
    """Predicts missing documents based on compliance patterns."""
    
    @staticmethod
    async def predict_missing(compliance_item_id: int) -> List[dict]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ComplianceItem).where(ComplianceItem.id == compliance_item_id)
            )
            item = result.scalar_one_or_none()
            if not item:
                return []
            
            result = await db.execute(
                select(DocumentRequest).where(
                    DocumentRequest.compliance_item_id == compliance_item_id,
                    DocumentRequest.status.in_(["pending", "incomplete"])
                )
            )
            predictions = []
            for req in result.scalars().all():
                days = (item.due_date - datetime.utcnow()).days
                predictions.append({
                    "document": req.title,
                    "risk": "high" if days < 5 else "medium",
                    "days_left": days,
                })
            return predictions


class ComplianceRiskAlerts:
    """Generates compliance risk alerts."""
    
    @staticmethod
    async def generate_alerts(firm_id: int) -> List[ComplianceRiskAlert]:
        alerts = []
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            
            # Overdue items
            result = await db.execute(
                select(func.count(ComplianceItem.id))
                .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
                .join(Client, Workspace.client_id == Client.id)
                .where(Client.firm_id == firm_id, ComplianceItem.due_date < now)
                .where(ComplianceItem.status.notin_(["filed", "completed"]))
            )
            overdue_count = result.scalar() or 0
            if overdue_count > 0:
                alerts.append(ComplianceRiskAlert(
                    alert_type="overdue",
                    severity="critical",
                    message=f"{overdue_count} compliance items overdue",
                    affected_items=[],
                    recommendation="Immediate action required",
                ))
            
            # Due this week
            result = await db.execute(
                select(func.count(ComplianceItem.id))
                .join(Workspace, ComplianceItem.workspace_id == Workspace.id)
                .join(Client, Workspace.client_id == Client.id)
                .where(
                    Client.firm_id == firm_id,
                    ComplianceItem.due_date.between(now, now + timedelta(days=7)),
                    ComplianceItem.status == "pending"
                )
            )
            due_count = result.scalar() or 0
            if due_count > 0:
                alerts.append(ComplianceRiskAlert(
                    alert_type="upcoming",
                    severity="high",
                    message=f"{due_count} items due within 7 days",
                    affected_items=[],
                    recommendation="Prioritize for timely filing",
                ))
        
        return alerts


class SmartCategorization:
    """Smart document categorization."""
    
    CATEGORIES = {
        "sales": ["sales", "outward", "invoice", "b2b", "export"],
        "purchase": ["purchase", "inward", "expense", "debit note"],
        "bank": ["bank", "statement", "neft", "rtgs"],
        "returns": ["return", "gstr", "tds", "itr", "filing"],
        "legal": ["agreement", "contract", "deed", "moa", "aoa"],
        "audit": ["audit", "review", "certificate", "report"],
    }
    
    @staticmethod
    def categorize(filename: str, content: str = "") -> dict:
        text = (filename + " " + content).lower()
        scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in SmartCategorization.CATEGORIES.items()}
        best = max(scores, key=scores.get) if scores else "other"
        return {"category": best, "confidence": scores.get(best, 0) / 3}