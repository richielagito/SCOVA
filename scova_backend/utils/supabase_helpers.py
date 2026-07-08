
from typing import Optional
from urllib.parse import urlparse, parse_qs
import mimetypes

from supabase import Client, create_client
import os as _os


class SupabaseStorageError(Exception):
    """General supabase storage error with original exception attached."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class SupabaseDownloadError(SupabaseStorageError):
    """Raised when download fails or returns unexpected result."""


def _require_env(name: str) -> str:
    value = _os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_server_supabase_client() -> Client:
    """Lazily create a server supabase client using environment variables.

    Do not call this at import time in libraries that run during tests which do not set env.
    Tests may pass a client instance directly to helpers.
    """
    supabase_url = _require_env("SUPABASE_URL")
    supabase_secret_key = _require_env("SUPABASE_SECRET_KEY")
    return create_client(supabase_url, supabase_secret_key)


def get_publishable_key() -> str:
    # Return publishable key from environment. Tests should set this via monkeypatch.setenv
    return _require_env("SUPABASE_PUBLISHABLE_KEY")


def get_public_path(public_url: str) -> str:
    """Extract the storage path from a Supabase public URL.

    Compatible with URLs like:
      https://<project>.supabase.co/storage/v1/object/public/uploads/path/to/file.pdf
    or with query params. Returns the path inside the 'uploads' bucket (no leading slash).
    If the URL is already a path (no scheme), returns it unchanged.
    """
    if not public_url:
        return ""
    # If looks like a path already, just return
    if not public_url.startswith("http") and not public_url.startswith("/"):
        return public_url

    try:
        parsed = urlparse(public_url)
        # path like /storage/v1/object/public/uploads/... -> split after '/object/public/uploads/'
        path = parsed.path
        marker = '/object/public/uploads/'
        if marker in path:
            return path.split(marker, 1)[1]
        # fallback: maybe path directly under /uploads/
        marker2 = '/uploads/'
        if marker2 in path:
            return path.split(marker2, 1)[1]
        # If query contains "path" param
        qs = parse_qs(parsed.query)
        if 'path' in qs and qs['path']:
            return qs['path'][0]
    except Exception:
        pass
    return ''


def upload_file(
    file_bytes: bytes,
    dest_path: str,
    client: Optional[Client] = None,
    bucket: str = 'uploads',
) -> str:
    """Upload bytes to Supabase storage and return the public URL.

    If object exists, attempt update. On other errors raise SupabaseStorageError.
    Accepts an optional supabase client for test injection.
    """
    if client is None:
        client = get_server_supabase_client()

    content_type, _ = mimetypes.guess_type(dest_path)
    if not content_type:
        content_type = 'application/octet-stream'
        
    file_options = {"content-type": content_type}

    try:
        res = client.storage.from_(bucket).upload(dest_path, file_bytes, file_options=file_options)
    except Exception as e:
        # detect object-exists by message substring (mocked tests rely on this)
        msg = str(e).lower()
        if 'already exists' in msg or 'object already exists' in msg:
            try:
                res = client.storage.from_(bucket).update(dest_path, file_bytes, file_options=file_options)
            except Exception as e2:
                raise SupabaseStorageError(f"Failed to update existing object '{dest_path}': {e2}", e2)
        else:
            raise SupabaseStorageError(f"Failed to upload object '{dest_path}': {e}", e)

    try:
        public = client.storage.from_(bucket).get_public_url(dest_path)
        return public
    except Exception as e:
        raise SupabaseStorageError(f"Upload succeeded but failed to get public URL for '{dest_path}': {e}", e)


def download_file(
    public_url_or_path: str,
    client: Optional[Client] = None,
    bucket: str = 'uploads',
) -> bytes:
    """Download from Supabase storage using either a public URL or a storage path.

    On failure raise SupabaseDownloadError.
    """
    if client is None:
        client = get_server_supabase_client()

    # Determine if input is a URL or a path
    path = public_url_or_path
    if public_url_or_path.startswith('http'):
        path = get_public_path(public_url_or_path)

    if not path:
        raise SupabaseDownloadError(f"Invalid path or public URL: '{public_url_or_path}'")

    try:
        data = client.storage.from_(bucket).download(path)
        # Expect bytes-like result
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        # Some SDKs may return a response-like object with .read()
        if hasattr(data, 'read'):
            return data.read()
        raise SupabaseDownloadError(f"Unexpected download result type for path '{path}': {type(data)}")
    except SupabaseDownloadError:
        raise
    except Exception as e:
        raise SupabaseDownloadError(f"Failed to download '{path}': {e}", e)
