#app.py:

import csv
import datetime
import json
import logging
import os
import pathlib
import random
import string
import sys
import tempfile
from io import BytesIO, StringIO
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, g, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_cors import CORS
import requests

# Ensure the package's own directory is on sys.path so that `utils.*` imports
# work both when running directly (python app.py / gunicorn app:app from within
# uploaditin_backend/) and when imported as a sub-package from the project root.
_here = pathlib.Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))


from utils.db import (
    fetch_all_results,
    fetch_results_by_assignment_id,
    fetch_results_by_kelas,
    fetch_results_by_kode_kelas,
    get_engine,
    simpan_ke_postgres,
)
from utils.supabase_helpers import (
    SupabaseDownloadError,
    SupabaseStorageError,
    download_file,
    get_public_path,
    get_server_supabase_client,
    upload_file,
)
from utils.LSA import (
    extract_text_from_any,
    lsa_similarity,
)
from utils.embedding_scorer import embedding_score_submission
from utils.feedback_generator import generate_pedagogical_feedback
from utils.highlight_helper import extract_highlights
from sqlalchemy import text

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_allowed_origins_raw = os.getenv("ALLOWED_ORIGINS")
if _allowed_origins_raw is None:
    allowed_origins = ["http://localhost:3000"]
else:
    allowed_origins = [origin.strip() for origin in _allowed_origins_raw.split(",") if origin.strip()]
    if not allowed_origins:
        raise RuntimeError(
            "ALLOWED_ORIGINS is set but does not contain any valid origins. "
            "Provide a comma-separated list of origins, for example: "
            "\"http://localhost:3000,https://example.com\""
        )
CORS(app, origins=allowed_origins)

# --- Security: secret key wajib di-set via environment variable ---
_secret = os.getenv("FLASK_SECRET_KEY")
if not _secret:
    raise RuntimeError(
        "FLASK_SECRET_KEY environment variable harus di-set. "
        "Generate dengan: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
app.secret_key = _secret

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CSV_FOLDER'] = 'data'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CSV_FOLDER'], exist_ok=True)


# ---------------------------------------------------------------------------
# Database helpers — menggunakan flask.g untuk connection per-request
# ---------------------------------------------------------------------------

def get_db():
    """Dapatkan koneksi SQLAlchemy per-request via flask.g (Flask best practice)."""
    if 'db' not in g:
        g.db = get_engine().connect()
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Tutup koneksi DB otomatis saat request selesai (termasuk saat ada exception)."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Supabase client helper
# ---------------------------------------------------------------------------

def _get_supabase():
    """Lazy-load Supabase client, cached di flask.g per-request."""
    if 'supabase' not in g:
        g.supabase = get_server_supabase_client()
    return g.supabase


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def generate_unique_class_code(length: int = 6):
    conn = get_db()
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        row = conn.execute(
            text("SELECT 1 FROM classes WHERE kode_kelas = :code"), {"code": code}
        ).fetchone()
        if not row:
            break
    return code


def get_clean_ext(url: str) -> str:
    path = urlparse(url).path
    ext = os.path.splitext(path)[-1]
    if ext.lower() not in [".pdf", ".docx", ".txt"]:
        return ".pdf"
    return ext


# ---------------------------------------------------------------------------
# Auth placeholder (frontend uses this endpoint reference for url_for)
# ---------------------------------------------------------------------------

@app.route('/login_register')
def login_register():
    return jsonify({"error": "Unauthorized / Please login"}), 401


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login_register'))
    return render_template('admin-dashboard.html')


@app.route('/api/admin/summary')
def admin_summary():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db()
        total_users = conn.execute(text("SELECT COUNT(*) FROM auth.users")).scalar() or 0
        total_classes = conn.execute(text("SELECT COUNT(*) FROM classes")).scalar() or 0
        total_uploads = conn.execute(text("SELECT COUNT(*) FROM hasil_penilaian")).scalar() or 0
        active_admins = conn.execute(
            text("SELECT COUNT(*) FROM admins WHERE is_active = TRUE")
        ).scalar() or 0
    except Exception:
        logger.exception("Error fetching admin stats")
        return jsonify({"error": "Gagal mengambil statistik admin"}), 500

    return jsonify({
        "total_users": total_users,
        "total_classes": total_classes,
        "total_uploads": total_uploads,
        "active_admins": active_admins,
    })


@app.route('/api/admin/users')
def admin_get_users():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db()
        rows = conn.execute(text("""
            SELECT
                u.id,
                u.email,
                u.created_at,
                CASE WHEN a.id IS NOT NULL AND a.is_active THEN true ELSE false END as is_admin
            FROM auth.users u
            LEFT JOIN admins a ON u.id = a.user_id
            ORDER BY u.created_at DESC
        """)).fetchall()
    except Exception:
        logger.exception("Error fetching admin users")
        return jsonify({"error": "Gagal mengambil data user"}), 500

    result = [
        {
            "id": str(r[0]),
            "email": r[1],
            "created_at": r[2].strftime("%Y-%m-%d %H:%M"),
            "is_admin": r[3],
        }
        for r in rows
    ]
    return jsonify(result)


