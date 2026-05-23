"""
Workflow Engine Tests
"""

import pytest
from datetime import datetime, timedelta


class TestWorkflowEngine:
    """Test compliance workflow engine."""
    
    def test_calculate_monthly_due_date(self):
        """Test due date calculation for monthly compliance."""
        from oneroof.compliance.workflow import ComplianceWorkflowEngine
        
        now = datetime(2026, 5, 15)
        due_date = ComplianceWorkflowEngine._calculate_due_date("monthly", now)
        
        assert due_date.month == 6  # June
        assert due_date.day == 20
        assert due_date.year == 2026
    
    def test_calculate_quarterly_due_date(self):
        """Test due date calculation for quarterly compliance."""
        from oneroof.compliance.workflow import ComplianceWorkflowEngine
        
        now = datetime(2026, 3, 15)
        due_date = ComplianceWorkflowEngine._calculate_due_date("quarterly", now)
        
        assert due_date.month == 3
        assert due_date.day == 20
    
    def test_calculate_yearly_due_date(self):
        """Test due date calculation for yearly compliance."""
        from oneroof.compliance.workflow import ComplianceWorkflowEngine
        
        now = datetime(2026, 5, 15)
        due_date = ComplianceWorkflowEngine._calculate_due_date("yearly", now)
        
        assert due_date.month == 9  # September
        assert due_date.day == 30
    
    def test_get_default_workflow_steps(self):
        """Test default workflow steps generation."""
        from oneroof.compliance.workflow import ComplianceWorkflowEngine
        
        steps = ComplianceWorkflowEngine._get_default_workflow_steps("gst")
        
        assert len(steps) == 6
        assert steps[0]["step"] == 1
        assert "GSTR" in steps[0]["name"]


class TestReminderEngine:
    """Test reminder generation engine."""
    
    def test_generate_reminder_days(self):
        """Test reminder day generation."""
        from oneroof.compliance.workflow import ComplianceWorkflowEngine
        
        reminder_days = ComplianceWorkflowEngine.DEFAULT_REMINDER_DAYS.get("gst")
        
        assert -7 in reminder_days
        assert -3 in reminder_days
        assert -1 in reminder_days
        assert 0 in reminder_days