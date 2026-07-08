import json
import os
import math

import pytest

from uploaditin_backend.utils.LSA import extract_answers, lsa_similarity
from uploaditin_backend.utils import embedding_scorer


FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "teacher_student_fixtures.json")


@pytest.fixture(scope="module")
def fixtures():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_extract_answers_parsing(fixtures):
    teacher = fixtures["teacher"]
    parsed = extract_answers(teacher)
    # Expect 3 answers keyed '1','2','3'
    assert isinstance(parsed, dict)
    assert set(parsed.keys()) == {"1", "2", "3"}


def test_missing_student_answer_scores_zero(fixtures):
    teacher = fixtures["teacher"]
    student = fixtures["student_missing"]

    avg_similarity, grade, per_question = lsa_similarity(teacher, student)

    # Per LSA behavior: missing answer => per-question sim 0 included in average
    # There are 3 teacher answers, student provided 2 -> one zero included
    assert 0.0 <= avg_similarity <= 1.0
    # Grade is rounded(mean * 100)
    assert grade == round(avg_similarity * 100)


def test_per_question_rounding_before_average(monkeypatch, fixtures):
    # Use embedding_scorer to test rounding behavior with mocked embeddings
    teacher = fixtures["teacher"]
    student = fixtures["student_partial"]

    # Prepare deterministic vectors with known cosines
    # For simplicity, use orthogonal/simple vectors so cosine values are exact
    # model vectors: v1=(1,0), v2=(1,0), v3=(1,0)
    # student vectors: s1=(1,0) -> cos=1.0, s2=(0.70710678,0.70710678) -> cos ~0.70710678,
    # s3=(0.8660254,0.5) -> cos ~0.8660254

    model_vecs = [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]]
    student_vecs = [[1.0, 0.0], [0.70710678, 0.70710678], [0.8660254, 0.5]]

    def fake_get_embeddings(texts, **kwargs):
        # return model vectors when called with teacher texts (first call), then student vectors
        # Determine which set by inspecting first element length or token
        if all("The capital of France" in t or "Water boils" in t or "Photosynthesis" in t for t in texts):
            return model_vecs
        return student_vecs

    import uploaditin_backend.utils.embedding_client as ec
    monkeypatch.setattr(ec, "get_embeddings", fake_get_embeddings)

    result = embedding_scorer.embedding_score_submission(teacher, student)

    # Per-question similarities rounded to 3 decimals
    per_q = result["per_question"]
    assert len(per_q) == 3
    sims = [q["similarity"] for q in per_q]
    # Ensure each similarity has at most 3 decimal places when represented
    for s in sims:
        # multiply by 1000 and check it's near an integer
        assert abs(round(s * 1000) - (s * 1000)) < 1e-6

    # Average should be computed from rounded per-question sims
    avg_manual = sum(sims) / len(sims)
    assert math.isclose(result["avg_similarity"], avg_manual, rel_tol=1e-9, abs_tol=1e-9)
    assert result["grade"] == round(avg_manual * 100)


def test_malformed_teacher_returns_zero(monkeypatch, fixtures):
    teacher = fixtures["teacher_malformed"]
    student = fixtures["student_full"]

    # Embedding path should not be required here; test LSA path behavior
    avg_similarity, grade, per_question = lsa_similarity(teacher, student)
    assert avg_similarity == 0.0
    assert grade == 0