@app.route('/api/admin/landing', methods=['GET', 'POST'])
def api_admin_landing():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()

    if request.method == 'GET':
        try:
            rows = conn.execute(
                text("SELECT section_name, content FROM landing_page_content")
            ).fetchall()
        except Exception:
            logger.exception("Error fetching landing page content")
            return jsonify({"error": "Gagal mengambil konten landing page"}), 500

        result = {}
        for section_name, content in rows:
            try:
                result[section_name] = json.loads(content) if isinstance(content, str) else content
            except json.JSONDecodeError:
                result[section_name] = content

        result.setdefault('hero', {"title": "", "subtitle": "", "description": ""})
        result.setdefault('statistics', {"essays_graded": "1000+", "active_users": "500+", "satisfaction": "98%"})
        result.setdefault('testimonials', [])
        result.setdefault('contact', {"email": "", "phone": "", "address": ""})
        return jsonify(result)

    elif request.method == 'POST':
        data = request.get_json() or {}
        try:
            with get_engine().begin() as txn:
                for section in ['hero', 'statistics', 'testimonials', 'contact']:
                    if section in data:
                        content_to_store = json.dumps(data[section])
                        txn.execute(
                            text("""
                                INSERT INTO landing_page_content
                                    (section_name, content, updated_by, created_at, updated_at)
                                VALUES
                                    (:section, :content, :user_id, NOW(), NOW())
                                ON CONFLICT (section_name)
                                DO UPDATE SET
                                    content    = EXCLUDED.content,
                                    updated_by = EXCLUDED.updated_by,
                                    updated_at = NOW()
                            """),
                            {"section": section, "content": content_to_store, "user_id": session['user_id']},
                        )
        except Exception:
            logger.exception("Error saving landing page data")
            return jsonify({"error": "Gagal menyimpan konten landing page"}), 500

        return jsonify({"success": True})

    return jsonify({"error": "Method not allowed"}), 405


@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login_register'))
    return render_template('admin-users.html')


@app.route('/admin/landing-page')
def admin_landing():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login_register'))
    return render_template('admin-landing.html')


@app.route('/api/admin/promote', methods=['POST'])
def promote_user():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    if not target_user_id:
        return jsonify({"error": "No user_id provided"}), 400

    try:
        with get_engine().begin() as txn:
            existing = txn.execute(
                text("SELECT id FROM admins WHERE user_id = :uid"), {"uid": target_user_id}
            ).fetchone()
            if existing:
                txn.execute(
                    text("UPDATE admins SET is_active = TRUE WHERE user_id = :uid"),
                    {"uid": target_user_id},
                )
            else:
                txn.execute(
                    text("""
                        INSERT INTO admins (user_id, admin_level, is_active, created_by)
                        VALUES (:uid, :level, TRUE, :created_by)
                    """),
                    {"uid": target_user_id, "level": 2, "created_by": session['user_id']},
                )
    except Exception:
        logger.exception("Error promoting user")
        return jsonify({"error": "Gagal mempromosikan user"}), 500

    return jsonify({"success": True})


@app.route('/api/admin/deactivate', methods=['POST'])
def deactivate_user():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    if not target_user_id:
        return jsonify({"error": "No user_id provided"}), 400

    try:
        with get_engine().begin() as txn:
            txn.execute(
                text("UPDATE admins SET is_active = false WHERE user_id = :uid"),
                {"uid": target_user_id},
            )
    except Exception:
        logger.exception("Error deactivating user")
        return jsonify({"error": "Gagal menonaktifkan user"}), 500

    return jsonify({"success": True})


@app.route('/api/admin/classes')
def api_admin_classes():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db()
        rows = conn.execute(
            text("SELECT id, nama_kelas, kode_kelas, created_at FROM classes ORDER BY created_at DESC")
        ).fetchall()

    except Exception:
        logger.exception("Error fetching admin classes")
        return jsonify({"error": "Gagal mengambil daftar kelas"}), 500

    return jsonify([{
        "id": r[0],
        "nama_kelas": r[1],
        "kode_kelas": r[2],
        "created_at": r[3].strftime("%Y-%m-%d %H:%M"),
    } for r in rows])


@app.route('/api/admin/delete-user', methods=['POST'])
def admin_delete_user():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    if not target_user_id:
        return jsonify({"error": "No user_id provided"}), 400

    try:
        with get_engine().begin() as txn:
            txn.execute(
                text("DELETE FROM murid_kelas WHERE user_id = :uid"), {"uid": target_user_id}
            )
            txn.execute(
                text("DELETE FROM admins WHERE user_id = :uid"), {"uid": target_user_id}
            )
            txn.execute(
                text("DELETE FROM auth.users WHERE id = :uid"), {"uid": target_user_id}
            )
    except Exception:
        logger.exception("Error deleting user")
        return jsonify({"error": "Gagal menghapus user"}), 500

    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Class routes
# ---------------------------------------------------------------------------

