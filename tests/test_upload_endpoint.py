import io
import json
import pytest

import uploaditin_backend.app as app_module


def _make_file_tuple(tmp_file):
    bio, name = tmp_file
    bio.seek(0)
    return (name, bio, 'application/pdf')


def test_happy_path(client, tmp_file, make_fake_db, patch_upload_and_download, patch_extract_text_and_score, capture_simpan):
    # Prepare DB to return kelas_id, jawaban_path, judul when selecting assignment
    make_fake_db([(1, 'https://supabase.test/storage/v1/object/public/uploads/answers/teacher/guru.pdf', 'Soal 1', None)])

    data = {
        'file': (tmp_file[0], tmp_file[1])
    }

    # Flask test client expects file tuple as (fileobj, filename)
    file_obj = io.BytesIO(b"dummy content")
    file_obj.name = 'student_submission.pdf'

    rv = client.post('/api/assignments/upload/123', data={
        'file': (file_obj, 'student_submission.pdf')
    }, content_type='multipart/form-data')

    assert rv.status_code == 200
    body = rv.get_json()
    assert body['success'] is True
    assert body['status'] == 'pending'
    
    # simpan_ke_postgres should have been called once with list containing dict
    assert len(capture_simpan['args']) == 1
    saved = capture_simpan['args'][0]
    assert isinstance(saved, list) and len(saved) == 1
    item = saved[0]
    for key in ['name', 'similarity', 'grade', 'user_id', 'kelas_id', 'assignment_id', 'file_path', 'feedback']:
        assert key in item
    assert item['feedback'] == "Menunggu penilaian guru."
    assert item['status'] == "pending"


def test_storage_download_failure(client, tmp_file, make_fake_db, patch_upload_and_download, patch_extract_text_and_score, monkeypatch):
    make_fake_db([(1, 'https://supabase.test/storage/v1/object/public/uploads/answers/teacher/guru.pdf', 'Soal 1', None)])

    # make download_file raise SupabaseDownloadError when downloading murid file (happens during upload)
    SupabaseDownloadError = app_module.SupabaseDownloadError

    def bad_download(url, client=None, bucket='uploads'):
        raise SupabaseDownloadError('download failed')

    monkeypatch.setattr(app_module, 'download_file', bad_download)

    file_obj = io.BytesIO(b"dummy content")
    file_obj.name = 'student_submission.pdf'

    rv = client.post('/api/assignments/upload/123', data={
        'file': (file_obj, 'student_submission.pdf')
    }, content_type='multipart/form-data')

    assert rv.status_code == 500
    body = rv.get_json()
    assert 'Gagal mendownload' in body.get('error', '') or 'download' in body.get('error', '').lower()


def test_extraction_failure_returns_400(client, tmp_file, make_fake_db, patch_upload_and_download, patch_extract_text_and_score, monkeypatch, capture_simpan):
    make_fake_db([(1, 'https://supabase.test/storage/v1/object/public/uploads/answers/teacher/guru.pdf', 'Soal 1', None)])

    def bad_extract(path):
        return None

    monkeypatch.setattr(app_module, 'extract_text_from_any', bad_extract)

    file_obj = io.BytesIO(b"dummy content")
    file_obj.name = 'student_submission.pdf'

    rv = client.post('/api/assignments/upload/123', data={
        'file': (file_obj, 'student_submission.pdf')
    }, content_type='multipart/form-data')

    assert rv.status_code == 400
    assert "Format tidak didukung" in rv.get_json()['error']
    assert len(capture_simpan['args']) == 0


def test_db_save_failure_returns_500(client, tmp_file, make_fake_db, patch_upload_and_download, patch_extract_text_and_score, capture_simpan):
    make_fake_db([(1, 'https://supabase.test/storage/v1/object/public/uploads/answers/teacher/guru.pdf', 'Soal 1', None)])
    # instruct capture_simpan to raise
    capture_simpan['raise'] = True

    file_obj = io.BytesIO(b"dummy content")
    file_obj.name = 'student_submission.pdf'

    rv = client.post('/api/assignments/upload/123', data={
        'file': (file_obj, 'student_submission.pdf')
    }, content_type='multipart/form-data')

    assert rv.status_code == 500
    body = rv.get_json()
    assert 'Gagal menyimpan' in body.get('error', '') or 'gagal' in body.get('error', '').lower()
