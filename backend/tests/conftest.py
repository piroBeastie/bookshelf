import os

# point the app at a throwaway sqlite file BEFORE the app is imported, so the
# tests can never touch the real postgres database
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_book(client):
    response = client.post(
        "/api/books",
        json={
            "title": "The Pragmatic Programmer",
            "author": "Hunt and Thomas",
            "genre": "Tech",
            "pages": 352,
            "shelf": "READING",
        },
    )
    assert response.status_code == 201
    return response.json()
