# OneRoof - Unit & Integration Tests

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=oneroof --cov-report=html

# Run specific test file
pytest tests/test_compliance.py

# Run with verbose output
pytest -v
```

## Test Structure

```
tests/
├── conftest.py           # Pytest fixtures
├── test_api/             # API endpoint tests
│   ├── test_auth.py
│   ├── test_compliance.py
│   └── test_workspaces.py
├── test_services/        # Service layer tests
│   ├── test_workflow.py
│   └── test_failsafe.py
└── test_integration/      # Full workflow tests
    └── test_client_flow.py
```

## Writing Tests

```python
import pytest
from httpx import AsyncClient
from oneroof.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_login(client):
    response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
```

## Fixtures (conftest.py)

Available fixtures:
- `client` - AsyncClient for API testing
- `auth_headers` - Headers with JWT token
- `test_user` - Test user fixture
- `test_client` - Test client fixture
- `test_workspace` - Test workspace fixture