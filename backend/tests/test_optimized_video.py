import pytest
import time
import os
import uuid
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal, DBExportJob, DBLessonSession
from app.services.video import VideoService
from app.config import settings

client = TestClient(app)

@pytest.fixture
def auth_headers():
    # Register/login a student
    email = f"testvideo_{uuid.uuid4().hex[:8]}@test.com"
    pwd = "SecurePassword123!"
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "name": "Video Test Student",
        "role": "student",
        "preferred_difficulty": "intermediate"
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_video_generate_and_status_api(auth_headers):
    """
    Tests POST /api/video/generate and GET /api/video/status/{job_id}.
    Verifies immediate job return, valid step list, and status reporting.
    """
    from unittest.mock import patch
    with patch("app.api.video.VideoService.generate_standalone_video"):
        # 1. Start generation in demo mode
        resp = client.post(
            "/api/video/generate",
            headers=auth_headers,
            json={
                "topic": "Photosynthesis and Calvin Cycle",
                "mode": "demo",
                "language": "en"
            }
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "job_id" in data
        assert data["status"] in ["processing", "queued"]
        assert data["mode"] == "demo"
        job_id = data["job_id"]

    # 2. Check status polling endpoint
    status_resp = client.get(f"/api/video/status/{job_id}", headers=auth_headers)
    assert status_resp.status_code == 200, status_resp.text
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["processing", "completed", "failed", "queued"]
    assert isinstance(status_data["steps"], list)
    assert len(status_data["steps"]) >= 3

def test_video_status_404(auth_headers):
    resp = client.get("/api/video/status/non_existent_job_12345", headers=auth_headers)
    assert resp.status_code == 404
