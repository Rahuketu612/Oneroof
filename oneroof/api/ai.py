"""
AI Endpoints - Notice summarization, anomaly detection, risk alerts.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from oneroof.core.database import get_db
from oneroof.core.security import get_current_active_user
from oneroof.api.models import User
from oneroof.ai.engine import (
    NoticeSummarizer, AnomalyDetection, MissingDocumentPredictor,
    ComplianceRiskAlerts, AIGeneratedSummary
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/summarize-notice/{notice_id}")
async def summarize_notice(
    notice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    AI-powered summarization of a compliance notice.
    Extracts key points, action items, and risk level.
    """
    try:
        summary: AIGeneratedSummary = await NoticeSummarizer.summarize(notice_id)
        return {
            "success": True,
            "notice_id": notice_id,
            "summary": summary.summary,
            "key_points": summary.key_points,
            "action_items": summary.action_items,
            "risk_level": summary.risk_level,
            "confidence": summary.confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detect-anomalies")
async def detect_anomalies(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Detect anomalies in compliance data.
    Returns list of unusual patterns, missing data, inconsistencies.
    """
    try:
        anomalies = await AnomalyDetection.detect_compliance_anomalies(current_user.firm_id)
        return {
            "success": True,
            "firm_id": current_user.firm_id,
            "anomalies": anomalies,
            "total_found": len(anomalies),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict-missing-documents/{compliance_item_id}")
async def predict_missing_documents(
    compliance_item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Predict which documents are likely missing for a compliance item.
    Based on historical patterns and current status.
    """
    try:
        predictions = await MissingDocumentPredictor.predict_missing(compliance_item_id)
        return {
            "success": True,
            "compliance_item_id": compliance_item_id,
            "predictions": predictions,
            "high_risk_count": len([p for p in predictions if p.get("risk") == "high"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-alerts")
async def get_risk_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get compliance risk alerts for the firm.
    Includes overdue items, upcoming deadlines, high-risk clients.
    """
    try:
        alerts = await ComplianceRiskAlerts.generate_alerts(current_user.firm_id)
        return {
            "success": True,
            "firm_id": current_user.firm_id,
            "alerts": [
                {
                    "type": a.alert_type,
                    "severity": a.severity,
                    "message": a.message,
                    "affected_items": a.affected_items,
                    "recommendation": a.recommendation,
                }
                for a in alerts
            ],
            "critical_count": len([a for a in alerts if a.severity == "critical"]),
            "high_count": len([a for a in alerts if a.severity == "high"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-insights")
async def get_dashboard_insights(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get AI-powered dashboard insights.
    Combines multiple AI features for a quick overview.
    """
    try:
        # Get all insights in parallel would be ideal, but for now sequential
        alerts = await ComplianceRiskAlerts.generate_alerts(current_user.firm_id)
        anomalies = await AnomalyDetection.detect_compliance_anomalies(current_user.firm_id)
        
        return {
            "success": True,
            "overview": {
                "risk_alerts": len(alerts),
                "anomalies": len(anomalies),
                "health_score": _calculate_health_score(alerts, anomalies),
            },
            "top_concerns": [
                {
                    "type": "alert",
                    "severity": a.severity,
                    "message": a.message,
                }
                for a in alerts[:3]
            ] + [
                {
                    "type": "anomaly",
                    "severity": a.get("severity", "medium"),
                    "message": a.get("message", ""),
                }
                for a in anomalies[:3]
            ],
            "recommendations": _generate_recommendations(alerts, anomalies),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_health_score(alerts, anomalies) -> int:
    """Calculate overall health score (0-100)."""
    score = 100
    critical_alerts = len([a for a in alerts if a.severity == "critical"])
    high_alerts = len([a for a in alerts if a.severity == "high"])
    critical_anomalies = len([a for a in anomalies if a.get("severity") == "critical"])
    
    score -= (critical_alerts * 20)
    score -= (high_alerts * 5)
    score -= (critical_anomalies * 10)
    
    return max(0, min(100, score))


def _generate_recommendations(alerts, anomalies) -> list:
    """Generate actionable recommendations based on alerts and anomalies."""
    recommendations = []
    
    if any(a.severity == "critical" for a in alerts):
        recommendations.append({
            "priority": "urgent",
            "action": "Review and address critical risk alerts immediately",
        })
    
    if any(a.get("type") == "overdue_high_priority" for a in anomalies):
        recommendations.append({
            "priority": "high",
            "action": "Escalate overdue high-priority items to partner",
        })
    
    if len(alerts) > 5:
        recommendations.append({
            "priority": "medium",
            "action": "Schedule weekly review meeting to address compliance items",
        })
    
    if not recommendations:
        recommendations.append({
            "priority": "info",
            "action": "Continue current monitoring approach",
        })
    
    return recommendations