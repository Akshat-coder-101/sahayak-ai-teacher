import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
import uuid

from main import app
from app.database import SessionLocal, DBUser, DBLessonSession
from app.services.auth import create_access_token

client = TestClient(app)

def test_open_routes_accessible_without_token():
    unauth_client = TestClient(app)
    resp = unauth_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    resp = unauth_client.get("/api/health")
    assert resp.status_code == 200

    resp = unauth_client.get("/")
    assert resp.status_code == 200

def test_unauthenticated_request_to_protected_route_fails_401():
    unauth_client = TestClient(app)
    # Protected route /api/profile/{user_id}
    resp = unauth_client.get("/api/profile/user-pranjal")
    assert resp.status_code == 401
    assert "error" in resp.json()
    assert resp.json()["error"]["code"] == "unauthorized"

    # Protected route /api/sandbox/run
    resp = unauth_client.post("/api/sandbox/run", json={"code": "print('hello')"})
    assert resp.status_code == 401

def test_password_format_validation():
    test_email = f"student_{uuid.uuid4().hex[:8]}@sahayak.edu"
    
    # 1. Too short
    r1 = client.post("/api/auth/register", json={"email": test_email, "password": "Sh1!"})
    assert r1.status_code in [400, 422]
    
    # 2. Missing uppercase
    r2 = client.post("/api/auth/register", json={"email": test_email, "password": "lowercase123!"})
    assert r2.status_code == 400
    assert "uppercase" in r2.text.lower()

    # 3. Missing lowercase
    r3 = client.post("/api/auth/register", json={"email": test_email, "password": "UPPERCASE123!"})
    assert r3.status_code == 400
    assert "lowercase" in r3.text.lower()

    # 4. Missing number
    r4 = client.post("/api/auth/register", json={"email": test_email, "password": "NoNumbersHere!"})
    assert r4.status_code == 400
    assert "number" in r4.text.lower()

    # 5. Missing special character
    r5 = client.post("/api/auth/register", json={"email": test_email, "password": "NoSpecialChar123"})
    assert r5.status_code == 400
    assert "special character" in r5.text.lower()

def test_user_registration_and_login():
    test_email = f"student_{uuid.uuid4().hex[:8]}@sahayak.edu"
    test_pwd = "safePassword123!"

    # 1. Register new student
    reg_resp = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_pwd,
        "name": "Test Student",
        "role": "student",
        "level": "beginner"
    })
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["role"] == "student"
    assert "access_token" in reg_resp.cookies

    # 2. Duplicate registration returns 409
    dup_resp = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_pwd,
        "role": "student"
    })
    assert dup_resp.status_code == 409

    # 3. Login with correct password
    login_resp = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_pwd
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == test_email

    # 4. Login with incorrect password returns 401
    bad_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401

def test_token_expiry_and_invalid_token():
    unauth_client = TestClient(app)

    # 1. Invalid token signature / format
    resp = unauth_client.get(
        "/api/profile/user-pranjal",
        headers={"Authorization": "Bearer completely-invalid-token-xyz"}
    )
    assert resp.status_code == 401

    # 2. Expired token
    expired_token = create_access_token(
        data={"sub": "user-pranjal", "email": "pranjal@sahayak.edu", "role": "student"},
        expires_delta=timedelta(seconds=-10)
    )
    resp = unauth_client.get(
        "/api/profile/user-pranjal",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp.status_code == 401

def test_role_based_access_scoping():
    db = SessionLocal()
    try:
        # Create student A and student B with unique emails
        suffix = uuid.uuid4().hex[:6]
        user_a_id = f"student-a-{suffix}"
        user_b_id = f"student-b-{suffix}"
        teacher_id = f"teacher-{suffix}"
        email_a = f"a_{suffix}@sahayak.edu"
        email_b = f"b_{suffix}@sahayak.edu"
        email_teacher = f"t_{suffix}@sahayak.edu"

        token_a = create_access_token({"sub": user_a_id, "email": email_a, "role": "student"})
        token_b = create_access_token({"sub": user_b_id, "email": email_b, "role": "student"})
        token_teacher = create_access_token({"sub": teacher_id, "email": email_teacher, "role": "teacher"})

        db.add(DBUser(id=user_a_id, email=email_a, hashed_password="pwd", role="student", name="Student A"))
        db.add(DBUser(id=user_b_id, email=email_b, hashed_password="pwd", role="student", name="Student B"))
        db.add(DBUser(id=teacher_id, email=email_teacher, hashed_password="pwd", role="teacher", name="Teacher T"))
        db.commit()

        # Student A creates own profile
        client.post(f"/api/profile/{user_a_id}", json={
            "name": "Student A",
            "level": "beginner",
            "goal": "understand_concept",
            "preferred_style": "visual",
            "language": "en"
        }, headers={"Authorization": f"Bearer {token_a}"})

        # Student A fetches own profile -> 200
        resp = client.get(f"/api/profile/{user_a_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Student A"

        # Student B attempts to fetch Student A's profile -> 403 Forbidden!
        resp = client.get(f"/api/profile/{user_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "forbidden"

        # Teacher fetches Student A's profile -> 200 OK
        resp = client.get(f"/api/profile/{user_a_id}", headers={"Authorization": f"Bearer {token_teacher}"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Student A"

        # Test scoped report access
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        sess = DBLessonSession(
            id=session_id,
            user_id=user_a_id,
            topic="Thermodynamics",
            language="en"
        )
        db.add(sess)
        db.commit()

        # Student B attempts to fetch Student A's report -> 403 Forbidden!
        resp = client.get(f"/api/report/{session_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "forbidden"

        # Student A fetches own report -> 200 OK
        resp = client.get(f"/api/report/{session_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert resp.status_code == 200
    finally:
        db.close()

def test_auth_me_endpoint():
    token = create_access_token({"sub": "user-pranjal", "email": "pranjal@sahayak.edu", "role": "student"})
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "pranjal@sahayak.edu"
    assert data["role"] == "student"

def test_logout_endpoint():
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
