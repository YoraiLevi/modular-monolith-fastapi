import pytest
from httpx import ASGITransport, AsyncClient

from app.app_factory import app_factory


@pytest.fixture
def app():
    return app_factory()


@pytest.mark.anyio
async def test_root(app):
    # How to test health but also follow redirects?
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
