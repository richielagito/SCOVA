import fitz  
from docx import Document  
import os
import re
import logging
import numpy as np
from collections import Counter
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

logger = logging.getLogger(__name__)

# --- File Read ---

def extract_text_from_pdf(path):
    try:
        doc = fitz.open(path)
        return " ".join(page.get_text("text") for page in doc.pages())
    except Exception as e:
        logger.error("Error membaca PDF %s: %s", path, e)
        return ""

def extract_text_from_docx(path):
    try:
        doc = Document(path)
        return " ".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error("Error membaca DOCX %s: %s", path, e)
        return ""

def extract_text_from_txt(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error("Error membaca TXT %s: %s", path, e)
        return ""

def extract_text_from_any(path):
    ext = os.path.splitext(path)[-1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    elif ext == ".txt":
        return extract_text_from_txt(path)
    else:
        logger.warning("Format tidak didukung: %s", ext)
        return ""

def extract_answers(text):
    pattern = r"jawaban\s*(\d+)\s*=\s*((?:.|\n)*?)(?=jawaban\s*\d+\s*=|\Z)"
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    return {num.strip(): ans.strip() for num, ans in matches}

# --- Text Preprocessing ---

_stemmer = None
_stopword_remover = None


def _get_stemmer():
    global _stemmer
    if _stemmer is None:
        _stemmer = StemmerFactory().create_stemmer()
    return _stemmer


def _get_stopword_remover():
    global _stopword_remover
    if _stopword_remover is None:
        _stopword_remover = StopWordRemoverFactory().create_stop_word_remover()
    return _stopword_remover


def preprocess(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = _get_stopword_remover().remove(text)
    text = _get_stemmer().stem(text)
    tokens = text.split()
    return tokens

# --- TFIDF ---
def compute_tfidf(docs):
    vocabulary = sorted(set(word for doc in docs for word in doc))
    vocab_index = {word: idx for idx, word in enumerate(vocabulary)}
    N = len(docs)

    tfidf_matrix = np.zeros((N, len(vocabulary)))
    df = Counter()

    for doc in docs:
        unique_words = set(doc)
        for word in unique_words:
            df[word] += 1

    for i, doc in enumerate(docs):
        word_counts = Counter(doc)
        total_words = len(doc)
        for word, count in word_counts.items():
            tf = count / total_words
            idf = np.log((N + 1) / (df[word] + 1)) + 1 
            tfidf_matrix[i][vocab_index[word]] = tf * idf

    return tfidf_matrix

def truncated_svd(matrix, n_components=2):
    n_components = min(n_components, matrix.shape[0], matrix.shape[1])
    U, S, VT = np.linalg.svd(matrix, full_matrices=False)
    S_matrix = np.diag(S[:n_components])
    return np.dot(U[:, :n_components], S_matrix)

def cosine_similarity(a, b):
    numerator = np.dot(a, b)
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return numerator / denominator if denominator != 0 else 0.0

def lsa_similarity(guru_text, siswa_text):
    model_answers = extract_answers(guru_text)
    student_answers = extract_answers(siswa_text)
    results = {}

    for num, model_ans in model_answers.items():
        student_ans = student_answers.get(num, "")
        if not student_ans:
            results[num] = 0.0
            continue

        # Preprocess
        model_tokens = preprocess(model_ans)
        student_tokens = preprocess(student_ans)

        # TF-IDF
        tfidf_matrix = compute_tfidf([model_tokens, student_tokens])

        # Truncated SVD
        reduced = truncated_svd(tfidf_matrix, n_components=2)

        # Cosine similarity
        sim = cosine_similarity(reduced[0], reduced[1])
        results[num] = round(sim, 3)

    jumlah_soal = len(model_answers)
    total_similarity = sum(results.values())
    avg_similarity = (total_similarity / jumlah_soal) if jumlah_soal > 0 else 0
    skor_akhir = round(avg_similarity * 100)  

    per_question = [
        {"question": int(q) if q.isdigit() else q, "similarity": sim, "grade": round(sim * 100)}
        for q, sim in results.items()
    ]

    return avg_similarity, skor_akhir, per_question
