"""Per-question embedding-based scorer.

Uses extract_answers from LSA to parse teacher and student answers, calls
embedding_client.get_embeddings in batches for model and student texts,
computes cosine similarity per question, rounds per-question similarity to
3 decimals, and returns avg_similarity and grade (0-100) along with per-question
breakdown.

Behavior notes:
- Missing student answers are treated as empty string and assigned 0.0 similarity
- If no questions parsed from reference_text, returns avg_similarity 0.0 and grade 0
"""
from typing import List, Dict, Any
import math

from .LSA import extract_answers
from . import embedding_client


def _cosine(a: List[float], b: List[float]) -> float:
    # assumes vectors are same length; embedding_client may normalize already
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def embedding_score_submission(reference_text: str, student_text: str) -> Dict[str, Any]:
    """Score a student submission against reference per-question using embeddings.

    Returns dict with keys:
      - avg_similarity: float between 0 and 1 (mean of per-question similarities)
      - grade: int 0..100 (round(avg_similarity * 100))
      - per_question: list of {question: int, similarity: float, grade: int}

    Deterministic fallback: if no questions parsed, returns avg_similarity 0.0,
    grade 0 and empty per_question list.
    """
    model_answers = extract_answers(reference_text or "") or {}
    student_answers = extract_answers(student_text or "") or {}

    if not model_answers:
        return {"avg_similarity": 0.0, "grade": 0, "per_question": []}

    # Ensure numeric ordering by question number (keys may be strings)
    try:
        ordered_qnums = sorted(model_answers.keys(), key=lambda k: int(k))
    except Exception:
        # fallback: sort lexicographically
        ordered_qnums = sorted(model_answers.keys())

    model_texts: List[str] = []
    student_texts: List[str] = []
    for q in ordered_qnums:
        model_texts.append(model_answers.get(q, "") or "")
        student_texts.append(student_answers.get(q, "") or "")

    # Batch embeddings: call get_embeddings twice (models then students) to preserve order
    # embedding_client.get_embeddings will raise if GEMINI_API_KEY missing; tests should mock
    model_vectors = embedding_client.get_embeddings(model_texts) if model_texts else []
    student_vectors = embedding_client.get_embeddings(student_texts) if student_texts else []

    per_question = []
    similarities = []

    for idx, q in enumerate(ordered_qnums):
        student_text = student_texts[idx]
        if not student_text:
            sim = 0.0
        else:
            mv = model_vectors[idx] if idx < len(model_vectors) else []
            sv = student_vectors[idx] if idx < len(student_vectors) else []
            sim = _cosine(mv, sv)
        sim_rounded = round(sim, 3)
        similarities.append(sim_rounded)
        per_question.append({"question": int(q) if q.isdigit() else q, "similarity": sim_rounded, "grade": round(sim_rounded * 100)})

    avg_similarity = float(sum(similarities) / len(similarities)) if similarities else 0.0
    grade = int(round(avg_similarity * 100))

    return {"avg_similarity": avg_similarity, "grade": grade, "per_question": per_question}
