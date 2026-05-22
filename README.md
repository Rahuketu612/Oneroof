# OneRoof - Compliance Collaboration Operating System

## Overview
OneRoof is a secure compliance operating system designed for CA/CS/CMA firms to manage client compliance, workflows, approvals, and document storage in one unified platform.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with role-based access control
- **File Storage**: Local with encryption, S3-compatible for cloud
- **Task Queue**: Celery with Redis for scheduling

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand
- **UI Library**: Custom components with Tailwind CSS
- **Routing**: React Router v6

### Infrastructure
- **Web Server**: Nginx
- **WSGI**: Gunicorn/Uvicorn
- **Database**: PostgreSQL 15
- **Cache**: Redis

## Project Structure

```
oneroof/
├── api/                 # API routes and endpoints
├── core/                # Core configuration and security
├── compliance/          # Compliance workflow engine
├── documents/           # Document management system
├── notifications/       # Notification and reminder system
├── workspaces/         # Client workspace management
├── audit/               # Audit logging system
└── utils/               # Utility functions

frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components
│   ├── hooks/           # Custom React hooks
│   ├── context/         # React context providers
│   └── utils/           # Frontend utilities
└── public/              # Static assets
```

## Key Features
1. Compliance Workspaces - Per-client secure environments
2. Automated Workflow Generation - Template-based compliance creation
3. Immutable Approvals - Timestamped client sign-offs
4. Version-Controlled Documents - No overwriting, full history
5. Structured Communication - All messages linked to compliance items
6. Complete Audit Trail - Track every action
7. Role-Based Dashboards - Partner, Manager, Staff, Client views
8. Notice Management - Structured response workflows
9. Failsafe Mechanisms - Escalation, duplicate protection, integrity validation

## Security
- All files encrypted at rest
- Role-based access control (RBAC)
- MFA support
- Immutable audit logs
- IP/device logging for approvals
- Watermarking for sensitive downloads