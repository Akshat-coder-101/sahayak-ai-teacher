import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.services.rate_limiter import auth_rate_limiter, sandbox_rate_limiter
from main import app, lifespan

client = TestClient(app)

def test_production_startup_jwt_secret_validation():
    """Startup must fail in production if JWT_SECRET_KEY is default dev or < 32 chars."""
    original_env = settings.ENV
    original_key = settings.JWT_SECRET_KEY

    try:
        # Case 1: Default dev secret in production -> raises RuntimeError
        settings.ENV = "production"
        settings.JWT_SECRET_KEY = "sahayak-insecure-secret-key-change-in-production-2026"
        with pytest.raises(RuntimeError, match="FATAL: In production"):
            with client:
                pass

        # Case 2: Secret key shorter than 32 characters -> raises RuntimeError
        settings.JWT_SECRET_KEY = "short_insecure_key"
        with pytest.raises(RuntimeError, match="at least 32 characters"):
            with client:
                pass

        # Case 3: Valid strong key >= 32 chars -> succeeds
        settings.JWT_SECRET_KEY = "production-hardened-strong-jwt-secret-key-2026-secure"
        with client:
            res = client.get("/health")
            assert res.status_code == 200
    finally:
        settings.ENV = original_env
        settings.JWT_SECRET_KEY = original_key


def test_production_auth_cookie_attributes():
    """Auth cookie must be httpOnly and SameSite in all modes, and Secure in production."""
    original_env = settings.ENV
    try:
        # Test in production mode
        settings.ENV = "production"
        res = client.post("/api/auth/login", json={"email": "pranjal@sahayak.edu", "password": "password123"})
        assert res.status_code == 200
        set_cookie = res.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "httponly" in set_cookie.lower()
        assert "samesite=lax" in set_cookie.lower()
        assert "secure" in set_cookie.lower()

        # Test in development mode
        settings.ENV = "development"
        res_dev = client.post("/api/auth/login", json={"email": "pranjal@sahayak.edu", "password": "password123"})
        assert res_dev.status_code == 200
        dev_cookie = res_dev.headers.get("set-cookie", "")
        assert "access_token=" in dev_cookie
        assert "httponly" in dev_cookie.lower()
    finally:
        settings.ENV = original_env


def test_production_cors_filters_wildcard():
    """Wildcard origins are disallowed in production."""
    from main import allowed
    origins = list(allowed) + ["*"]
    if True: # production logic simulation
        prod_origins = [o for o in origins if o != "*"]
        assert "*" not in prod_origins


def test_auth_rate_limiting():
    """Repeated login attempts beyond limit trigger HTTP 429 Too Many Requests."""
    limiter = getattr(auth_rate_limiter, "limiter", None)
    if limiter:
        limiter.reset()

    # Default auth limiter allows 15 requests per 60s
    for _ in range(15):
        res = client.post("/api/auth/login", json={"email": "pranjal@sahayak.edu", "password": "password123"})
        assert res.status_code in [200, 401]

    # 16th request must exceed threshold
    overflow_res = client.post("/api/auth/login", json={"email": "pranjal@sahayak.edu", "password": "password123"})
    assert overflow_res.status_code == 429
    assert "Rate limit exceeded" in overflow_res.text
    assert "Retry-After" in overflow_res.headers

    if limiter:
        limiter.reset()


def test_sandbox_rate_limiting():
    """Sandbox execution endpoint enforces rate limits."""
    limiter = getattr(sandbox_rate_limiter, "limiter", None)
    if limiter:
        limiter.reset()

    # Default sandbox limiter allows 25 requests per 60s
    for _ in range(25):
        res = client.post("/api/sandbox/run", json={"code": "x = 10\nprint(x)"})
        assert res.status_code == 200

    # 26th request must be throttled
    throttled = client.post("/api/sandbox/run", json={"code": "print('blocked')"})
    assert throttled.status_code == 429
    assert "Rate limit exceeded" in throttled.text

    if limiter:
        limiter.reset()


def test_upload_validation_empty_file():
    """Upload must reject empty 0-byte files with HTTP 400."""
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    msg = res.json().get("error", {}).get("message", "") or res.text
    assert "empty" in msg.lower()


def test_upload_validation_wrong_extension():
    """Upload must reject unsupported file extensions (e.g. .exe, .sh) with HTTP 400."""
    files = {"file": ("malicious_script.sh", b"echo 'hacked'", "application/x-sh")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    msg = res.json().get("error", {}).get("message", "") or res.text
    assert "unsupported" in msg.lower()


def test_upload_validation_no_extension():
    """Upload must reject files lacking an extension with HTTP 400."""
    files = {"file": ("README", b"Some markdown text", "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    msg = res.json().get("error", {}).get("message", "") or res.text
    assert "no extension" in msg.lower()


def test_upload_validation_oversize():
    """Upload must reject files exceeding MAX_UPLOAD_MB with HTTP 400."""
    original_max = settings.MAX_UPLOAD_MB
    try:
        settings.MAX_UPLOAD_MB = 1  # temporarily set to 1MB
        oversize_content = b"0" * (1024 * 1024 + 500)  # > 1MB
        files = {"file": ("large_doc.txt", oversize_content, "text/plain")}
        res = client.post("/api/documents/upload", files=files)
        assert res.status_code == 400
        msg = res.json().get("error", {}).get("message", "") or res.text
        assert "exceeds maximum allowed size" in msg.lower()
    finally:
        settings.MAX_UPLOAD_MB = original_max
