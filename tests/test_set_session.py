import importlib
import pathlib
import sys

import pytest

import uploaditin_backend.app as app_module


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeConn:
    def __init__(self, admin_row=None):
        self.admin_row = admin_row

    def execute(self, *_args, **_kwargs):
        return _FakeResult(row=self.admin_row)

    def close(self):
        return None


@pytest.fixture
def app_module_fixture(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "header.payload.signature")
    return app_module


def test_set_session_valid_token_sets_session(monkeypatch, app_module_fixture):
    def fake_requests_get(url, headers=None, timeout=0):
        assert headers is not None
        assert url == "https://example.supabase.co/auth/v1/user"
        assert headers["Authorization"] == "Bearer token-123"
        assert headers["apikey"] == "header.payload.signature"
        assert timeout == 10
        return _FakeResponse(
            200,
            {
                "id": "user-1",
                "email": "student@example.com",
                "user_metadata": {"username": "student-name", "role": "Student"},
            },
        )

    monkeypatch.setattr(app_module_fixture.requests, "get", fake_requests_get)
    monkeypatch.setattr(app_module_fixture, "get_db", lambda: _FakeConn(admin_row=None))

    client = app_module_fixture.app.test_client()
    resp = client.post("/set_session", json={"access_token": "token-123"})

    assert resp.status_code == 200
    assert resp.get_json() == {"success": True}

    with client.session_transaction() as sess:
        assert sess["user_id"] == "user-1"
        assert sess["username"] == "student-name"
        assert sess["role"] == "Student"
        assert "SUPABASE_SECRET_KEY" not in sess
        assert "apikey" not in sess


def test_set_session_missing_token(monkeypatch, app_module_fixture):
    monkeypatch.setattr(app_module_fixture.requests, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("requests.get should not be called")))

    client = app_module_fixture.app.test_client()
    resp = client.post("/set_session", json={})

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "No token"}


def test_set_session_invalid_token_returns_401(monkeypatch, app_module_fixture):
    monkeypatch.setattr(app_module_fixture.requests, "get", lambda *_args, **_kwargs: _FakeResponse(401, {"error": "invalid"}))
    monkeypatch.setattr(app_module_fixture, "get_db", lambda: _FakeConn(admin_row=None))

    client = app_module_fixture.app.test_client()
    resp = client.post("/set_session", json={"access_token": "bad-token"})

    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Invalid token"}


def test_set_session_admin_override(monkeypatch, app_module_fixture):
    monkeypatch.setattr(
        app_module_fixture.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(
            200,
            {
                "id": "user-admin",
                "email": "admin@example.com",
                "user_metadata": {"username": "admin-name", "role": "Student"},
            },
        ),
    )
    monkeypatch.setattr(app_module_fixture, "get_db", lambda: _FakeConn(admin_row=(1,)))

    client = app_module_fixture.app.test_client()
    resp = client.post("/set_session", json={"access_token": "token-admin"})

    assert resp.status_code == 200
    assert resp.get_json() == {"success": True}
    with client.session_transaction() as sess:
        assert sess["user_id"] == "user-admin"
        assert sess["username"] == "admin-name"
        assert sess["role"] == "Admin"
        assert sess["admin_level"] == 1
