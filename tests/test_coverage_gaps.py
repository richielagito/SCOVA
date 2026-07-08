import pytest
from unittest.mock import MagicMock
from scova_backend.utils.supabase_helpers import get_public_path, upload_file, download_file, SupabaseStorageError, SupabaseDownloadError

@pytest.fixture
def admin_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 'admin-123'
        sess['role'] = 'Admin'
    return client

def test_promote_user_success(admin_client, make_fake_db):
    # Mock existing admin check (returns None to trigger insert)
    make_fake_db([[], []])
    
    rv = admin_client.post('/api/admin/promote', json={'user_id': 'user-456'})
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_promote_user_update(admin_client, make_fake_db):
    # Mock existing admin check (returns something to trigger update)
    make_fake_db([(1,), []])
    
    rv = admin_client.post('/api/admin/promote', json={'user_id': 'user-456'})
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_promote_user_missing_id(admin_client):
    rv = admin_client.post('/api/admin/promote', json={})
    assert rv.status_code == 400

def test_deactivate_user_success(admin_client, make_fake_db):
    make_fake_db([[]])
    rv = admin_client.post('/api/admin/deactivate', json={'user_id': 'user-456'})
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_admin_delete_user_missing_id(admin_client):
    rv = admin_client.post('/api/admin/delete-user', json={})
    assert rv.status_code == 400

def test_admin_summary_db_error(admin_client, monkeypatch):
    import uploaditin_backend.app as app_module
    def mock_get_db():
        raise Exception("DB Down")
    monkeypatch.setattr(app_module, 'get_db', mock_get_db)
    
    rv = admin_client.get('/api/admin/summary')
    assert rv.status_code == 500
    assert "Gagal mengambil statistik admin" in rv.get_json()['error']

def test_get_public_path_variations():
    # Empty
    assert get_public_path("") == ""
    # Path already
    assert get_public_path("my/path.pdf") == "my/path.pdf"
    # Marker 1
    url1 = "https://x.supabase.co/storage/v1/object/public/uploads/folder/file.pdf"
    assert get_public_path(url1) == "folder/file.pdf"
    # Marker 2
    url2 = "https://x.supabase.co/uploads/other/file.docx"
    assert get_public_path(url2) == "other/file.docx"
    # Query param
    url3 = "https://example.com/download?path=query/path.txt"
    assert get_public_path(url3) == "query/path.txt"
    # Invalid
    assert get_public_path("http://invalid.com") == ""

def test_upload_file_update_on_exists(monkeypatch):
    mock_client = MagicMock()
    # First upload fails with 'already exists'
    mock_client.storage.from_().upload.side_effect = Exception("Object already exists")
    mock_client.storage.from_().update.return_value = {"path": "dest/path.pdf"}
    mock_client.storage.from_().get_public_url.return_value = "http://pub.url"
    
    url = upload_file(b"content", "dest/path.pdf", client=mock_client)
    assert url == "http://pub.url"
    assert mock_client.storage.from_().update.called

def test_upload_file_error(monkeypatch):
    mock_client = MagicMock()
    mock_client.storage.from_().upload.side_effect = Exception("General failure")
    
    with pytest.raises(SupabaseStorageError) as exc:
        upload_file(b"content", "dest/path.pdf", client=mock_client)
    assert "Failed to upload" in str(exc.value)

def test_download_file_invalid_path():
    with pytest.raises(SupabaseDownloadError) as exc:
        download_file("http://invalid.com", client=MagicMock())
    assert "Invalid path" in str(exc.value)

def test_download_file_unexpected_type():
    mock_client = MagicMock()
    mock_client.storage.from_().download.return_value = 12345 # Not bytes
    
    with pytest.raises(SupabaseDownloadError) as exc:
        download_file("path/to/file", client=mock_client)
    assert "Unexpected download result type" in str(exc.value)

def test_download_file_read_attr():
    mock_client = MagicMock()
    mock_data = MagicMock()
    mock_data.read.return_value = b"streamed content"
    # Delete __bytes__ if present to ensure it uses .read()
    if hasattr(mock_data, '__bytes__'): del mock_data.__bytes__
    
    mock_client.storage.from_().download.return_value = mock_data
    
    assert download_file("path/to/file", client=mock_client) == b"streamed content"
