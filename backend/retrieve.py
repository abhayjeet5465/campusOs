"""Brute-force cosine over one matrix multiply, plus the relevance gate.

ponytail: O(n) scan over all chunks. At a few thousand chunks this is sub-millisecond;
add hnswlib only above ~50k chunks.
"""
import numpy as np
from . import config, store, embed


def search(query: str, k=None, doc_id=None):
    k = k or config.TOP_K
    V = store.vectors()
    if V.shape[0] == 0:
        return [], 0.0
    q = embed.embed_query(query)
    scores = V @ q                                  # both sides L2-normalised -> cosine
    order = np.argsort(-scores)[: k * 4 if doc_id else k]
    hits = []
    for row in order:
        c = store.chunks_by_rows([int(row)])
        if not c:
            continue
        if doc_id and c[0]["doc_id"] != doc_id:
            continue
        c[0]["score"] = float(scores[row])
        hits.append(c[0])
        if len(hits) >= k:
            break
    return hits, (hits[0]["score"] if hits else 0.0)


def gated_search(query, k=None, doc_id=None):
    """Returns (hits, grounded). grounded=False -> the caller must take the refusal path (FR-08)."""
    hits, top = search(query, k, doc_id)
    return hits, top >= config.RELEVANCE_THRESHOLD


def demo():
    V = np.array([[1, 0], [0, 1], [0.7, 0.7]], dtype=np.float32)
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    q = np.array([1, 0], dtype=np.float32)
    assert int(np.argmax(V @ q)) == 0, "cosine ranking broken"
    assert (V @ q)[2] > (V @ q)[1], "partial match must outrank orthogonal"
    print("retrieve self-check ok")


if __name__ == "__main__":
    demo()