@app.route('/create-class', methods=['POST'])
def create_class():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    nama_kelas = request.form.get('class_name')
    user_id = session['user_id']
    kode_kelas = generate_unique_class_code()
    created_at = datetime.datetime.now()

    try:
        with get_engine().begin() as txn:
            row = txn.execute(
                text(
                    "INSERT INTO classes (nama_kelas, kode_kelas, user_id, created_at) "
                    "VALUES (:nama, :kode, :uid, :created) RETURNING id"
                ),
                {"nama": nama_kelas, "kode": kode_kelas, "uid": user_id, "created": created_at},
            ).fetchone()
            kelas_id = row[0] if row else None
    except Exception:
        logger.exception("Error creating class")
        return jsonify({"error": "Gagal membuat kelas"}), 500

    return jsonify({"class_code": kode_kelas, "kelas_id": kelas_id})


@app.route('/api/classes', methods=['GET'])
def api_classes():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db()
        rows = conn.execute(
            text(
                "SELECT id, nama_kelas, kode_kelas, created_at FROM classes "
                "WHERE user_id = :uid ORDER BY created_at DESC"
            ),
            {"uid": session['user_id']},
        ).fetchall()
    except Exception:
        logger.exception("Error getting classes")
        return jsonify({"error": "Terjadi kesalahan saat mengambil daftar kelas"}), 500

    return jsonify([{
        "id": row[0],
        "nama_kelas": row[1],
        "kode_kelas": row[2],
        "created_at": row[3].strftime("%Y-%m-%d %H:%M"),
    } for row in rows])


@app.route('/api/class/update', methods=['POST'])
def api_update_class():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    role = session.get('role')
    data = request.get_json() or {}
    kode_kelas = data.get('kode_kelas')
    nama_kelas = data.get('nama_kelas')

    if not kode_kelas or not nama_kelas:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        with get_engine().begin() as txn:
            if role == 'Admin':
                txn.execute(
                    text("UPDATE classes SET nama_kelas = :nama WHERE kode_kelas = :kode"),
                    {"nama": nama_kelas, "kode": kode_kelas},
                )
            else:
                txn.execute(
                    text(
                        "UPDATE classes SET nama_kelas = :nama "
                        "WHERE kode_kelas = :kode AND user_id = :uid"
                    ),
                    {"nama": nama_kelas, "kode": kode_kelas, "uid": session['user_id']},
                )
    except Exception:
        logger.exception("Error updating class")
        return jsonify({'error': 'Gagal memperbarui kelas'}), 500

    return jsonify({'success': True})


@app.route('/admin/classes')
def admin_classes():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login_register'))
    return render_template('admin-classes.html')


@app.route('/api/class/delete', methods=['POST'])
def api_delete_class():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    kode_kelas = data.get('kode_kelas')
    if not kode_kelas:
        return jsonify({'error': 'Invalid data'}), 400

    conn = get_db()
    try:
        kelas_row = conn.execute(
            text("SELECT id FROM classes WHERE kode_kelas = :kode AND user_id = :uid"),
            {"kode": kode_kelas, "uid": session['user_id']},
        ).fetchone()

        if not kelas_row:
            return jsonify({'error': 'Class not found'}), 404

        kelas_id = kelas_row[0]

        with get_engine().begin() as txn:
            txn.execute(
                text("DELETE FROM hasil_penilaian WHERE kelas_id = :kid"), {"kid": kelas_id}
            )
            txn.execute(
                text("DELETE FROM assignments WHERE kelas_id = :kid"), {"kid": kelas_id}
            )
            txn.execute(
                text("DELETE FROM classes WHERE id = :kid"), {"kid": kelas_id}
            )
    except Exception:
        logger.exception("Error deleting class")
        return jsonify({'error': 'Gagal menghapus kelas'}), 500

    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Results routes
# ---------------------------------------------------------------------------

@app.route('/api/results', methods=['GET'])
def api_results():
    if 'user_id' not in session:
        return jsonify([]), 401
    
    results = fetch_all_results(session['user_id'])
    return jsonify(results)


@app.route('/api/results/kelas/<int:kelas_id>', methods=['GET'])
def api_results_by_kelas(kelas_id):
    if 'user_id' not in session:
        return jsonify([]), 401
    
    results = fetch_results_by_kelas(kelas_id)
    return jsonify(results)


@app.route('/api/results/kelas-kode/<kode_kelas>', methods=['GET'])
def api_results_by_kode_kelas(kode_kelas):
    if 'user_id' not in session:
        return jsonify([]), 401
    
    results = fetch_results_by_kode_kelas(kode_kelas, session['user_id'])
    return jsonify(results)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route('/set_session', methods=['POST'])
