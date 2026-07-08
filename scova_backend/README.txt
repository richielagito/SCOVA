essay_grader/
├── app.py                        # Flask app utama
├── requirements.txt              # Semua dependensi
├── templates/
│   └── index.html                # Form upload PDF
├── uploads/                      # Tempat simpan file PDF upload
├── data/                         # Tempat simpan hasil penilaian CSV
├── utils/
│   ├── pdf_reader.py             # Ekstrak teks dari PDF
│   ├── preprocessing.py          # Preprocessing teks Bahasa Indonesia
│   ├── tfidf_manual.py           # Perhitungan TF-IDF manual
│   ├── lsa_manual.py             # SVD manual dan cosine similarity
│   └── db.py                     # Simpan hasil ke PostgreSQL


HARUS BUKA FILE db.py UNTUK CONNECT KE PG ADMIN, ROUTE DAN PASSWORD GANTI SESUAI YANG UDAH DI SETTING YA.

pip install -r requirements.txt (UNTUK INSTALL LIBRARY DI requirements.txt)

Kelompok 11 (NLP):
OctoNik | Nikolaus Nathaniel (535230113)
Borjues | Dhani Andika Maharsi (535230149)

Kelompok 11 (Software Development):
Jalsson (535230145)
Richie Lagito (535230037)
Nikolaus Nathaniel (535230113)
Dhani Andika Maharsi (535230149)
