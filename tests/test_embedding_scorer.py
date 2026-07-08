import sys
import pathlib
import pytest

# Ensure project root is on sys.path for test discovery environments
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from uploaditin_backend.utils.embedding_scorer import embedding_score_submission, _cosine


class DummyEmbeddingClient:
    """Simple mock replacement for embedding_client.get_embeddings.

    We'll monkeypatch uploaditin_backend.utils.embedding_client.get_embeddings
    to point to this function during tests.
    """


def fake_get_embeddings_texts(texts):
    # Return deterministic vectors: vector = [len(text), 0.0, 0.0]
    vecs = []
    for t in texts:
        vecs.append([float(len(t)), 0.0, 0.0])
    return vecs


def test_embedding_score_basic(monkeypatch):
    import uploaditin_backend.utils.embedding_client as ec
    from uploaditin_backend.utils import embedding_scorer as es
    print(f"DEBUG: ec is {ec}")
    print(f"DEBUG: es.embedding_client is {es.embedding_client}")
    print(f"DEBUG: identity match: {ec is es.embedding_client}")
    
    monkeypatch.setattr(ec, "get_embeddings", fake_get_embeddings_texts)
    print(f"DEBUG: ec.get_embeddings is {ec.get_embeddings}")
    print(f"DEBUG: es.embedding_client.get_embeddings is {es.embedding_client.get_embeddings}")

    teacher = "jawaban 1 = The cat sat on the mat\njawaban 2 = Water is wet"
    student = "jawaban 1 = The cat sat on mat\njawaban 2 = Water is wet indeed"

    res = embedding_score_submission(teacher, student)

    # With our fake vectors, similarity is 1.0 when lengths equal, otherwise ratio of lengths
    assert "avg_similarity" in res and "grade" in res and "per_question" in res
    assert isinstance(res["avg_similarity"], float)
    assert isinstance(res["grade"], int)
    assert len(res["per_question"]) == 2

    # Check rounding: similarities are rounded to 3 decimals
    for pq in res["per_question"]:
        assert round(pq["similarity"], 3) == pq["similarity"]


def test_missing_student_answer(monkeypatch):
    import uploaditin_backend.utils.embedding_client as ec
    monkeypatch.setattr(ec, "get_embeddings", fake_get_embeddings_texts)

    teacher = "jawaban 1 = Answer one\njawaban 2 = Answer two"
    student = "jawaban 1 = "  # student missing answer 2

    res = embedding_score_submission(teacher, student)
    assert res["per_question"][0]["similarity"] >= 0.0
    assert res["per_question"][1]["similarity"] == 0.0


def test_no_questions_parsed(monkeypatch):
    import uploaditin_backend.utils.embedding_client as ec
    monkeypatch.setattr(ec, "get_embeddings", fake_get_embeddings_texts)

    teacher = "this has no answers"  # extract_answers will return {}
    student = "some text"
    res = embedding_score_submission(teacher, student)
    assert res["avg_similarity"] == 0.0
    assert res["grade"] == 0
    assert res["per_question"] == []


def test_cosine_zero_magnitude():
    # Test handling of zero magnitude vectors to prevent division by zero
    v1 = [0.0, 0.0, 0.0]
    v2 = [1.0, 2.0, 3.0]

    # One vector is zero
    assert _cosine(v1, v2) == 0.0
    assert _cosine(v2, v1) == 0.0

    # Both vectors are zero
    assert _cosine(v1, v1) == 0.0

    # Empty vectors
    assert _cosine([], []) == 0.0
