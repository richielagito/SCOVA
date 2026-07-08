import logging
import os
import traceback
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Shared column list for hasil_penilaian SELECT queries.
# Centralised here so that schema changes (e.g. adding/renaming a column or
# changing a cast) only need to be made in one place.
_HP_COLUMNS = (
    "id, nama_murid, similarity, nilai, user_id, kelas_id, assignment_id, "
    "file_path, status, feedback, "
    "sub_criteria_scores::json AS sub_criteria_scores, "
    "highlights::json AS highlights, "
    "essay_text, version, is_active, created_at"
)

# Same list with the 'hp.' table alias prefix, used in JOIN queries.
_HP_COLUMNS_PREFIXED = (
    "hp.id, hp.nama_murid, hp.similarity, hp.nilai, hp.user_id, hp.kelas_id, hp.assignment_id, "
    "hp.file_path, hp.status, hp.feedback, "
    "hp.sub_criteria_scores::json AS sub_criteria_scores, "
    "hp.highlights::json AS highlights, "
    "hp.essay_text, hp.version, hp.is_active, hp.created_at"
)

_USER = os.getenv("DB_USER")
_PASSWORD = os.getenv("DB_PASSWORD")
_HOST = os.getenv("DB_HOST")
_PORT = os.getenv("DB_PORT")
_DBNAME = os.getenv("DB_NAME")

_DATABASE_URL = (
    f"postgresql+psycopg2://{_USER}:{_PASSWORD}@{_HOST}:{_PORT}/{_DBNAME}?sslmode=require"
)

# Singleton engine — dibuat sekali saat startup, bukan setiap pemanggilan
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        if not all([_USER, _PASSWORD, _HOST, _PORT, _DBNAME]):
            raise ValueError(
                "Missing DB configuration. Pastikan DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME ada di .env"
            )
        _engine = create_engine(
            _DATABASE_URL,
            pool_size=5,
            max_overflow=2,
            pool_pre_ping=True,  # Cek koneksi sebelum dipakai (menghindari stale connections)
        )
        logger.info("SQLAlchemy engine created (singleton)")
    return _engine


def simpan_ke_postgres(results, conn=None):
    """Simpan hasil penilaian. Menggunakan INSERT biasa (tanpa ON CONFLICT) untuk mendukung versi."""
    if not results:
        return

    params = [
        {
            "name": r["name"],
            "similarity": float(r["similarity"]),
            "grade": r["grade"],
            "user_id": r["user_id"],
            "kelas_id": r["kelas_id"],
            "assignment_id": r.get("assignment_id"),
            "file_path": r["file_path"],
            "status": r.get("status", "draft"),
            "feedback": r.get("feedback"),
            "sub_criteria_scores": json.dumps(r.get("sub_criteria_scores"))
            if r.get("sub_criteria_scores")
            else None,
            "highlights": json.dumps(r.get("highlights")) if r.get("highlights") else None,
            "essay_text": r.get("essay_text"),
            "version": r.get("version", 1),
            "is_active": r.get("is_active", True),
        }
        for r in results
    ]

    query = text("""
        INSERT INTO hasil_penilaian
            (nama_murid, similarity, nilai, user_id, kelas_id, assignment_id, file_path, status, feedback, sub_criteria_scores, highlights, essay_text, version, is_active)
        VALUES
            (:name, :similarity, :grade, :user_id, :kelas_id, :assignment_id, :file_path, :status, :feedback, :sub_criteria_scores, :highlights, :essay_text, :version, :is_active)
    """)

    try:
        if conn is not None:
            conn.execute(query, params)
        else:
            with get_engine().begin() as c:
                c.execute(query, params)
    except Exception:
        logger.exception("Gagal menyimpan ke PostgreSQL")
        traceback.print_exc()
        raise


def fetch_all_results(user_id, status=None):
    try:
        with get_engine().connect() as conn:
            query = f"SELECT {_HP_COLUMNS} FROM public.hasil_penilaian WHERE user_id = :user_id AND is_active = TRUE"
            params = {"user_id": user_id}
            if status:
                query += " AND status = :status"
                params["status"] = status
            query += " ORDER BY nama_murid"
            result = conn.execute(text(query), params)
            results = [dict(row) for row in result.mappings()]
            for r in results:
                r["similarity"] = float(r["similarity"])
            return results
    except Exception:
        logger.exception("Gagal fetch data dari PostgreSQL")
        return []


def fetch_results_by_kelas(kelas_id, status=None):
    try:
        with get_engine().connect() as conn:
            query = f"SELECT {_HP_COLUMNS} FROM public.hasil_penilaian WHERE kelas_id = :kelas_id AND is_active = TRUE"
            params = {"kelas_id": kelas_id}
            if status:
                query += " AND status = :status"
                params["status"] = status
            query += " ORDER BY nama_murid"
            result = conn.execute(text(query), params)
            results = [dict(row) for row in result.mappings()]
            for r in results:
                r["similarity"] = float(r["similarity"])
            return results
    except Exception:
        logger.exception("Gagal fetch data dari PostgreSQL (by kelas)")
        return []


def fetch_results_by_kode_kelas(kode_kelas, user_id, status=None):
    try:
        with get_engine().connect() as conn:
            kelas_result = conn.execute(
                text(
                    "SELECT c.id FROM classes c "
                    "JOIN murid_kelas mk ON c.id = mk.kelas_id "
                    "WHERE c.kode_kelas = :kode_kelas AND mk.user_id = :user_id"
                ),
                {"kode_kelas": kode_kelas, "user_id": user_id},
            )
            kelas_row = kelas_result.fetchone()
            if not kelas_row:
                return []
            kelas_id = kelas_row[0]

            query = f"""
                SELECT {_HP_COLUMNS_PREFIXED}, a.judul AS judul_assignment
                FROM public.hasil_penilaian hp
                JOIN assignments a ON hp.assignment_id = a.id
                WHERE hp.kelas_id = :kelas_id AND hp.user_id = :user_id AND hp.is_active = TRUE
            """
            params = {"kelas_id": kelas_id, "user_id": user_id}
            if status:
                query += " AND hp.status = :status"
                params["status"] = status
            query += " ORDER BY hp.nama_murid"

            result = conn.execute(text(query), params)
            results = [dict(row) for row in result.mappings()]
            for r in results:
                r["similarity"] = float(r["similarity"])
            return results
    except Exception:
        logger.exception("Gagal fetch data dari PostgreSQL (by kode_kelas)")
        return []


def fetch_results_by_assignment_id(assignment_id, status=None):
    try:
        with get_engine().connect() as conn:
            query = """
                SELECT id, nama_murid, similarity, nilai, status, feedback, sub_criteria_scores::json AS sub_criteria_scores, highlights::json AS highlights, essay_text, created_at, version
                FROM public.hasil_penilaian
                WHERE assignment_id = :assignment_id AND is_active = TRUE
            """
            params = {"assignment_id": assignment_id}
            if status:
                query += " AND status = :status"
                params["status"] = status
            query += " ORDER BY created_at DESC"

            result = conn.execute(text(query), params)
            results = [dict(row) for row in result.mappings()]
            for r in results:
                r["similarity"] = float(r["similarity"])
            return results
    except Exception:
        logger.exception("Gagal fetch data dari PostgreSQL (by assignment_id)")
        return []
