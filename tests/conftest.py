import pytest
from app import create_app
from app.extensions import db as _db
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture
def sample_prompt(client):
    """Create a sample prompt and return its data."""
    resp = client.post("/api/prompts", json={
        "title": "Test Prompt",
        "content": "You are a helpful assistant.",
        "notes": "A test prompt",
    })
    assert resp.status_code == 201
    return resp.json


@pytest.fixture
def sample_tag(client):
    """Create a sample tag and return its data."""
    resp = client.post("/api/tags", json={"name": "python", "color": "#3776ab"})
    assert resp.status_code == 201
    return resp.json


@pytest.fixture
def sample_category(client):
    """Create a sample category and return its data."""
    resp = client.post("/api/categories", json={"name": "TestCat", "description": "For testing"})
    assert resp.status_code == 201
    return resp.json