def set_session():
    data = request.get_json() or {}
    access_token = data.get('access_token')
    if not access_token:
        return jsonify({"error": "No token"}), 400

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_secret_key = os.getenv("SUPABASE_SECRET_KEY")
    if not supabase_url or not supabase_secret_key:
        return jsonify({"error": "Server configuration error"}), 500

    headers = {
        "apikey": supabase_secret_key,
        "Authorization": f"Bearer {access_token}",
    }
    resp = requests.get(f"{supabase_url}/auth/v1/user", headers=headers, timeout=10)
    if resp.status_code != 200:
        return jsonify({"error": "Invalid token"}), 401

    user = resp.json() if hasattr(resp, 'json') else {}

    session['user_id'] = user.get('id')
    user_metadata = user.get('user_metadata') or {}
    session['username'] = user_metadata.get('username') or user.get('email') or 'user'
    session['role'] = user_metadata.get('role') or 'Student'

    # Cek apakah user adalah admin
    try:
        conn = get_db()
        admin_row = conn.execute(
            text("SELECT admin_level FROM admins WHERE user_id = :uid AND is_active = true"),
            {"uid": session.get('user_id')},
        ).fetchone()
        if admin_row:
            session['role'] = 'Admin'
            session['admin_level'] = admin_row[0] if len(admin_row) > 0 else None
    except Exception:
        logger.exception("Error checking admin role")

    logger.info("LOGIN ROLE: %s", session['role'])
    return jsonify({"success": True})


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Upload delete
# ---------------------------------------------------------------------------

@app.route('/api/upload/delete', methods=['POST'])
def api_delete_upload():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    upload_id = data.get('id')
    if not upload_id:
        return jsonify({'error': 'Invalid data'}), 400

    conn = get_db()
    try:
        existing = conn.execute(
            text("SELECT id FROM hasil_penilaian WHERE id = :id"), {"id": upload_id}
        ).fetchone()
        if not existing:
            return jsonify({'error': 'Not found'}), 404

        with get_engine().begin() as txn:
            txn.execute(
                text("DELETE FROM hasil_penilaian WHERE id = :id"), {"id": upload_id}
            )
    except Exception:
        logger.exception("Error deleting upload")
        return jsonify({'error': 'Gagal menghapus upload'}), 500

    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Join class routes
# ---------------------------------------------------------------------------

@app.route('/api/join-class', methods=['POST'])
def join_class():
    if 'user_id' not in session or session.get('role') != 'Student':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    kode_kelas = data.get('kode_kelas')
    if not kode_kelas:
        return jsonify({'error': 'Kode kelas harus diisi'}), 400

    conn = get_db()
    try:
        kelas = conn.execute(
            text("SELECT id, nama_kelas FROM classes WHERE kode_kelas = :kode"),
            {"kode": kode_kelas},
        ).fetchone()
        if not kelas:
            return jsonify({'error': 'Kode kelas tidak ditemukan'}), 404

        kelas_id, nama_kelas = kelas

        already_joined = conn.execute(
            text("SELECT 1 FROM murid_kelas WHERE user_id = :uid AND kelas_id = :kid"),
            {"uid": session['user_id'], "kid": kelas_id},
        ).fetchone()
        if already_joined:
            return jsonify({'error': 'Kamu sudah join kelas ini'}), 400

        with get_engine().begin() as txn:
            txn.execute(
                text("INSERT INTO murid_kelas (user_id, kelas_id) VALUES (:uid, :kid)"),
                {"uid": session['user_id'], "kid": kelas_id},
            )
    except Exception:
        logger.exception("Error joining class")
        return jsonify({'error': 'Gagal bergabung ke kelas'}), 500

    return jsonify({'success': True, 'nama_kelas': nama_kelas, 'kode_kelas': kode_kelas})


@app.route('/api/joined-classes', methods=['GET'])
def api_joined_classes():
    if 'user_id' not in session or session.get('role') != 'Student':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    try:
        rows = conn.execute(
            text("""
                SELECT c.nama_kelas, c.kode_kelas
                FROM murid_kelas mk
                JOIN classes c ON mk.kelas_id = c.id
                WHERE mk.user_id = :uid
                ORDER BY mk.joined_at DESC
            """),
            {"uid": session['user_id']},
        ).fetchall()
    except Exception:
        logger.exception("Error fetching joined classes")
        return jsonify({'error': 'Gagal mengambil daftar kelas'}), 500

    return jsonify([{"nama_kelas": row[0], "kode_kelas": row[1]} for row in rows])


# ---------------------------------------------------------------------------
# Assignment routes
# ---------------------------------------------------------------------------

