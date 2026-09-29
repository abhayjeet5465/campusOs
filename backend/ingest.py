"""PDF -> page-aware chunks -> vectors. Rejects anything without a text layer, loudly."""
import uuid, re
import pymupdf
from . import config, store, embed


class IngestError(Exception):
    pass


def _chunk_page(text, size_chars, overlap_chars):
    """Recursive-ish split on paragraph, then sentence, then hard cut. Page boundaries never crossed."""
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    parts, buf = [], ""
    for para in re.split(r"\n\s*\n", text):
        if len(buf) + len(para) + 1 <= size_chars:
            buf = f"{buf}\n{para}".strip()
            continue
        if buf:
            parts.append(buf)
        while len(para) > size_chars:
            cut = para.rfind(". ", 0, size_chars)
            cut = cut + 1 if cut > size_chars // 2 else size_chars
            parts.append(para[:cut].strip())
            para = para[max(0, cut - overlap_chars):]
        buf = para.strip()
    if buf:
        parts.append(buf)
    return [p for p in parts if len(p) >= 40]     # drop headers/page-number fragments


def ingest_pdf(data: bytes, filename: str, progress=None):
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise IngestError(f"File exceeds {config.MAX_UPLOAD_BYTES // 1024 // 1024} MB limit")
    if not data.startswith(b"%PDF"):
        raise IngestError("Not a PDF (missing %PDF header)")
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as e:
        raise IngestError(f"Could not open PDF: {e}")
    if doc.needs_pass:
        raise IngestError("PDF is password-protected")
    if doc.page_count > config.MAX_PAGES:
        raise IngestError(f"PDF exceeds {config.MAX_PAGES} page limit")

    # ~4 chars/token is the usual English ratio; good enough to size chunks without a tokenizer.
    size_chars, overlap_chars = config.CHUNK_TOKENS * 4, config.CHUNK_OVERLAP * 4
    rows = []
    for i, page in enumerate(doc):
        for c in _chunk_page(page.get_text(), size_chars, overlap_chars):
            rows.append((i + 1, c))
        if progress:
            progress(i + 1, doc.page_count)
    pages = doc.page_count
    doc.close()

    if not rows:
        raise IngestError("No extractable text — this looks like a scanned PDF. OCR is not supported yet.")

    doc_id = uuid.uuid4().hex
    vecs = embed.embed([t for _, t in rows])
    store.add_document(doc_id, filename, pages, rows, vecs)
    return {"id": doc_id, "name": filename, "pages": pages, "chunks": len(rows)}


def demo():
    cs = _chunk_page("A" * 100 + "\n\n" + "B" * 5000, 400, 50)
    assert cs and all(len(c) <= 460 for c in cs), [len(c) for c in cs]
    assert _chunk_page("tiny", 400, 50) == [], "short fragments must be dropped"
    assert _chunk_page("", 400, 50) == []
    print("ingest self-check ok:", len(cs), "chunks")


if __name__ == "__main__":
    demo()
