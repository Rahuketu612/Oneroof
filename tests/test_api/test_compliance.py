"""
Compliance API Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_compliance_items(client: AsyncClient):
    """Test fetching compliance items list."""
    response = await client.get("/api/compliance")
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_get_compliance_calendar(client: AsyncClient):
    """Test fetching compliance calendar."""
    response = await client.get("/api/compliance/calendar", params={"year": 2026, "month": 5})
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_validate_compliance(client: AsyncClient):
    """Test compliance validation."""
    response = await client.post("/api/compliance/1/validate")
    assert response.status_code in [200, 401, 404]