# OneRoof

## Compliance Collaboration Operating System

A secure, structured compliance management platform designed for CA/CS/CMA firms.

### Features

- **Compliance Workspaces** - Per-client secure environments
- **Automated Workflow Generation** - Template-based compliance creation
- **Immutable Approvals** - Timestamped client sign-offs with IP logging
- **Version-Controlled Documents** - No overwriting, full history
- **Structured Communication** - All messages linked to compliance items
- **Complete Audit Trail** - Track every action
- **Role-Based Dashboards** - Partner, Manager, Staff, Client views
- **Notice Management** - Structured response workflows
- **Failsafe Mechanisms** - Escalation, duplicate protection, integrity validation

### Architecture

```
oneroof/
├── api/                 # API routes and endpoints
│   ├── users.py        # User & client management
│   ├── workspaces.py   # Workspace management
│   ├── compliance.py   # Compliance items & requests
│   ├── documents.py    # Document management
│   ├── approvals.py    # Approval workflows
│   ├── notices.py      # Notice management
│   ├── communications.py # Structured communication
│   └── dashboard.py    # Role-based dashboards
├── core/               # Core configuration
│   ├── config.py       # Settings
│   ├── database.py     # Database connection
│   └── security.py     # Authentication & authorization
├── audit/              # Audit logging
├── compliance/         # Compliance workflow engine
├── documents/          # Document management
├── notifications/      # Notification system
├── workspaces/         # Workspace management
└── main.py            # Application entry

frontend/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Page components
│   ├── context/       # React context
│   └── utils/         # Utilities
```

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL with SQLAlchemy
- JWT authentication
- Celery for task scheduling

**Frontend:**
- React 18 with TypeScript
- Zustand for state management
- Tailwind CSS

### Quick Start

```bash
# Backend
cd oneroof
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Design Philosophy

OneRoof is NOT:
- ❌ WhatsApp
- ❌ Gmail
- ❌ Slack

OneRoof IS:
- ✅ Structured compliance operations software
- ✅ Secure compliance OS for professional firms
- ✅ Complete audit trail and accountability

### Security

- All files encrypted at rest
- Role-based access control
- MFA support
- Immutable audit logs
- IP/device logging for approvals
- Watermarking for sensitive downloads

### License

Proprietary - All rights reserved