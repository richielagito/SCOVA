import pytest

from uploaditin_backend.utils import supabase_helpers as sh


class DummyStorage:
    def __init__(self):
        self._store = {}

    def upload(self, path, data, file_options=None):
        if path in self._store:
            raise Exception("Object already exists")
        self._store[path] = data
        return {"key": path}

    def update(self, path, data, file_options=None):
        self._store[path] = data
        return {"key": path}

    def get_public_url(self, path):
        return f"https://example.supabase.co/storage/v1/object/public/uploads/{path}"

    def download(self, path):
        if path not in self._store:
            raise Exception("Not found")
        return self._store[path]



@pytest.fixture
def dummy_client():
    # Provide an object where client.storage.from_(bucket) returns storage
    class C:
        def __init__(self):
            self._storage = DummyStorage()
            class StorageWrapper:
                def __init__(self, inst):
                    self._inst = inst

                def from_(self, bucket):
                    return self._inst._storage

            self.storage = StorageWrapper(self)

    return C()


def test_upload_success_returns_public_url(dummy_client):
    data = b"hello"
    url = sh.upload_file(data, "path/file.txt", client=dummy_client)
    assert url.endswith("/uploads/path/file.txt")


def test_upload_existing_calls_update(dummy_client):
    data1 = b"first"
    data2 = b"second"
    # pre-populate
    dummy_client.storage.from_("uploads")._store = {}
    dummy_client.storage.from_("uploads")._store["path/exist.txt"] = data1

    url = sh.upload_file(data2, "path/exist.txt", client=dummy_client)
    assert url.endswith("/uploads/path/exist.txt")
    # ensure data updated
    assert dummy_client.storage.from_("uploads")._store["path/exist.txt"] == data2


def test_download_success_returns_bytes(dummy_client):
    # populate store
    dummy_client.storage.from_("uploads")._store["some/file.pdf"] = b"pdfbytes"
    result = sh.download_file("https://example.supabase.co/storage/v1/object/public/uploads/some/file.pdf", client=dummy_client)
    assert result == b"pdfbytes"


def test_download_missing_raises(dummy_client):
    with pytest.raises(sh.SupabaseDownloadError):
        sh.download_file("https://example.supabase.co/storage/v1/object/public/uploads/missing.pdf", client=dummy_client)


def test_require_env_missing_raises(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(RuntimeError, match="Missing required environment variable: MISSING_VAR"):
        sh._require_env("MISSING_VAR")
