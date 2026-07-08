import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def teacher_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 'teacher-123'
        sess['role'] = 'Teacher'
    return client

def test_unauthorized_endpoints(client):
    import uploaditin_backend.app as app_module
    with app_module.app.test_client() as guest:
        assert guest.get('/api/results').status_code == 401
        assert guest.get('/api/assignments/ABCDEF').status_code == 401
        assert guest.get('/api/assignments/1').status_code == 401
        assert guest.post('/api/class/update').status_code == 401
        assert guest.post('/api/class/delete').status_code == 401
        assert guest.post('/api/join-class').status_code == 401
        assert guest.get('/admin').status_code == 302
        assert guest.get('/admin/classes').status_code == 302
        assert guest.get('/admin/users').status_code == 302

def test_api_assignment_not_found(teacher_client, make_fake_db):
    # get_assignment_detail -> 1. class check, 2. assignment check
    make_fake_db([(1,), []])
    rv = teacher_client.get('/api/assignments/999')
    assert rv.status_code == 404
    assert "Assignment tidak ditemukan" in rv.get_json()['error']

def test_api_delete_assignment_not_found(teacher_client, make_fake_db):
    make_fake_db([[]])
    rv = teacher_client.delete('/api/assignments/999')
    assert rv.status_code == 404

def test_api_results_by_kode_kelas_not_found(client, make_fake_db):
    make_fake_db([[]])
    rv = client.get('/api/results/kelas-kode/NONEXIST')
    assert rv.status_code == 200
    assert rv.get_json() == []

def test_api_grading_unauthorized(client):
    rv = client.post('/api/assignments/grade-bulk/1')
    assert rv.status_code == 401

def test_api_publish_missing(teacher_client, make_fake_db):
    make_fake_db([[]])
    rv = teacher_client.post('/api/assignments/publish/999', json={'is_published': True})
    assert rv.status_code == 404

def test_api_upload_jawaban_missing_assignment(client, make_fake_db):
    make_fake_db([[]])
    rv = client.post('/api/assignments/upload/999', data={'essay_text': 'test'})
    assert rv.status_code == 404

def test_api_grading_missing_assignment(teacher_client, make_fake_db):
    make_fake_db([[]])
    rv = teacher_client.post('/api/assignments/grade-bulk/999')
    assert rv.status_code == 404
