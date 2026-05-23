"""
Failsafe Mechanism Tests
"""

import pytest
from datetime import datetime, timedelta


class TestDeadlineProtection:
    """Test deadline protection mechanisms."""
    
    def test_risk_level_low(self):
        """Test low risk level calculation."""
        from oneroof.compliance.failsafe import DeadlineProtection, _get_risk_recommendation
        
        risk_level = _get_risk_recommendation("low")
        assert "on track" in risk_level.lower()
    
    def test_risk_level_critical(self):
        """Test critical risk level calculation."""
        from oneroof.compliance.failsafe import _get_risk_recommendation
        
        risk_level = _get_risk_recommendation("critical")
        assert "immediate" in risk_level.lower() or "urgent" in risk_level.lower()


class TestDuplicateProtection:
    """Test duplicate filing protection."""
    
    def test_collect_issues_empty(self):
        """Test issue collection with no issues."""
        from oneroof.compliance.failsafe import _collect_issues
        
        issues = _collect_issues(
            duplicate_check=(False, None),
            approval_check={"all_required_approved": True, "approvals": []},
            document_check={"complete": True}
        )
        
        assert len(issues) == 0
    
    def test_collect_issues_with_problems(self):
        """Test issue collection with issues."""
        from oneroof.compliance.failsafe import _collect_issues
        
        issues = _collect_issues(
            duplicate_check=(True, {"name": "GSTR-1"}),
            approval_check={
                "all_required_approved": False,
                "approvals": [{"type": "client_approval", "status": "missing"}]
            },
            document_check={"complete": False, "pending_titles": ["Sales Register"]}
        )
        
        assert len(issues) >= 1


class TestSmartCategorization:
    """Test smart document categorization."""
    
    def test_categorize_sales_document(self):
        """Test categorization of sales document."""
        from oneroof.ai.engine import SmartCategorization
        
        result = SmartCategorization.categorize("Sales_Register_May_2026.xlsx")
        
        assert result["category"] == "sales"
        assert result["confidence"] > 0
    
    def test_categorize_bank_statement(self):
        """Test categorization of bank statement."""
        from oneroof.ai.engine import SmartCategorization
        
        result = SmartCategorization.categorize("Bank_Statement.pdf")
        
        assert result["category"] == "bank"
    
    def test_categorize_unknown_document(self):
        """Test categorization of unknown document type."""
        from oneroof.ai.engine import SmartCategorization
        
        result = SmartCategorization.categorize("random_file.xyz")
        
        assert result["category"] == "other"
    
    def test_categorize_with_content(self):
        """Test categorization with content preview."""
        from oneroof.ai.engine import SmartCategorization
        
        result = SmartCategorization.categorize(
            "document.pdf",
            "Quarterly TDS return Form 27Q"
        )
        
        assert result["category"] == "returns"