@app.route('/api/assignments', methods=['POST'])
def api_add_assignment():
    if 'user_id' not in session or session.get('role') != 'Teacher':
        return jsonify({"error": "Unauthorized"}), 401

    try:
        judul = request.form.get('judulAssignment')
        deskripsi = request.form.get('deskripsiAssignment')
        deadline = request.form.get('deadlineAssignment')
        kelas_id = request.form.get('kelas_id')
        file_assignment = request.files.get('fileAssignment')
        file_jawaban = request.files.get('jawabanGuru')

        if file_assignment is None or not getattr(file_assignment, 'filename', None):
            return jsonify({"error": "No assignment file provided"}), 400
        if file_jawaban is None or not getattr(file_jawaban, 'filename', None):
            return jsonify({"error": "No teacher answer file provided"}), 400

        assignment_ext = os.path.splitext(file_assignment.filename or "")[-1]
        jawaban_ext = os.path.splitext(file_jawaban.filename or "")[-1]
        assignment_filename = f"assignments/{kelas_id}_{judul}_assignment{assignment_ext}".replace(" ", "_")
        jawaban_filename = f"answers/teacher/{kelas_id}_{judul}_jawaban{jawaban_ext}".replace(" ", "_")

        assignment_url = upload_file(file_assignment.read(), assignment_filename)
        jawaban_url = upload_file(file_jawaban.read(), jawaban_filename)

        with get_engine().begin() as txn:
            row = txn.execute(
                text("""
                    INSERT INTO assignments
                        (judul, deskripsi, deadline, file_path, jawaban_path, kelas_id, created_at)
                    VALUES
                        (:judul, :deskripsi, :deadline, :file_path, :jawaban_path, :kelas_id, :created_at)
                    RETURNING id
                """),
                {
                    "judul": judul,
                    "deskripsi": deskripsi,
                    "deadline": deadline,
                    "file_path": assignment_url,
                    "jawaban_path": jawaban_url,
                    "kelas_id": kelas_id,
                    "created_at": datetime.datetime.now(),
                },
            ).fetchone()
            assignment_id_from_db = row[0] if row else None

    except SupabaseStorageError:
        logger.exception("Error uploading assignment files")
        return jsonify({"error": "Gagal mengupload file ke storage"}), 500
    except Exception:
        logger.exception("Error adding assignment")
        return jsonify({"error": "Terjadi kesalahan saat menambahkan assignment"}), 500

    return jsonify({
        "success": True,
        "message": "Assignment berhasil ditambahkan",
        "assignment_id": assignment_id_from_db,
    })


@app.route('/api/assignments/<kode_kelas>', methods=['GET'])
def api_get_assignments_by_kode_kelas(kode_kelas):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    try:
        kelas_info = conn.execute(
            text("SELECT id FROM classes WHERE kode_kelas = :kode"), {"kode": kode_kelas}
        ).fetchone()
        if not kelas_info:
            return jsonify({"error": "Class not found"}), 404

        kelas_id = kelas_info[0]
        user_id = session['user_id']

        assignments = conn.execute(
            text("""
                SELECT
                    a.id,
                    a.judul,
                    a.deskripsi,
                    a.deadline,
                    a.file_path,
                    a.jawaban_path,
                    a.created_at,
                    EXISTS(
                        SELECT 1 FROM hasil_penilaian hp
                        WHERE hp.assignment_id = a.id AND hp.user_id = :uid AND hp.is_active = TRUE
                    ) as is_submitted,
                    a.is_published,
                    (SELECT COALESCE(MAX(version), 0) FROM hasil_penilaian hp
                     WHERE hp.assignment_id = a.id AND hp.user_id = :uid
                    ) as max_version
                FROM assignments a
                WHERE a.kelas_id = :kid
                ORDER BY a.created_at DESC
            """),
            {"uid": user_id, "kid": kelas_id},
        ).fetchall()
    except Exception:
        logger.exception("Error fetching assignments")
        return jsonify({"error": "Terjadi kesalahan saat mengambil data assignment"}), 500

    return jsonify([{
        "id": a[0],
        "judul": a[1],
        "deskripsi": a[2],
        "deadline": a[3].strftime("%Y-%m-%d %H:%M") if a[3] else None,
        "file_path": a[4],
        "jawaban_path": a[5],
        "created_at": a[6].strftime("%Y-%m-%d %H:%M"),
        "is_submitted": a[7],
        "is_published": a[8],
        "max_version": a[9]
    } for a in assignments])


@app.route('/api/submissions/undo/<int:assignment_id>', methods=['POST'])
def api_undo_submission(assignment_id):
    if 'user_id' not in session or session.get('role') != 'Student':
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    conn = get_db()
    
    try:
        # 1. Cek apakah assignment masih dalam periode submission (belum lewat deadline)
        assignment = conn.execute(
            text("SELECT deadline FROM assignments WHERE id = :id"),
            {"id": assignment_id}
        ).fetchone()
        
        if not assignment:
            return jsonify({"error": "Assignment tidak ditemukan"}), 404
        
        deadline = assignment[0]
        if deadline:
            # Pastikan deadline timezone-aware jika perlu (asumsi naive adalah UTC)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=datetime.timezone.utc)
            
            if datetime.datetime.now(datetime.timezone.utc) > deadline:
                return jsonify({"error": "Batas waktu pengumpulan telah lewat. Tidak bisa membatalkan pengumpulan."}), 400

        # 2. Cek apakah ada submission yang aktif
        submission = conn.execute(
            text("SELECT id FROM hasil_penilaian WHERE user_id = :uid AND assignment_id = :aid AND is_active = TRUE"),
            {"uid": user_id, "aid": assignment_id}
        ).fetchone()
        
        if not submission:
            return jsonify({"error": "Tidak ada submission aktif yang ditemukan"}), 404

        # 3. Mark as inactive
        with get_engine().begin() as txn:
            txn.execute(
                text("UPDATE hasil_penilaian SET is_active = FALSE WHERE id = :sid"),
                {"sid": submission[0]}
            )

        return jsonify({"success": True, "message": "Berhasil membatalkan pengumpulan. Silakan unggah ulang jika perlu."})
        
    except Exception:
        logger.exception("Error undoing submission")
        return jsonify({"error": "Terjadi kesalahan saat membatalkan pengumpulan"}), 500


