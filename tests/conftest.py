import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

# Configure pytest for async tests
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    from oneroof.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Get authentication headers with a valid token."""
    # In production, this would login and return the token
    # For now, return mock headers
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for creating test users."""
    return {
        "email": f"test_{asyncio.get_event_loop().time()}@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+91 9876543210"
    }


@pytest.fixture
def sample_client_data() -> dict:
    """Sample client data for creating test clients."""
    return {
        "name": "Test Company Pvt Ltd",
        "email": "test@company.com",
        "phone": "+91 9876543211",
        "gstin": "27AADCT1234P1Z5",
        "pan": "AADCT1234P",
        "entity_type": "pvt_ltd",
        "address": "123 Test Street, Mumbai",
        "compliance_types": {
            "gst": True,
            "tds": True,
            "income_tax": True,
            "roc": False
        }
    }


@pytest.fixture
def sample_compliance_data() -> dict:
    """Sample compliance item data."""
    from datetime import datetime, timedelta
    
    return {
        "name": "GSTR-1 Filing - Test Month",
        "compliance_type": "gst",
        "period": "Test Period",
        "priority": "high",
        "due_date": (datetime.utcnow() + timedelta(days=15)).isoformat(),
    }