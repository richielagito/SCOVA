import pytest
from unittest.mock import MagicMock
import json
import datetime

@pytest.fixture
def admin_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 'admin-123'
        sess['role'] = 'Admin'
    return client

@pytest.fixture
def teacher_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 'teacher-123'
        sess['role'] = 'Teacher'
    return client

# 1. /api/class/update
def test_api_update_class_success(client, make_fake_db):
    make_fake_db([]) # Success doesn't return anything from begin() txn
    payload = {"kode_kelas": "ABCDEF", "nama_kelas": "New Name"}
    rv = client.post('/api/class/update', json=payload)
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_api_update_class_admin(admin_client, make_fake_db):
    make_fake_db([])
    payload = {"kode_kelas": "ABCDEF", "nama_kelas": "Admin New Name"}
    rv = admin_client.post('/api/class/update', json=payload)
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_api_update_class_invalid_data(client):
    rv = client.post('/api/class/update', json={})
    assert rv.status_code == 400
    assert 'error' in rv.get_json()

# 2. /api/class/delete
def test_api_delete_class_success(client, make_fake_db):
    # 1. SELECT id FROM classes (fetchone)
    # 2. DELETE FROM hasil_penilaian
    # 3. DELETE FROM assignments
    # 4. DELETE FROM classes
    make_fake_db([(123,)])
    payload = {"kode_kelas": "ABCDEF"}
    rv = client.post('/api/class/delete', json=payload)
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_api_delete_class_not_found(client, make_fake_db):
    make_fake_db([[]])
    payload = {"kode_kelas": "NONEXIST"}
    rv = client.post('/api/class/delete', json=payload)
    assert rv.status_code == 404

from unittest.mock import MagicMock, patch

# 3. /api/results & variants
def test_api_results(client, monkeypatch):
    import scova_backend.utils.db as db_utils
    import uploaditin_backend.app as app_module
    mock_engine = MagicMock()
    mock_row = (1, 10, "Student A", "url", "draft", "text", "uid", 101, 1, 90, 0.9, "fb", datetime.datetime.now(), datetime.datetime.now(), "Admin", "published")
    mock_engine.connect.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = [mock_row]
    # Patch BOTH modules
    monkeypatch.setattr(db_utils, "get_engine", lambda: mock_engine)
    monkeypatch.setattr(app_module, "get_engine", lambda: mock_engine)
    
    rv = client.get('/api/results')
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data) == 1

def test_api_results_by_kelas(client, monkeypatch):
    import scova_backend.utils.db as db_utils
    import uploaditin_backend.app as app_module
    mock_engine = MagicMock()
    mock_row = (1, 10, "Student B", "url", "draft", "text", "uid", 101, 1, 85, 0.85, "fb", datetime.datetime.now(), datetime.datetime.now(), "Admin", "published")
    mock_engine.connect.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = [mock_row]
    monkeypatch.setattr(db_utils, "get_engine", lambda: mock_engine)
    monkeypatch.setattr(app_module, "get_engine", lambda: mock_engine)
    
    rv = client.get('/api/results/kelas/123')
    assert rv.status_code == 200
    assert rv.get_json()[0]['nama_murid'] == "Student B"

def test_api_results_by_kode_kelas(client, monkeypatch):
    import scova_backend.utils.db as db_utils
    import uploaditin_backend.app as app_module
    mock_engine = MagicMock()
    mock_row = (1, 10, "Student C", "url", "draft", "text", "uid", 101, 1, 80, 0.8, "fb", datetime.datetime.now(), datetime.datetime.now(), "Admin", "published")
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    mock_conn.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(101,))),
        MagicMock(fetchall=MagicMock(return_value=[mock_row]))
    ]
    monkeypatch.setattr(db_utils, "get_engine", lambda: mock_engine)
    monkeypatch.setattr(app_module, "get_engine", lambda: mock_engine)
    
    rv = client.get('/api/results/kelas-kode/ABCDEF')
    assert rv.status_code == 200
    assert rv.get_json()[0]['nama_murid'] == "Student C"

