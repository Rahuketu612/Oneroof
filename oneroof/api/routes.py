"""
API module initialization.
"""

from fastapi import APIRouter

from oneroof.api import users, workspaces, compliance, documents, approvals, notices, communications, dashboard

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
router.include_router(notices.router, prefix="/notices", tags=["Notices"])
router.include_router(communications.router, prefix="/communications", tags=["Communications"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

routes = router