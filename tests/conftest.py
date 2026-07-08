import io
import itertools
import os
import pytest

os.environ.setdefault('DB_USER', 'test_user')
os.environ.setdefault('DB_PASSWORD', 'test_password')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('GEMINI_API_KEY', 'dummy-key-for-testing')
os.environ.setdefault('DB_NAME', 'test_db')
os.environ['SCORING_ENGINE'] = 'legacy'
os.environ.setdefault('FLASK_SECRET_KEY', 'test-secret-key-for-tests')

import uploaditin_backend.app as app_module


class FakeResult:
    def __init__(self, results):
        self._results = [tuple(r) if isinstance(r, (list, tuple)) else (r,) for r in results]

    def fetchone(self):
        if not self._results:
            return None
        return self._results.pop(0)

    def scalar(self):
        val = self.fetchone()
        return val[0] if val else None

    def fetchall(self):
        res = self._results
        self._results = []
        return res


class FakeConn:
    def __init__(self, fetchone_results):
        self.results = fetchone_results

    def execute(self, *args, **kwargs):
        if not self.results:
            return FakeResult([])
        res = self.results.pop(0)
        # If it's a list (for fetchall), pass as is to FakeResult
        # If it's a tuple (for fetchone), wrap in list
        if isinstance(res, list):
            return FakeResult(res)
        else:
            return FakeResult([res])

    def close(self):
        return


@pytest.fixture
def client():
    app_module.app.config.setdefault('TESTING', True)
    with app_module.app.test_client() as client:
        # set authenticated session for tests
        with client.session_transaction() as sess:
            sess['user_id'] = 42
            sess['username'] = 'test_user'
            sess['role'] = 'Student'
        yield client


@pytest.fixture
def tmp_file():
    """Return a small in-memory file-like and a filename for upload payloads."""
    return (io.BytesIO(b"dummy file content"), "student_submission.pdf")


@pytest.fixture
def make_fake_db(monkeypatch):
    """Provide helper to inject a fake DB connection that returns supplied fetchone values."""

    def _make(fetchone_results):
        conn = FakeConn(fetchone_results)

        def _get_db():
            return conn

        class FakeEngine:
            def connect(self):
                return conn
            def begin(self):
                from contextlib import contextmanager
                @contextmanager
                def _begin():
                    yield conn
                return _begin()

        fake_engine = FakeEngine()

        def _get_engine():
            return fake_engine

        monkeypatch.setattr(app_module, 'get_db', _get_db)
        monkeypatch.setattr(app_module, 'get_engine', _get_engine)
        return conn

    return _make


@pytest.fixture(autouse=True)
def patch_tempfile_and_remove(monkeypatch):
    """Avoid real disk IO: patch tempfile.NamedTemporaryFile used in app to return in-memory file-like objects,
    and patch os.remove to a no-op that records calls."""
    import types

    counter = itertools.count()


    class FakeTempFile:
        def __init__(self, delete=False, suffix=None):
            self._buf = io.BytesIO()
            self._id = next(counter)
            self.name = f"/tmp/fake_temp_{self._id}{suffix or ''}"

        def write(self, b):
            return self._buf.write(b)

        def flush(self):
            return None

        def read(self):
            self._buf.seek(0)
            return self._buf.read()

        def close(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_named_tempfile(delete=False, suffix=None):
        return FakeTempFile(delete=delete, suffix=suffix)

    import tempfile
    monkeypatch.setattr(tempfile, 'NamedTemporaryFile', fake_named_tempfile)

    removed = []

    def fake_remove(path):
        removed.append(path)

    import os
    monkeypatch.setattr(os, 'remove', fake_remove)

    yield {'removed': removed}


@pytest.fixture
def capture_simpan(monkeypatch):
    """Capture calls to simpan_ke_postgres and allow forcing an exception via attribute."""
    calls = {'args': []}

    def fake_simpan(results, conn=None):
        calls['args'].append(results)
        if calls.get('raise'):
            raise Exception('DB save failed')

    monkeypatch.setattr(app_module, 'simpan_ke_postgres', fake_simpan)
    return calls


@pytest.fixture
def patch_upload_and_download(monkeypatch):
    """Patch upload_file and download_file in the app module to deterministic behaviors."""

    def upload_file(file_bytes, dest_path, client=None):
        # return a predictable public URL that includes dest_path
        return f"https://supabase.test/storage/v1/object/public/uploads/{dest_path}"

    def download_file(public_url_or_path, client=None, bucket='uploads'):
        # return deterministic bytes content
        if 'guru' in public_url_or_path:
            return b"guru pdf bytes"
        return b"murid pdf bytes"

    monkeypatch.setattr(app_module, 'upload_file', upload_file)
    monkeypatch.setattr(app_module, 'download_file', download_file)
    # ensure _get_supabase does not attempt to create real client during tests
    monkeypatch.setattr(app_module, '_get_supabase', lambda: object())
    return {'upload': upload_file, 'download': download_file}


@pytest.fixture
def patch_extract_text_and_score(monkeypatch):
    """Patch text extraction and scorer to deterministic results; tests override as needed."""
    calls = {'extract_calls': []}

    def fake_extract(path):
        calls['extract_calls'].append(path)
        # return simple text depending on filename
        if 'guru' in path:
            return 'guru reference text'
        return 'murid student text'

    def fake_score(ref, stu):
        per_question = [
            {"question": 1, "similarity": 0.823, "grade": 82}
        ]
        return (0.823, 82, per_question)

    monkeypatch.setattr(app_module, 'extract_text_from_any', fake_extract)
    monkeypatch.setattr(app_module, 'lsa_similarity', fake_score)
    
    # Mock feedback generator to avoid real API calls during tests
    monkeypatch.setattr(app_module, 'generate_pedagogical_feedback', 
                       lambda t, s, sc: {"feedback": "Mocked pedagogical feedback", "highlights": []})
    
    return calls


@pytest.fixture(autouse=True)
def mock_genai_client(monkeypatch):
    """Globally mock google.genai.Client to avoid any real API calls."""
    try:
        import google.genai
        from unittest.mock import MagicMock
        
        def fake_embed_content(model, contents, **kwargs):
            mock_response = MagicMock()
            vecs = []
            for _ in contents:
                mock_embedding = MagicMock()
                mock_embedding.values = [0.1, 0.2, 0.3]
                vecs.append(mock_embedding)
            mock_response.embeddings = vecs
            return mock_response

        mock_client_instance = MagicMock()
        mock_client_instance.models.embed_content.side_effect = fake_embed_content
        
        monkeypatch.setattr(google.genai, "Client", lambda **kwargs: mock_client_instance)
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def mock_embedding_client(monkeypatch):
    """Globally mock embedding_client.get_embeddings to avoid 429 errors."""
    try:
        from uploaditin_backend.utils import embedding_client
        
        def fake_get_embeddings(texts, **kwargs):
            return [[0.1, 0.2, 0.3] for _ in texts]
            
        monkeypatch.setattr(embedding_client, "get_embeddings", fake_get_embeddings)
    except ImportError:
        pass