def test_api_results_by_assignment(teacher_client, monkeypatch):
    import scova_backend.utils.db as db_utils
    import uploaditin_backend.app as app_module
    mock_engine = MagicMock()
    mock_row = (1, 10, "Student D", "url", "draft", "text", "uid", 101, 1, 75, 0.75, "fb", datetime.datetime.now(), datetime.datetime.now(), "Admin", "published")
    mock_engine.connect.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = [mock_row]
    monkeypatch.setattr(db_utils, "get_engine", lambda: mock_engine)
    monkeypatch.setattr(app_module, "get_engine", lambda: mock_engine)
    
    rv = teacher_client.get('/api/results/assignment/10')
    assert rv.status_code == 200
    assert rv.get_json()[0]['nama_murid'] == "Student D"

# Redirect tests
def test_admin_dashboard_redirect(client):
    import uploaditin_backend.app as app_module
    with app_module.app.test_client() as guest:
        rv = guest.get('/admin')
        assert rv.status_code == 302
        assert '/login_register' in rv.location

def test_admin_classes_view_redirect(client):
    import uploaditin_backend.app as app_module
    with app_module.app.test_client() as guest:
        rv = guest.get('/admin/classes')
        assert rv.status_code == 302

def test_admin_users_view_redirect(client):
    import uploaditin_backend.app as app_module
    with app_module.app.test_client() as guest:
        rv = guest.get('/admin/users')
        assert rv.status_code == 302

# 4. /api/upload/delete
def test_api_delete_upload_success(client, make_fake_db):
    make_fake_db([(1,)]) # existing check
    rv = client.post('/api/upload/delete', json={"id": 1})
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_api_delete_upload_not_found(client, make_fake_db):
    make_fake_db([[]])
    rv = client.post('/api/upload/delete', json={"id": 999})
    assert rv.status_code == 404

# 5. /api/join-class
def test_api_join_class_success(client, make_fake_db):
    # 1. SELECT id, nama_kelas FROM classes
    # 2. SELECT 1 FROM murid_kelas (already joined) -> None
    # 3. INSERT INTO murid_kelas
    make_fake_db([(101, "Test Class"), []])
    rv = client.post('/api/join-class', json={"kode_kelas": "ABCDEF"})
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_api_join_class_already_joined(client, make_fake_db):
    make_fake_db([(101, "Test Class"), (1,)])
    rv = client.post('/api/join-class', json={"kode_kelas": "ABCDEF"})
    assert rv.status_code == 400
    assert 'sudah join' in rv.get_json()['error']

# 6. /api/joined-classes
def test_api_joined_classes(client, make_fake_db):
    make_fake_db([[("Class A", "CODEA"), ("Class B", "CODEB")]])
    rv = client.get('/api/joined-classes')
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data) == 2
    assert data[0]['nama_kelas'] == "Class A"

# 7. /api/assignments (POST)
def test_api_add_assignment_success(teacher_client, make_fake_db, patch_upload_and_download):
    make_fake_db([(555,)]) # RETURNING id
    data = {
        'judulAssignment': 'Homework 1',
        'deskripsiAssignment': 'Do it',
        'deadlineAssignment': '2025-12-31 23:59',
        'kelas_id': '101'
    }
    # Mock files
    import io
    files = {
        'fileAssignment': (io.BytesIO(b"assignment"), 'hw1.pdf'),
        'jawabanGuru': (io.BytesIO(b"answer"), 'ans1.pdf')
    }
    rv = teacher_client.post('/api/assignments', data=data, content_type='multipart/form-data')
    # Wait, I need to pass files correctly
    rv = teacher_client.post('/api/assignments', data={**data, **files}, content_type='multipart/form-data')
    assert rv.status_code == 200
    assert rv.get_json()['assignment_id'] == 555

# 8. /api/assignments/<kode_kelas> (GET)
def test_api_get_assignments(client, make_fake_db):
    # 1. SELECT id FROM classes
    # 2. SELECT a.id, ... FROM assignments
    import datetime
    mock_assignments = [
        (1, "HW1", "Desc", datetime.datetime.now(), "path1", "path2", datetime.datetime.now(), False, True, 1)
    ]
    make_fake_db([(101,), mock_assignments])
    rv = client.get('/api/assignments/ABCDEF')
    assert rv.status_code == 200
    assert len(rv.get_json()) == 1

# 9. /api/assignments/publish/<int:assignment_id>
def test_api_publish_assignment(teacher_client, make_fake_db):
    make_fake_db([])
    rv = teacher_client.post('/api/assignments/publish/1', json={"is_published": True})
    assert rv.status_code == 200
    assert "dipublikasikan" in rv.get_json()['message']

