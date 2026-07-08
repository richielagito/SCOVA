import json
import pytest
from unittest.mock import MagicMock, patch
from scova_backend.utils import db

def test_get_engine_singleton():
    # Test that get_engine returns the same object twice
    with patch('scova_backend.utils.db.create_engine') as mock_create:
        mock_create.return_value = MagicMock()
        # Reset _engine
        db._engine = None
        
        e1 = db.get_engine()
        e2 = db.get_engine()
        
        assert e1 is e2
        mock_create.assert_called_once()

def test_simpan_ke_postgres_basic():
    mock_conn = MagicMock()
    results = [
        {
            "name": "Budi",
            "similarity": 0.85,
            "grade": 85,
            "user_id": "u1",
            "kelas_id": 10,
            "file_path": "path/to/file.pdf"
        }
    ]
    
    db.simpan_ke_postgres(results, conn=mock_conn)
    
    assert mock_conn.execute.called
    args, kwargs = mock_conn.execute.call_args
    # First arg is the query, second is params
    params = args[1]
    assert len(params) == 1
    assert params[0]['name'] == "Budi"
    assert params[0]['similarity'] == 0.85
    assert params[0]['status'] == "draft" # Default value

def test_simpan_ke_postgres_empty():
    mock_conn = MagicMock()
    db.simpan_ke_postgres([], conn=mock_conn)
    assert not mock_conn.execute.called

def test_fetch_all_results_success():
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value = [
        {"id": 1, "nama_murid": "Budi", "similarity": "0.85", "nilai": 85}
    ]
    mock_conn.execute.return_value = mock_result
    
    with patch('scova_backend.utils.db.get_engine') as mock_engine:
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        
        res = db.fetch_all_results("u1")
        assert len(res) == 1
        assert res[0]["nama_murid"] == "Budi"
        assert res[0]["similarity"] == 0.85 # converted to float

def test_fetch_all_results_failure():
    with patch('scova_backend.utils.db.get_engine') as mock_engine:
        mock_engine.return_value.connect.side_effect = Exception("DB error")
        res = db.fetch_all_results("u1")
        assert res == []

def test_simpan_ke_postgres_no_conn():
    results = [{"name": "Budi", "similarity": 0.85, "grade": 85, "user_id": "u1", "kelas_id": 10, "file_path": "f"}]
    mock_conn = MagicMock()
    with patch('scova_backend.utils.db.get_engine') as mock_engine:
        mock_engine.return_value.begin.return_value.__enter__.return_value = mock_conn
        db.simpan_ke_postgres(results, conn=None)
        assert mock_conn.execute.called

def test_fetch_results_by_kelas():
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value = []
    mock_conn.execute.return_value = mock_result
    
    with patch('scova_backend.utils.db.get_engine') as mock_engine:
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        res = db.fetch_results_by_kelas(10, status="published")
        assert res == []
        assert "status = :status" in mock_conn.execute.call_args[0][0].text

def test_fetch_results_by_kode_kelas_not_found():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = None
    
    with patch('scova_backend.utils.db.get_engine') as mock_engine:
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        res = db.fetch_results_by_kode_kelas("KODE1", "u1")
        assert res == []

def test_fetch_results_by_kode_kelas_success():
    mock_conn = MagicMock()
    # First call: SELECT c.id
    # Second call: SELECT hp.*
    mock_conn.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(10,))),
        MagicMock(mappings=MagicMock(return_value=[{"nama_murid": "Budi", "similarity": "0.9"}]))
    ]
    
    with patch('scova_backend.utils.db.get_engine') as mock_engine:
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        res = db.fetch_results_by_kode_kelas("KODE1", "u1")
        assert len(res) == 1
        assert res[0]["similarity"] == 0.9

def test_fetch_results_by_assignment_id():
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value = [{"similarity": "0.8"}]
    mock_conn.execute.return_value = mock_result
    
    with patch('scova_backend.utils.db.get_engine') as mock_engine:
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        res = db.fetch_results_by_assignment_id(123)
        assert len(res) == 1
        assert res[0]["similarity"] == 0.8
