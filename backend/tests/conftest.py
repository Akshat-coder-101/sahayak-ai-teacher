import pytest
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app, seed_default_users
from app.database import init_db, SessionLocal, DBUser
from app.services.auth import create_access_token, get_password_hash

@pytest.fixture(scope="session", autouse=True)
def setup_test_db_and_auth():
    init_db()
    seed_default_users()

@pytest.fixture(scope="session")
def student_auth_token():
    return create_access_token(data={"sub": "user-pranjal", "email": "pranjal@sahayak.edu", "role": "student"})

@pytest.fixture(scope="session")
def teacher_auth_token():
    return create_access_token(data={"sub": "user-teacher", "email": "teacher@sahayak.edu", "role": "teacher"})

@pytest.fixture(scope="session")
def student_headers(student_auth_token):
    return {"Authorization": f"Bearer {student_auth_token}"}

@pytest.fixture(scope="session")
def teacher_headers(teacher_auth_token):
    return {"Authorization": f"Bearer {teacher_auth_token}"}

@pytest.fixture(autouse=True)
def inject_auth_header_into_clients(student_auth_token, request):
    """
    Automatically injects default student Bearer token into module-level TestClients 
    so existing 65+ integration tests continue to pass seamlessly with real token verification.
    """
    token_header = f"Bearer {student_auth_token}"
    mod = getattr(request, "module", None)
    if mod and hasattr(mod, "client") and hasattr(mod.client, "headers"):
        # Only inject if test module is not test_auth (which tests raw unauthenticated calls)
        if getattr(mod, "__name__", "") != "tests.test_auth":
            mod.client.headers["Authorization"] = token_header
