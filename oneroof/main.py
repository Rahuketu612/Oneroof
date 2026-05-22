"""
OneRoof - Compliance Collaboration Operating System
Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from oneroof.api import routes
from oneroof.core.config import settings
from oneroof.core.database import engine, Base
from oneroof.core.security import SecurityMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="OneRoof",
        description="Secure Compliance Operating System for Professional Firms",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityMiddleware)

    # Include API routes
    app.include_router(routes.router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup():
        """Initialize database and services on startup."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown."""
        await engine.dispose()

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}

    return app


app = create_app()