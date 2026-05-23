"""
Database migration script - Creates all tables and seeds demo data.
Run this to initialize the database with sample data.
"""

import asyncio
import sys
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, '/workspace/project')

from oneroof.core.config import settings
from oneroof.core.database import Base, AsyncSessionLocal
from oneroof.core.security import get_password_hash
from oneroof.api.models import (
    Firm, User, Client, ClientUser, Workspace,
    ComplianceTemplate, ComplianceItem, DocumentRequest
)
from oneroof.utils.seed_data import create_demo_data


async def create_tables():
    """Create all database tables."""
    print("📦 Creating database tables...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Tables created successfully!")


async def seed_demo_data():
    """Seed the database with demo data."""
    print("\n🌱 Seeding demo data...")
    
    data = create_demo_data()
    
    async with AsyncSessionLocal() as db:
        # Check if data already exists
        result = await db.execute(select(Firm).where(Firm.email == data["firm"]["email"]))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("⚠️  Demo data already exists. Skipping seed.")
            print("   To re-seed, delete existing data first.")
            return
        
        # Create Firm
        firm = Firm(
            name=data["firm"]["name"],
            email=data["firm"]["email"],
            phone=data["firm"]["phone"],
            address=data["firm"]["address"],
            gstin=data["firm"]["gstin"],
        )
        db.add(firm)
        await db.flush()
        print(f"   ✅ Created firm: {firm.name}")
        
        # Create Firm Users
        for user_data in data["users"]:
            user = User(
                firm_id=firm.id,
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                phone=user_data["phone"],
                is_active=True,
            )
            db.add(user)
        print(f"   ✅ Created {len(data['users'])} firm users")
        
        # Create Clients and Workspaces
        for client_data in data["clients"]:
            client = Client(
                firm_id=firm.id,
                name=client_data["name"],
                email=client_data["email"],
                phone=client_data["phone"],
                gstin=client_data["gstin"],
                pan=client_data["pan"],
                entity_type=client_data["entity_type"],
                address=client_data["address"],
                compliance_types=client_data["compliance_types"],
                is_active=True,
            )
            db.add(client)
            await db.flush()
            
            # Create workspace for client
            workspace = Workspace(
                client_id=client.id,
                name=f"{client.name} Workspace",
                is_active=True,
            )
            db.add(workspace)
            print(f"   ✅ Created client: {client.name} (Workspace: {workspace.id})")
            
            # Create client users
            for client_user_data in client_data["users"]:
                client_user = ClientUser(
                    client_id=client.id,
                    email=client_user_data["email"],
                    password_hash=get_password_hash(client_user_data["password"]),
                    first_name=client_user_data["first_name"],
                    last_name=client_user_data["last_name"],
                    role=client_user_data["role"],
                    is_active=True,
                )
                db.add(client_user)
            
            await db.flush()
            print(f"      Created {len(client_data['users'])} client users")
        
        # Create Compliance Templates
        for template_data in data["templates"]:
            template = ComplianceTemplate(
                firm_id=firm.id,
                name=template_data["name"],
                compliance_type=template_data["compliance_type"],
                frequency=template_data["frequency"],
                description=template_data["description"],
                required_documents=template_data["required_documents"],
                workflow_steps=template_data["workflow_steps"],
                reminder_days=template_data["reminder_days"],
                is_active=True,
            )
            db.add(template)
        print(f"   ✅ Created {len(data['templates'])} compliance templates")
        
        await db.commit()
        print("\n🌱 Demo data seeded successfully!")


async def main():
    """Main migration function."""
    print("="*60)
    print("OneRoof Database Migration")
    print("="*60)
    
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        # Full migration with seeding
        await create_tables()
        await seed_demo_data()
    elif len(sys.argv) > 1 and sys.argv[1] == "--tables-only":
        # Create tables only
        await create_tables()
    else:
        # Interactive
        print("\nChoose an option:")
        print("1. Create tables only")
        print("2. Create tables and seed demo data")
        choice = input("\nEnter choice (1/2): ").strip()
        
        if choice == "1":
            await create_tables()
        elif choice == "2":
            await create_tables()
            await seed_demo_data()
        else:
            print("Invalid choice. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())