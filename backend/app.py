"""FastAPI app, loopback only. No auth by design: single user, 127.0.0.1 bound."""
import json, pathlib, platform, threading
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from . import config, store, ingest, answer, quiz, llm, asr, embed

FRONTEND = pathlib.Path(__file__).parent.parent / "frontend"
app = FastAPI(title="CampusOS AI", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def warm_up():
    """Prefill the model's cache in the background so the first real question is not the one
    that pays for it. Cold TTFT measured at ~11 s on this hardware, warm at ~0.7 s -- and the
    first question is the one a demo viewer judges the product by."""
    def run():
        try:
            llm.chat([{"role": "system", "content": answer.system_prompt("en")},
                      {"role": "user", "content": "ready?"}], max_tokens=1)
        except Exception:
            pass          # the server may not be up yet; health already reports that
    threading.Thread(target=run, daemon=True).start()


@app.get("/api/health")
def health():
    return {"llm": llm.healthy(), "llm_url": config.LLM_BASE_URL,
            "asr": asr.available(), "asr_backend": asr.BACKEND,
            "embed_provider": embed.active_provider(),
            "providers_configured": [p if isinstance(p, str) else p[0] for p in config.ort_providers()],
            "arm64": config.is_arm64_windows(), "machine": platform.machine(),
            "documents": len(store.list_documents()), "chunks": int(store.vectors().shape[0]),
            "gate": config.RELEVANCE_THRESHOLD}


@app.get("/api/documents")
def documents():
    return store.list_documents()


@app.post("/api/documents")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    try:
        return ingest.ingest_pdf(data, file.filename or "document.pdf")
    except ingest.IngestError as e:
        raise HTTPException(400, str(e))


@app.delete("/api/documents/{doc_id}")
def delete(doc_id: str):
    if not store.delete_document(doc_id):
        raise HTTPException(404, "No such document")
    return {"deleted": doc_id}


@app.post("/api/ask")
def ask(body: dict = Body(...)):
    q = (body.get("question") or "").strip()
    if not q:
        raise HTTPException(400, "Empty question")
    try:
        return answer.ask(q, body.get("lang", "en"), body.get("depth", "normal"), body.get("doc_id"))
    except llm.LLMDown as e:
        raise HTTPException(503, str(e))


@app.post("/api/ask/stream")
def ask_stream(body: dict = Body(...)):
    """Server-sent events. Same guarantees as /api/ask; only the delivery differs."""
    q = (body.get("question") or "").strip()
    if not q:
        raise HTTPException(400, "Empty question")

    def events():
        try:
            for kind, payload in answer.ask_stream(
                    q, body.get("lang", "en"), body.get("depth", "normal"), body.get("doc_id")):
                yield f"event: {kind}\ndata: {json.dumps(payload)}\n\n"
        except llm.LLMDown as e:
            # The stream has already started, so an HTTP error code is no longer available.
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = None):
    if not asr.available():
        raise HTTPException(503, "Speech input unavailable (faster-whisper not installed). Type your question instead.")
    try:
        return asr.transcribe(await file.read(), language)
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {e}")


@app.post("/api/quiz")
def make_quiz(body: dict = Body(default={})):
    try:
        return quiz.generate(body.get("doc_id"), int(body.get("n", 5)))
    except llm.LLMDown as e:
        raise HTTPException(503, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/quiz/{qid}/submit")
def submit_quiz(qid: str, body: dict = Body(...)):
    try:
        return quiz.submit(qid, body.get("answers", {}))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/documents/{doc_id}/page/{page}")
def page_text(doc_id: str, page: int):
    """Backs the clickable citation: show the student the actual source page text."""
    rows = [dict(r) for r in store.conn().execute(
        "SELECT text FROM chunks WHERE doc_id=? AND page=? ORDER BY id", (doc_id, page))]
    if not rows:
        raise HTTPException(404, "No text for that page")
    return {"doc_id": doc_id, "page": page, "text": "\n\n".join(r["text"] for r in rows)}


app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="static")