@app.route('/api/assignments/publish/<int:assignment_id>', methods=['POST'])
def api_toggle_publish_assignment(assignment_id):
    if 'user_id' not in session or session.get('role') != 'Teacher':
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    try:
        data = request.get_json()
        is_published = data.get('is_published', False)

        with get_engine().begin() as txn:
            txn.execute(
                text("UPDATE assignments SET is_published = :pub WHERE id = :id"),
                {"pub": is_published, "id": assignment_id}
            )

        status = "dipublikasikan" if is_published else "disembunyikan"
        return jsonify({"success": True, "message": f"Hasil pengumpulan berhasil {status}."})
        
    except Exception:
        logger.exception("Error toggling publish status")
        return jsonify({"error": "Terjadi kesalahan saat mengubah status publikasi"}), 500


@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
def api_delete_assignment(assignment_id):
    if 'user_id' not in session or session.get('role') != 'Teacher':
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    try:
        result = conn.execute(
            text("SELECT file_path, jawaban_path FROM assignments WHERE id = :id"),
            {"id": assignment_id},
        ).fetchone()
        if not result:
            return jsonify({"error": "Assignment tidak ditemukan"}), 404

        file_url, jawaban_url = result

        with get_engine().begin() as txn:
            txn.execute(
                text("DELETE FROM assignments WHERE id = :id"), {"id": assignment_id}
            )

        # Hapus file dari Supabase Storage
        supabase_client = _get_supabase()
        for url in [file_url, jawaban_url]:
            if url:
                storage_path = get_public_path(url)
                if storage_path:
                    try:
                        supabase_client.storage.from_('uploads').remove([storage_path])
                    except Exception:
                        logger.warning("Gagal hapus file dari storage: %s", storage_path)

    except Exception:
        logger.exception("Error deleting assignment")
        return jsonify({"error": "Terjadi kesalahan saat menghapus assignment"}), 500

    return jsonify({"success": True, "message": "Assignment berhasil dihapus"})


@app.route('/api/results/assignment/<int:assignment_id>', methods=['GET'])
def api_results_by_assignment(assignment_id):
    if 'user_id' not in session or session.get('role') not in ['Teacher', 'Admin']:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        results = fetch_results_by_assignment_id(assignment_id)
        return jsonify(results)
    except Exception:
        logger.exception("Error fetching results by assignment ID")
        return jsonify({"error": "Terjadi kesalahan saat mengambil hasil upload"}), 500