# 10. /api/assignments/upload/<int:assignment_id>
def test_api_upload_student_answer(client, make_fake_db, patch_upload_and_download, patch_extract_text_and_score, capture_simpan):
    # 1. SELECT kelas_id, jawaban_path, judul, deadline FROM assignments
    # 2. SELECT nama_kelas FROM classes
    # 3. SELECT MAX(version) FROM hasil_penilaian
    import datetime
    make_fake_db([
        (101, "guru_url", "HW1", datetime.datetime.now() + datetime.timedelta(days=1)),
        ("Math Class",),
        (0,)
    ])
    
    import io
    files = {'file': (io.BytesIO(b"student answer"), 'answer.pdf')}
    rv = client.post('/api/assignments/upload/1', data=files, content_type='multipart/form-data')
    assert rv.status_code == 200
    assert capture_simpan['args'][0][0]['status'] == "pending"

# 11. /api/submissions/grade/<submission_id>
def test_api_grade_submission(teacher_client, make_fake_db, patch_upload_and_download, patch_extract_text_and_score, capture_simpan):
    # 1. SELECT id, assignment_id, ... FROM hasil_penilaian
    # 2. SELECT kelas_id, jawaban_path, judul, deadline FROM assignments
    # 3. SELECT MAX(version) FROM hasil_penilaian (inside _perform_ai_grading)
    import datetime
    submission_row = (1, 10, "Student X", "murid_url", "pending", "essay text", "user-123", 101)
    assignment_row = (101, "guru_url", "HW1", datetime.datetime.now() - datetime.timedelta(days=1)) # past deadline
    
    make_fake_db([
        submission_row,
        assignment_row,
        (0,) 
    ])
    
    rv = teacher_client.post('/api/submissions/grade/1')
    assert rv.status_code == 200
    assert capture_simpan['args'][0][0]['status'] == "draft"

# 12. /api/assignments/grade-bulk/<int:assignment_id>
def test_api_grade_bulk(teacher_client, make_fake_db, patch_upload_and_download, patch_extract_text_and_score, capture_simpan):
    # 1. SELECT ... FROM assignments
    # 2. SELECT ... FROM hasil_penilaian (pending)
    # 3. SELECT MAX(version) FROM hasil_penilaian (inside _perform_ai_grading)
    import datetime
    assignment_row = (101, "guru_url", "HW1", datetime.datetime.now() - datetime.timedelta(days=1))
    pending_submissions = [
        (1, 10, "Student 1", "url1", "pending", "text1", "u1", 101),
        (2, 10, "Student 2", "url2", "pending", "text2", "u2", 101)
    ]
    
    make_fake_db([
        assignment_row,
        pending_submissions,
        (0,), # max version for sub 1
        (0,)  # max version for sub 2
    ])
    
    rv = teacher_client.post('/api/assignments/grade-bulk/10')
    assert rv.status_code == 200
    assert rv.get_json()['processed_count'] == 2

# 13. /api/results/override
def test_api_override_result(teacher_client, make_fake_db):
    make_fake_db([])
    payload = {
        "id": 1,
        "grade": 95,
        "feedback": "Excellent",
        "status": "published"
    }
    rv = teacher_client.post('/api/results/override', json=payload)
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

# Additional tests for error paths
def test_api_undo_submission(client, make_fake_db):
    # 1. SELECT deadline FROM assignments
    # 2. SELECT id FROM hasil_penilaian
    # 3. UPDATE hasil_penilaian
    import datetime
    make_fake_db([
        (datetime.datetime.now() + datetime.timedelta(days=1),), # deadline
        (1,) # submission id
    ])
    rv = client.post('/api/submissions/undo/10')
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_api_delete_assignment(teacher_client, make_fake_db, patch_upload_and_download):
    make_fake_db([("file_url", "ans_url")])
    
    mock_supabase = MagicMock()
    mock_from = MagicMock()
    mock_supabase.storage.from_.return_value = mock_from
    
    with patch('uploaditin_backend.app._get_supabase', return_value=mock_supabase):
        rv = teacher_client.delete('/api/assignments/1')
        assert rv.status_code == 200
        assert rv.get_json()['success'] is True
        assert mock_supabase.storage.from_.called
        assert mock_from.remove.called

