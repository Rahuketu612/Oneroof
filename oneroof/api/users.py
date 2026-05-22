"""
User management API endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oneroof.core.database import get_db
from oneroof.core.security import get_current_user, get_password_hash, verify_password, create_access_token, RoleChecker
from oneroof.api.models import User, ClientUser, Client


router = APIRouter(prefix="/users", tags=["Users"])


# Pydantic schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str
    phone: Optional[str] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['partner', 'manager', 'staff']:
            raise ValueError('Role must be partner, manager, or staff')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    phone: Optional[str]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class ClientUserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    phone: Optional[str] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['client_admin', 'client_user', 'client_viewer']:
            raise ValueError('Role must be client_admin, client_user, or client_viewer')
        return v


class ClientUserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    phone: Optional[str]
    is_active: bool
    client_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    entity_type: str
    address: Optional[str] = None
    compliance_types: dict = {}


class ClientResponse(BaseModel):
    id: int
    name: str
    email: str
    gstin: Optional[str]
    pan: Optional[str]
    entity_type: str
    compliance_types: dict
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Firm management endpoints
@router.post("/firm", response_model=dict)
async def create_firm(name: str, email: str, phone: Optional[str] = None):
    """Create a new firm (called during firm registration)."""
    db = await anext(get_db())
    # Check if firm exists
    result = await db.execute(select(Firm).where(Firm.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Firm with this email already exists")
    
    firm = Firm(name=name, email=email, phone=phone)
    db.add(firm)
    await db.commit()
    await db.refresh(firm)
    
    return {"id": firm.id, "name": firm.name, "email": firm.email}


# User endpoints
@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserCreate, firm_id: int):
    """Register a new firm user."""
    db = await anext(get_db())
    
    # Check if user exists
    result = await db.execute(select(User).where(User.firm_id == firm_id, User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user
    user = User(
        firm_id=firm_id,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        phone=user_data.phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "firm_id": firm_id
    })
    refresh_token = create_access_token(
        {"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=7)
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(credentials: UserLogin, firm_id: int):
    """Login a firm user."""
    db = await anext(get_db())
    
    result = await db.execute(select(User).where(User.firm_id == firm_id, User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "firm_id": firm_id
    })
    refresh_token = create_access_token(
        {"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=7)
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    db = await anext(get_db())
    result = await db.execute(select(User).where(User.id == int(current_user["user_id"])))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)


@router.get("/", response_model=List[UserResponse])
async def list_firm_users(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List all users in the firm."""
    db = await anext(get_db())
    result = await db.execute(
        select(User)
        .where(User.firm_id == current_user["firm_id"])
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    
    return [UserResponse.model_validate(u) for u in users]


# Client management
@router.post("/clients", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new client (Partner/Manager only)."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    client = Client(
        firm_id=current_user["firm_id"],
        name=client_data.name,
        email=client_data.email,
        phone=client_data.phone,
        gstin=client_data.gstin,
        pan=client_data.pan,
        entity_type=client_data.entity_type,
        address=client_data.address,
        compliance_types=client_data.compliance_types,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    
    return ClientResponse.model_validate(client)


@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List all clients for the firm."""
    db = await anext(get_db())
    result = await db.execute(
        select(Client)
        .where(Client.firm_id == current_user["firm_id"])
        .offset(skip)
        .limit(limit)
    )
    clients = result.scalars().all()
    
    return [ClientResponse.model_validate(c) for c in clients]


# Client user management
@router.post("/clients/{client_id}/users", response_model=ClientUserResponse)
async def invite_client_user(
    client_id: int,
    user_data: ClientUserCreate,
    current_user: dict = Depends(get_current_user)
):
    """Invite a client user (Partner/Manager only)."""
    if not RoleChecker.check(current_user["role"], ["partner", "manager"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await anext(get_db())
    
    # Verify client belongs to firm
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.firm_id == current_user["firm_id"])
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check if user exists
    result = await db.execute(
        select(ClientUser).where(ClientUser.client_id == client_id, ClientUser.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create invite
    import secrets
    invite_token = secrets.token_urlsafe(32)
    
    client_user = ClientUser(
        client_id=client_id,
        email=user_data.email,
        password_hash=get_password_hash(secrets.token_urlsafe(16)),  # Temp password
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        phone=user_data.phone,
        invite_token=invite_token,
        invite_expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(client_user)
    await db.commit()
    await db.refresh(client_user)
    
    # TODO: Send invite email
    
    return ClientUserResponse.model_validate(client_user)


@router.get("/clients/{client_id}/users", response_model=List[ClientUserResponse])
async def list_client_users(
    client_id: int,
    current_user: dict = Depends(get_current_user)
):
    """List all users for a client."""
    db = await anext(get_db())
    result = await db.execute(
        select(ClientUser).where(ClientUser.client_id == client_id)
    )
    users = result.scalars().all()
    
    return [ClientUserResponse.model_validate(u) for u in users]


# Need to import Firm for create_firm
from oneroof.api.models import Firm