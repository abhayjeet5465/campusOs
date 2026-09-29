"""SQLite rows + one NumPy vector array. No ORM, no migrations -- one file, one schema."""
import sqlite3, json, threading
import numpy as np
from . import config

_lock = threading.Lock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents(
  id TEXT PRIMARY KEY, name TEXT NOT NULL, pages INT, chunks INT,
  created REAL DEFAULT (strftime('%s','now')));
CREATE TABLE IF NOT EXISTS chunks(
  id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT NOT NULL, page INT NOT NULL,
  text TEXT NOT NULL, vec_row INT NOT NULL,
  FOREIGN KEY(doc_id) REFERENCES documents(id));
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE TABLE IF NOT EXISTS quizzes(
  id TEXT PRIMARY KEY, doc_id TEXT, questions TEXT NOT NULL,
  created REAL DEFAULT (strftime('%s','now')));
CREATE TABLE IF NOT EXISTS attempts(
  id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_id TEXT NOT NULL,
  result TEXT NOT NULL, score REAL, weak_topics TEXT,
  created REAL DEFAULT (strftime('%s','now')));
"""


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        _conn.commit()
    return _conn


def _load_vectors() -> np.ndarray:
    if config.VEC_PATH.exists():
        v = np.load(config.VEC_PATH)
        if v.ndim == 2 and v.shape[1] == config.EMBED_DIM:
            return v.astype(np.float32)
    return np.zeros((0, config.EMBED_DIM), dtype=np.float32)


_vectors = None


def vectors() -> np.ndarray:
    global _vectors
    if _vectors is None:
        _vectors = _load_vectors()
    return _vectors


def add_document(doc_id, name, pages, chunk_rows, vecs: np.ndarray):
    """chunk_rows: list of (page, text). vecs: [n, dim] L2-normalised, aligned with chunk_rows."""
    assert len(chunk_rows) == vecs.shape[0], "chunk/vector count mismatch"
    global _vectors
    with _lock:
        base = vectors().shape[0]
        c = conn()
        c.execute("INSERT OR REPLACE INTO documents(id,name,pages,chunks) VALUES(?,?,?,?)",
                  (doc_id, name, pages, len(chunk_rows)))
        c.executemany("INSERT INTO chunks(doc_id,page,text,vec_row) VALUES(?,?,?,?)",
                      [(doc_id, p, t, base + i) for i, (p, t) in enumerate(chunk_rows)])
        c.commit()
        _vectors = np.vstack([vectors(), vecs.astype(np.float32)])
        np.save(config.VEC_PATH, _vectors)


def list_documents():
    return [dict(r) for r in conn().execute(
        "SELECT id,name,pages,chunks,created FROM documents ORDER BY created DESC")]


def delete_document(doc_id) -> bool:
    """Hard delete incl. vectors (FR-15). Rows are compacted and vec_row reindexed."""
    global _vectors
    with _lock:
        c = conn()
        rows = [r["vec_row"] for r in c.execute("SELECT vec_row FROM chunks WHERE doc_id=?", (doc_id,))]
        if not c.execute("SELECT 1 FROM documents WHERE id=?", (doc_id,)).fetchone():
            return False
        keep = np.ones(vectors().shape[0], dtype=bool)
        keep[[r for r in rows if r < keep.size]] = False
        # old row index -> new row index after compaction
        remap = np.cumsum(keep) - 1
        c.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
        c.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        for cid, old in c.execute("SELECT id,vec_row FROM chunks").fetchall():
            c.execute("UPDATE chunks SET vec_row=? WHERE id=?", (int(remap[old]), cid))
        c.commit()
        _vectors = vectors()[keep]
        np.save(config.VEC_PATH, _vectors)
    return True


def chunks_by_rows(rows):
    if not rows:
        return []
    q = ",".join("?" * len(rows))
    out = {r["vec_row"]: dict(r) for r in conn().execute(
        f"SELECT c.id,c.doc_id,c.page,c.text,c.vec_row,d.name FROM chunks c "
        f"JOIN documents d ON d.id=c.doc_id WHERE c.vec_row IN ({q})", list(rows))}
    return [out[r] for r in rows if r in out]


def sample_chunks(doc_id, n):
    """Spread across the document, not top-k of one query (TRD §9)."""
    rows = [dict(r) for r in conn().execute(
        "SELECT c.id,c.doc_id,c.page,c.text,d.name FROM chunks c JOIN documents d ON d.id=c.doc_id"
        + (" WHERE c.doc_id=?" if doc_id else "") + " ORDER BY c.page,c.id",
        (doc_id,) if doc_id else ())]
    if len(rows) <= n:
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def save_quiz(qid, doc_id, questions):
    conn().execute("INSERT INTO quizzes(id,doc_id,questions) VALUES(?,?,?)",
                   (qid, doc_id, json.dumps(questions)))
    conn().commit()


def get_quiz(qid):
    r = conn().execute("SELECT * FROM quizzes WHERE id=?", (qid,)).fetchone()
    return json.loads(r["questions"]) if r else None


def save_attempt(qid, result, score, weak):
    conn().execute("INSERT INTO attempts(quiz_id,result,score,weak_topics) VALUES(?,?,?,?)",
                   (qid, json.dumps(result), score, json.dumps(weak)))
    conn().commit()
