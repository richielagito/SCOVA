import json
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import text

@pytest.fixture
def admin_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 'admin-123'
        sess['role'] = 'Admin'
    return client

def test_admin_summary_unauthorized(client):
    rv = client.get('/api/admin/summary')
    assert rv.status_code == 401

def test_admin_summary_success(admin_client, monkeypatch):
    mock_conn = MagicMock()
    # Order in app.py: total_users, total_classes, total_uploads, active_admins
    mock_conn.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=100)),
        MagicMock(scalar=MagicMock(return_value=20)),
        MagicMock(scalar=MagicMock(return_value=500)),
        MagicMock(scalar=MagicMock(return_value=5))
    ]
    
    import uploaditin_backend.app as app_module
    monkeypatch.setattr(app_module, 'get_db', lambda: mock_conn)
    
    rv = admin_client.get('/api/admin/summary')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['total_users'] == 100
    assert data['active_admins'] == 5
    assert data['total_classes'] == 20
    assert data['total_uploads'] == 500

def test_admin_users_list(admin_client, monkeypatch):
    mock_conn = MagicMock()
    import datetime
    mock_rows = [
        ('u1', 'user1@test.com', datetime.datetime.now(), True),
        ('u2', 'user2@test.com', datetime.datetime.now(), False)
    ]
    mock_conn.execute.return_value.fetchall.return_value = mock_rows
    
    import uploaditin_backend.app as app_module
    monkeypatch.setattr(app_module, 'get_db', lambda: mock_conn)
    
    rv = admin_client.get('/api/admin/users')
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data) == 2
    assert data[0]['id'] == 'u1'
    assert data[0]['is_admin'] is True

def test_api_admin_landing_get(admin_client, monkeypatch):
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = [
        ('hero', json.dumps({"title": "Hello"}))
    ]
    
    import uploaditin_backend.app as app_module
    monkeypatch.setattr(app_module, 'get_db', lambda: mock_conn)
    
    rv = admin_client.get('/api/admin/landing')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['hero']['title'] == "Hello"

def test_api_admin_landing_post(admin_client, monkeypatch):
    mock_engine = MagicMock()
    mock_txn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_txn
    
    import uploaditin_backend.app as app_module
    monkeypatch.setattr(app_module, 'get_engine', lambda: mock_engine)
    
    payload = {"hero": {"title": "New Title"}}
    rv = admin_client.post('/api/admin/landing', json=payload)
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True
    assert mock_txn.execute.called

def test_create_class_unauthorized(client):
    import uploaditin_backend.app as app_module
    # Use a fresh client without the authenticated session from the fixture
    with app_module.app.test_client() as guest_client:
        rv = guest_client.post('/create-class', data={'class_name': 'Test'})
        assert rv.status_code == 401

def test_create_class_success(admin_client, make_fake_db):
    # Mocking check for existing kode_kelas in generate_unique_class_code (get_db)
    # AND the actual insertion (get_engine.begin)
    # generate_unique_class_code needs a None for fetchone to break loop -> use []
    # insertion needs a [kelas_id] for RETURNING id -> use (123,)
    make_fake_db([[], (123,)])
    
    payload = {'class_name': 'Math 101'}
    rv = admin_client.post('/create-class', data=payload)
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'class_code' in data
    assert data['kelas_id'] == 123