@app.route('/api/assignments/upload/<int:assignment_id>', methods=['POST'])
def api_upload_student_answer(assignment_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file yang diunggah."}), 400

    student_file = request.files['file']
    if student_file.filename == '':
        return jsonify({"error": "File tidak dipilih."}), 400

    conn = get_db()
    try:
        assignment_info = conn.execute(
            text("SELECT kelas_id, jawaban_path, judul, deadline FROM assignments WHERE id = :id"),
            {"id": assignment_id},
        ).fetchone()
        if not assignment_info:
            return jsonify({"error": "Assignment tidak ditemukan."}), 404

        kelas_id, guru_jawaban_url, judul_assignment, deadline = assignment_info

        # Cek deadline
        if deadline:
            if deadline.tzinfo is not None:
                deadline = deadline.replace(tzinfo=None)
            
            if datetime.datetime.now() > deadline:
                return jsonify({"error": "Batas waktu pengumpulan (deadline) telah lewat."}), 400

        kelas_row = conn.execute(
            text("SELECT nama_kelas FROM classes WHERE id = :kid"), {"kid": kelas_id}
        ).fetchone()
        nama_kelas = kelas_row[0] if kelas_row and kelas_row[0] else "kelas"
    except Exception:
        logger.exception("Error fetching assignment info")
        return jsonify({"error": "Gagal mengambil info assignment"}), 500

    nama_user = session.get('username', 'user')
    ext = os.path.splitext(student_file.filename or "")[-1]
    import time
    timestamp = int(time.time())
    student_filename = f"answers/student/{kelas_id}_{assignment_id}_{nama_user}_jawaban_{timestamp}{ext}".replace(" ", "_")

    # Upload file murid ke Supabase Storage
    try:
        murid_url = upload_file(student_file.read(), student_filename)
    except SupabaseStorageError:
        logger.exception("Error uploading student file")
        return jsonify({"error": "Gagal mengupload file jawaban"}), 500

    if not murid_url:
        return jsonify({"error": "murid url tidak tersedia"}), 500

    murid_ext = get_clean_ext(murid_url)

    # Defer AI: Only extract text for now, skip scoring and feedback.
    with tempfile.NamedTemporaryFile(delete=False, suffix=murid_ext) as tmp_murid:
        try:
            murid_bytes = download_file(murid_url, client=_get_supabase())
        except SupabaseDownloadError:
            logger.exception("Failed to download murid file")
            return jsonify({"error": "Gagal mendownload file murid dari storage"}), 500
        tmp_murid.write(murid_bytes)
        tmp_murid.flush()

        murid_text = extract_text_from_any(tmp_murid.name)
        if not murid_text:
            return jsonify({"error": "Format tidak didukung atau file kosong"}), 400

    result_to_save = {
        "name": nama_user,
        "similarity": 0,
        "grade": 0,
        "user_id": session['user_id'],
        "kelas_id": kelas_id,
        "assignment_id": assignment_id,
        "file_path": murid_url,
        "status": "pending",
        "feedback": "Menunggu penilaian guru.",
        "sub_criteria_scores": [],
        "highlights": [],
        "essay_text": murid_text
    }

    try:
        with get_engine().begin() as txn:
            max_version_row = txn.execute(
                text("SELECT COALESCE(MAX(version), 0) FROM hasil_penilaian WHERE user_id = :uid AND assignment_id = :aid"),
                {"uid": session['user_id'], "aid": assignment_id}
            ).fetchone()
            max_version = max_version_row[0] if max_version_row else 0
            
            txn.execute(
                text("UPDATE hasil_penilaian SET is_active = FALSE WHERE user_id = :uid AND assignment_id = :aid"),
                {"uid": session['user_id'], "aid": assignment_id}
            )
            
            result_to_save["version"] = max_version + 1
            result_to_save["is_active"] = True
            
            simpan_ke_postgres([result_to_save], conn=txn)
    except Exception:
        logger.exception("Error saving student submission")
        return jsonify({"error": "Gagal menyimpan hasil unggahan siswa."}), 500

    # Hapus file temp
    try:
        os.remove(tmp_murid.name)
    except Exception:
        logger.warning("Gagal hapus file temp: %s", tmp_murid.name)

    return jsonify({
        "success": True,
        "message": "Unggahan berhasil! Menunggu penilaian guru.",
        "status": "pending"
    })


def _perform_ai_grading(submission, assignment):
    # submission: (id, assignment_id, nama_murid, file_path, status, essay_text, user_id, kelas_id)
    # assignment: (kelas_id, jawaban_path, judul, deadline)
    sub_id, aid, nama_murid, murid_url, status, murid_text, student_user_id, kelas_id = submission
    akid, guru_jawaban_url, judul_assignment, _ = assignment
    
    try:
        guru_ext = get_clean_ext(guru_jawaban_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=guru_ext) as tmp_guru:
            try:
                guru_bytes = download_file(guru_jawaban_url, client=_get_supabase())
            except SupabaseDownloadError:
                logger.exception("Failed to download guru file")
                return False, "Gagal mendownload file kunci jawaban dari storage"
            
            tmp_guru.write(guru_bytes)
            tmp_guru.flush()
            guru_text = extract_text_from_any(tmp_guru.name)

        if not guru_text:
            return False, "Gagal mengekstrak teks kunci jawaban guru."

        scoring_engine = os.getenv("SCORING_ENGINE", "legacy").lower()
        sub_criteria_scores = None

        if scoring_engine == "embeddings":
            try:
                score_res = embedding_score_submission(guru_text, murid_text)
                avg_similarity = score_res["avg_similarity"]
                grade = score_res["grade"]
                sub_criteria_scores = score_res.get("per_question")
            except Exception:
                logger.exception("Embedding scoring failed")
                return False, "Gagal memproses penilaian dengan AI."
        else:
            try:
                avg_similarity, grade, per_question = lsa_similarity(guru_text, murid_text)
                sub_criteria_scores = per_question
            except Exception:
                logger.exception("LSA scoring failed")
                return False, "Gagal memproses penilaian dengan LSA."

        # Generate Pedagogical Feedback
        try:
            feedback_data = generate_pedagogical_feedback(guru_text, murid_text, grade)
            feedback = feedback_data.get("feedback", "Gagal menghasilkan feedback otomatis.")
            raw_highlights = feedback_data.get("highlights", [])
            highlights = extract_highlights(murid_text, raw_highlights)
        except Exception:
            logger.exception("Feedback generation failed")
            feedback = "Gagal menghasilkan feedback otomatis."
            highlights = []

        result_to_save = {
            "name": nama_murid,
            "similarity": avg_similarity,
            "grade": grade,
            "user_id": student_user_id,
            "kelas_id": kelas_id,
            "assignment_id": aid,
            "file_path": murid_url,
            "status": "draft",
            "feedback": feedback,
            "sub_criteria_scores": sub_criteria_scores,
            "highlights": highlights,
            "essay_text": murid_text
        }

        with get_engine().begin() as txn:
            max_version_row = txn.execute(
                text("SELECT COALESCE(MAX(version), 0) FROM hasil_penilaian WHERE user_id = :uid AND assignment_id = :aid"),
                {"uid": student_user_id, "aid": aid}
            ).fetchone()
            max_version = max_version_row[0] if max_version_row else 0
            
            txn.execute(
                text("UPDATE hasil_penilaian SET is_active = FALSE WHERE user_id = :uid AND assignment_id = :aid"),
                {"uid": student_user_id, "aid": aid}
            )
            
            result_to_save["version"] = max_version + 1
            result_to_save["is_active"] = True
            
            simpan_ke_postgres([result_to_save], conn=txn)

        # Cleanup
        try:
            os.remove(tmp_guru.name)
        except Exception:
            pass
            
        return True, result_to_save
    except Exception:
        logger.exception("Internal error during _perform_ai_grading")
        return False, "Terjadi kesalahan saat memproses penilaian AI."

@app.route('/api/submissions/grade/<submission_id>', methods=['POST'])
def api_grade_individual_submission(submission_id):
    if 'user_id' not in session or session.get('role') not in ['Teacher', 'Admin']:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    try:
        submission = conn.execute(
            text("SELECT id, assignment_id, nama_murid, file_path, status, essay_text, user_id, kelas_id FROM hasil_penilaian WHERE id = :id"),
            {"id": submission_id}
        ).fetchone()
        
        if not submission:
            return jsonify({"error": "Submission tidak ditemukan"}), 404
        
        assignment_id = submission[1]
        assignment = conn.execute(
            text("SELECT kelas_id, jawaban_path, judul, deadline FROM assignments WHERE id = :id"),
            {"id": assignment_id}
        ).fetchone()
        
        # Check deadline
        deadline = assignment[3]
        if deadline:
            if deadline.tzinfo is not None:
                deadline = deadline.replace(tzinfo=None)
            if datetime.datetime.now() < deadline:
                return jsonify({"error": "Penilaian hanya dapat dilakukan setelah deadline lewat."}), 400

        success, result = _perform_ai_grading(submission, assignment)
        if not success:
            return jsonify({"error": result}), 500
            
        return jsonify({"success": True, "message": "Berhasil melakukan penilaian AI."})
        
    except Exception:
        logger.exception("Error in individual grading")
        return jsonify({"error": "Terjadi kesalahan internal"}), 500

@app.route('/api/assignments/grade-bulk/<int:assignment_id>', methods=['POST'])
def api_grade_bulk_submissions(assignment_id):
    if 'user_id' not in session or session.get('role') not in ['Teacher', 'Admin']:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    try:
        assignment = conn.execute(
            text("SELECT kelas_id, jawaban_path, judul, deadline FROM assignments WHERE id = :id"),
            {"id": assignment_id}
        ).fetchone()
        
        if not assignment:
            return jsonify({"error": "Assignment tidak ditemukan"}), 404

        # Check deadline
        deadline = assignment[3]
        if deadline:
            if deadline.tzinfo is not None:
                deadline = deadline.replace(tzinfo=None)
            if datetime.datetime.now() < deadline:
                return jsonify({"error": "Penilaian hanya dapat dilakukan setelah deadline lewat."}), 400

        pending_submissions = conn.execute(
            text("SELECT id, assignment_id, nama_murid, file_path, status, essay_text, user_id, kelas_id FROM hasil_penilaian WHERE assignment_id = :aid AND status = 'pending' AND is_active = TRUE"),
            {"aid": assignment_id}
        ).fetchall()
        
        processed_count = 0
        for sub in pending_submissions:
            success, _ = _perform_ai_grading(sub, assignment)
            if success:
                processed_count += 1
                
        return jsonify({"success": True, "processed_count": processed_count})
        
    except Exception:
        logger.exception("Error in bulk grading")
        return jsonify({"error": "Terjadi kesalahan internal"}), 500


# ---------------------------------------------------------------------------
# CSV download
# ---------------------------------------------------------------------------

@app.route('/api/assignments/<int:assignment_id>/download-csv', methods=['GET'])
def download_assignment_csv(assignment_id):
    if 'user_id' not in session or session.get('role') != 'Teacher':
        return jsonify({"error": "Unauthorized"}), 401

    results = fetch_results_by_assignment_id(assignment_id)
    if not results:
        return jsonify({"error": "No results found"}), 404

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Grade', 'Similarity', 'Upload Time'])
    for row in results:
        writer.writerow([
            row.get('nama_murid', '-'),
            row.get('nilai', row.get('grade', '-')),
            row.get('similarity', '-'),
            row.get('created_at', '-'),
        ])

    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)

    filename = f"assignment_{assignment_id}_results.csv"
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)


@app.route('/api/results/override', methods=['POST'])
def api_override_result():
    if 'user_id' not in session or session.get('role') not in ['Teacher', 'Admin']:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    result_id = data.get('id')
    new_grade = data.get('grade')
    new_feedback = data.get('feedback')
    new_sub_scores = data.get('sub_criteria_scores')
    new_status = data.get('status', 'published')

    if not result_id:
        return jsonify({"error": "Missing result ID"}), 400

    try:
        with get_engine().begin() as txn:
            txn.execute(
                text("""
                    UPDATE hasil_penilaian
                    SET nilai = :grade,
                        feedback = :feedback,
                        sub_criteria_scores = :sub_scores,
                        status = :status,
                        updated_at = NOW()
                    WHERE id = :id
                """),
                {
                    "grade": new_grade,
                    "feedback": new_feedback,
                    "sub_scores": json.dumps(new_sub_scores) if new_sub_scores else None,
                    "status": new_status,
                    "id": result_id
                }
            )
    except Exception:
        logger.exception("Error overriding result")
        return jsonify({"error": "Gagal menyimpan perubahan"}), 500

    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
