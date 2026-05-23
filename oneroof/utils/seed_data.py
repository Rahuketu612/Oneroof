"""
Database seed script - Creates demo data for testing.
Run this to populate the database with sample firm, users, clients, and compliance items.
"""

from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_demo_data():
    """Generate demo data dictionary for seeding."""
    
    # Demo Firm
    firm = {
        "name": "Sharma & Associates",
        "email": "info@sharmaassociates.com",
        "phone": "+91 9876543210",
        "address": "101, Trade Center, MG Road, Mumbai - 400001",
        "gstin": "27AAACH1234C1ZB",
    }
    
    # Demo Firm Users
    users = [
        {
            "email": "partner@sharmaassociates.com",
            "password": "partner123",
            "first_name": "Rajesh",
            "last_name": "Sharma",
            "role": "partner",
            "phone": "+91 9876543211",
        },
        {
            "email": "manager@sharmaassociates.com",
            "password": "manager123",
            "first_name": "Priya",
            "last_name": "Patel",
            "role": "manager",
            "phone": "+91 9876543212",
        },
        {
            "email": "staff@sharmaassociates.com",
            "password": "staff123",
            "first_name": "Amit",
            "last_name": "Singh",
            "role": "staff",
            "phone": "+91 9876543213",
        },
    ]
    
    # Demo Clients
    clients = [
        {
            "name": "Tech Solutions Pvt Ltd",
            "email": "accounts@techsol.com",
            "phone": "+91 9876543220",
            "gstin": "27AADCS1234P1ZP",
            "pan": "AADCS1234P",
            "entity_type": "pvt_ltd",
            "address": "502, Business Park, Andheri East, Mumbai - 400059",
            "compliance_types": {
                "gst": True,
                "tds": True,
                "income_tax": True,
                "roc": False,
            },
            "users": [
                {
                    "email": "admin@techsol.com",
                    "password": "client123",
                    "first_name": "Vikram",
                    "last_name": "Mehta",
                    "role": "client_admin",
                },
                {
                    "email": "accounts@techsol.com",
                    "password": "client123",
                    "first_name": "Sunita",
                    "last_name": "Shah",
                    "role": "client_user",
                },
            ],
        },
        {
            "name": "Green Earth Enterprises",
            "email": "finance@greenearth.in",
            "phone": "+91 9876543230",
            "gstin": "27AADCG5678M1ZX",
            "pan": "AADCG5678M",
            "entity_type": "proprietorship",
            "address": "203, Green Tower, Bandra West, Mumbai - 400050",
            "compliance_types": {
                "gst": True,
                "tds": False,
                "income_tax": True,
                "roc": False,
            },
            "users": [
                {
                    "email": "owner@greenearth.in",
                    "password": "client123",
                    "first_name": "Pooja",
                    "last_name": "Kapoor",
                    "role": "client_admin",
                },
            ],
        },
        {
            "name": "Metro Logistics LLP",
            "email": "compliance@metrologistics.com",
            "phone": "+91 9876543240",
            "gstin": "27AADCM9012L1ZY",
            "pan": "AADCM9012L",
            "entity_type": "llp",
            "address": "305, Logistics Hub, Navi Mumbai - 400703",
            "compliance_types": {
                "gst": True,
                "tds": True,
                "income_tax": True,
                "roc": True,
            },
            "users": [
                {
                    "email": "director@metrologistics.com",
                    "password": "client123",
                    "first_name": "Rahul",
                    "last_name": "Desai",
                    "role": "client_admin",
                },
            ],
        },
    ]
    
    # Compliance Templates
    templates = [
        {
            "name": "Monthly GST Return (GSTR-1)",
            "compliance_type": "gst",
            "frequency": "monthly",
            "description": "Monthly return of outward supplies",
            "required_documents": [
                "Sales Register",
                "E-Way Bills",
                "Export Invoices",
                "Credit/Debit Notes",
            ],
            "workflow_steps": [
                {"step": 1, "name": "Data Collection", "roles": ["staff"], "action": "Collect sales data from client"},
                {"step": 2, "name": "GSTR-1 Preparation", "roles": ["staff"], "action": "Prepare GSTR-1 return"},
                {"step": 3, "name": "Reconciliation", "roles": ["staff"], "action": "Reconcile with purchase returns"},
                {"step": 4, "name": "Manager Review", "roles": ["manager"], "action": "Verify and approve"},
                {"step": 5, "name": "Client Approval", "roles": ["client_admin"], "action": "Client reviews and approves"},
                {"step": 6, "name": "Filing", "roles": ["staff"], "action": "File GSTR-1 before deadline"},
            ],
            "reminder_days": [-7, -3, -1, 0],
        },
        {
            "name": "Monthly GST Return (GSTR-3B)",
            "compliance_type": "gst",
            "frequency": "monthly",
            "description": "Summary return with tax payment",
            "required_documents": [
                "GSTR-1 Data",
                "Purchase Register",
                "ITC Claims",
                "Tax Payment Challan",
            ],
            "workflow_steps": [
                {"step": 1, "name": "ITC Reconciliation", "roles": ["staff"], "action": "Reconcile input tax credit"},
                {"step": 2, "name": "Liability Calculation", "roles": ["staff"], "action": "Calculate tax liability"},
                {"step": 3, "name": "Payment Planning", "roles": ["manager"], "action": "Plan cash flow for payment"},
                {"step": 4, "name": "Client Approval", "roles": ["client_admin"], "action": "Client approves tax payment"},
                {"step": 5, "name": "Payment & Filing", "roles": ["staff"], "action": "Make payment and file return"},
            ],
            "reminder_days": [-5, -2, 0],
        },
        {
            "name": "Quarterly TDS Return (27Q)",
            "compliance_type": "tds",
            "frequency": "quarterly",
            "description": "TDS on payments other than salary",
            "required_documents": [
                "Payment Records",
                "Deduction Certificates",
                "PAN of deductees",
                "Challan Details",
            ],
            "workflow_steps": [
                {"step": 1, "name": "Deduction Data", "roles": ["staff"], "action": "Collect payment and deduction data"},
                {"step": 2, "name": "TDS Calculation", "roles": ["staff"], "action": "Calculate TDS on each payment"},
                {"step": 3, "name": "Challan Verification", "roles": ["manager"], "action": "Verify challan payments"},
                {"step": 4, "name": "Client Approval", "roles": ["client_admin"], "action": "Client approves filing"},
                {"step": 5, "name": "e-Filing", "roles": ["staff"], "action": "Upload and file TDS return"},
            ],
            "reminder_days": [-10, -5, -2, 0],
        },
        {
            "name": "Annual Income Tax Return (ITR-6)",
            "compliance_type": "income_tax",
            "frequency": "yearly",
            "description": "Annual return for companies",
            "required_documents": [
                "Financial Statements",
                "Audit Report",
                "Tax Audit Report",
                "Form 16/16A",
                "Investment Proofs",
                "Previous Year Returns",
            ],
            "workflow_steps": [
                {"step": 1, "name": "Documents Collection", "roles": ["staff"], "action": "Collect all required documents"},
                {"step": 2, "name": "Income Computation", "roles": ["staff"], "action": "Compute total income and tax"},
                {"step": 3, "name": "Deductions", "roles": ["staff"], "action": "Apply eligible deductions"},
                {"step": 4, "name": "Manager Review", "roles": ["manager"], "action": "Review computation"},
                {"step": 5, "name": "Partner Review", "roles": ["partner"], "action": "Partner final review"},
                {"step": 6, "name": "Client Approval", "roles": ["client_admin"], "action": "Client approval"},
                {"step": 7, "name": "Filing", "roles": ["staff"], "action": "File ITR on income tax portal"},
            ],
            "reminder_days": [-30, -15, -7, 0],
        },
    ]
    
    # Sample Compliance Items for demo
    def get_sample_compliance_items():
        """Generate sample compliance items for current month."""
        now = datetime.utcnow()
        month_name = now.strftime("%B %Y")
        
        items = []
        
        # GSTR-1 items
        items.append({
            "name": f"GSTR-1 Filing - {month_name}",
            "compliance_type": "gst",
            "period": month_name,
            "status": "pending",
            "priority": "high",
            "due_date": now + timedelta(days=10),
            "workflow_steps": templates[0]["workflow_steps"],
        })
        
        # GSTR-3B items
        items.append({
            "name": f"GSTR-3B Filing - {month_name}",
            "compliance_type": "gst",
            "period": month_name,
            "status": "in_progress",
            "priority": "high",
            "due_date": now + timedelta(days=12),
            "workflow_steps": templates[1]["workflow_steps"],
        })
        
        # TDS items (quarterly)
        quarter = ((now.month - 1) // 3) + 1
        items.append({
            "name": f"TDS Quarterly Return - Q{quarter} {now.year}",
            "compliance_type": "tds",
            "period": f"Q{quarter} {now.year}",
            "status": "pending",
            "priority": "normal",
            "due_date": now + timedelta(days=30),
            "workflow_steps": templates[2]["workflow_steps"],
        })
        
        return items
    
    return {
        "firm": firm,
        "users": users,
        "clients": clients,
        "templates": templates,
        "compliance_items": get_sample_compliance_items(),
    }


def print_demo_credentials():
    """Print demo login credentials."""
    print("\n" + "="*60)
    print("DEMO LOGIN CREDENTIALS")
    print("="*60)
    
    print("\n📋 FIRM USERS:")
    print("-" * 40)
    print("Partner: partner@sharmaassociates.com / partner123")
    print("Manager: manager@sharmaassociates.com / manager123")
    print("Staff:   staff@sharmaassociates.com / staff123")
    
    print("\n👥 CLIENT USERS:")
    print("-" * 40)
    print("Tech Solutions:     admin@techsol.com / client123")
    print("Green Earth:        owner@greenearth.in / client123")
    print("Metro Logistics:    director@metrologistics.com / client123")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    data = create_demo_data()
    print("\n✅ Demo data structure created!")
    print(f"\n📦 Firm: {data['firm']['name']}")
    print(f"👤 Users: {len(data['users'])}")
    print(f"🏢 Clients: {len(data['clients'])}")
    print(f"📋 Templates: {len(data['templates'])}")
    print(f"📅 Compliance Items: {len(data['compliance_items'])}")
    
    print_demo_credentials()