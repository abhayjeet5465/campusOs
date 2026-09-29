# CampusOS AI — Technical Requirements Document

**Date:** 2026-09-21 · **Phase:** 0

---

## 1. System overview

A single-user local application: a Python backend on `127.0.0.1` serving a static frontend, with all AI inference performed by local runtimes. No server component, no accounts, no cloud dependency after first-run model download.

**The organising principle:** every AI runtime is reached through an interface that has both an x86_64 implementation and a Snapdragon implementation. Porting is therefore configuration, not engineering.

| Workload | Interface | Dev host (x64) | Target host (Snapdragon) |
|---|---|---|---|
| LLM | OpenAI-compatible HTTP `/v1` | llama.cpp server (CPU) | **GenieX (NPU/GPU/CPU)** |
| ASR | ONNX Runtime session | ORT `CPUExecutionProvider` | ORT `QNNExecutionProvider` |
| Embeddings | ONNX Runtime session | ORT `CPUExecutionProvider` | ORT `QNNExecutionProvider` |

## 2. Architecture

    ┌──────────────────────────────────────────────┐
    │  Browser UI (vanilla JS + HTML)  127.0.0.1   │
    │  Library  │  Ask (voice/text)  │  Quiz       │
    └───────────────────┬──────────────────────────┘
                        │ HTTP (localhost only)
    ┌───────────────────▼──────────────────────────┐
    │  FastAPI backend                             │
    │  ingest · retrieve · answer · asr · quiz     │
    └──┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │
    ┌──▼───┐  ┌───▼────┐ ┌───▼─────┐ ┌──▼────────┐
    │PyMuPDF│ │Embedder│ │  ASR    │ │LLM client │
    │parse  │ │ (ORT)  │ │ (ORT)   │ │(OpenAI API)│
    └───────┘ └───┬────┘ └───┬─────┘ └──┬────────┘
                  │          │           │
              ┌───▼──────────▼───┐   ┌───▼─────────────┐
              │ SQLite + NumPy   │   │ llama.cpp       │
              │ chunks + vectors │   │   or GenieX     │
              └──────────────────┘   └─────────────────┘

## 3. Components

| Component | Responsibility | Tech |
|---|---|---|
| `ingest` | PDF → page-aware chunks → embeddings → store | PyMuPDF, ORT |
| `store` | Chunks, vectors, documents, quiz history | SQLite + NumPy |
| `retrieve` | Query embed → cosine top-k → threshold gate | NumPy |
| `answer` | Prompt assembly, grounding constraints, citation extraction | LLM client |
| `asr` | Audio → text | ORT Whisper |
| `quiz` | Generate, evaluate, detect weak topics | LLM client + store |
| `bench` | Latency/memory/offline harness | stdlib + psutil |

## 4. Data flow

**Ingest:** upload → validate (size, type, magic bytes) → PyMuPDF extract per page → recursive chunk (~800 tok, ~120 overlap) carrying `(doc_id, page)` → embed batch → persist.

**Ask:** (voice → ASR →) query text → embed → cosine top-k → **relevance gate** → if below threshold, refusal path → else assemble prompt → LLM → parse citations → return answer + sources.

**Quiz:** select doc/topic → sample representative chunks → LLM generates Q/A/distractors **with the source chunk id attached to each question** → student answers → score → per-question explanation cites the origin chunk → cluster incorrect answers by topic → name weak topic.

> Attaching the source chunk id at *generation* time is what makes quiz explanations grounded and weak-topic detection meaningful. It costs nothing and cannot be retrofitted reliably.

## 5. AI inference flow — CPU / GPU / NPU per workload

| Workload | Dev (Intel i5, no NPU) | Target (Snapdragon X) | NPU status |
|---|---|---|---|
| PDF parse | CPU | CPU | N/A — not an AI workload |
| Chunking | CPU | CPU | N/A |
| **Embeddings** | **CPU** (ORT CPU EP) | **NPU** via ORT QNN EP (`QnnHtp.dll`) | **Path documented, NOT verified — no hardware** |
| **ASR (Whisper)** | **CPU** (ORT CPU EP) | **NPU** via ORT QNN EP; Qualcomm ships QAIRT context binaries | **Path documented, NOT verified** |
| **LLM prefill** | **CPU** (llama.cpp) | **NPU/GPU** via GenieX | **Path documented, NOT verified** |
| **LLM decode** | **CPU** | NPU/GPU via GenieX — but memory-bandwidth-bound | **Expect throughput/power gains, not a large per-token latency win** |
| Cosine search | CPU (NumPy) | CPU | N/A — microseconds at this scale |

**Explicit statement for the submission:** no NPU execution has been measured. The dev machine has no NPU and, per ONNX Runtime documentation, `win-x64` supports QNN **quantization and AOT compilation only, not inference**. All NPU claims in this project are *documented deployment paths with citations*, never measured results.

## 6. Document ingestion pipeline

Validate (≤50 MB, `%PDF` magic bytes, page cap) → open with PyMuPDF → reject if no text layer with a clear message → per-page text + page index → recursive splitter preserving page boundaries → drop chunks below a minimum length → batch-embed → L2-normalise → persist vectors as a single NumPy array plus SQLite rows.

## 7. RAG pipeline

- **Embed:** `multilingual-e5-small`, 384-d, ONNX, normalised.
- **Search:** brute-force cosine via one matrix multiply. At a few thousand chunks this is sub-millisecond — an ANN index would be pure complexity. *`ponytail:` O(n) scan; add `hnswlib` above ~50k chunks.*
- **Gate:** if top score < threshold → refusal path. **This gate is the anti-hallucination mechanism** and is tested explicitly.
- **Prompt:** system instruction constraining the model to the provided context; context blocks delimited and labelled with `[doc, p.N]`; instruction to cite and to say when the answer is absent.
- **Citations:** parsed from output and validated against the chunks actually supplied — a citation the model invented for a chunk it was not given is dropped.

## 8. Speech pipeline

Browser `MediaRecorder` (push-to-talk, explicit user gesture) → POST audio → decode to 16 kHz mono → Whisper ONNX via ORT → transcript returned and **displayed for confirmation before it is used as a query**. Audio buffer discarded after transcription; never persisted.

## 9. Quiz pipeline

Sample chunks (spread across the document, not the top-k of one query) → LLM generates N questions, each carrying its source chunk id → student answers → exact/semantic scoring → per-question explanation from the source chunk → incorrect answers clustered by topic label → weakest topic surfaced with a link back into `answer`.

## 10. Local storage

    %LOCALAPPDATA%/CampusOS/
      campusos.db      SQLite: documents, chunks, quizzes, attempts
      vectors.npy      float32 [n_chunks, 384]
      models/          GGUF + ONNX weights
      logs/            local only, content-redacted

## 11. API (all `127.0.0.1` only)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/documents` | Upload + ingest |
| GET | `/api/documents` | List |
| DELETE | `/api/documents/{id}` | Hard delete incl. vectors |
| POST | `/api/ask` | Question → grounded answer + citations |
| POST | `/api/transcribe` | Audio → text |
| POST | `/api/quiz` | Generate |
| POST | `/api/quiz/{id}/submit` | Evaluate + weak topics |
| GET | `/api/health` | Backend + model status |

## 12. Frontend architecture

Vanilla HTML/CSS/JS, no build step. Rationale: a build toolchain adds Node dependency, bundler config, and an ARM64 story for zero user-visible benefit in a single-screen app. Fewer moving parts is the correct engineering choice here, and it removes an entire class of deployment failure on the target machine.

## 13. Backend architecture

FastAPI + Uvicorn, single process. Models loaded once at startup into module-level singletons. Ingestion runs in a background task with progress polling. No auth (loopback-bound, single user by design).

## 14. Model serving

- **LLM:** external process (llama.cpp `server` / GenieX server), reached over OpenAI-compatible HTTP. **Deliberately out-of-process** — it isolates the largest memory consumer and the most platform-specific component, which is precisely what makes the Snapdragon swap a config change.
- **ASR & embeddings:** in-process ORT sessions; provider list selected at startup by platform detection.

## 15. Hardware acceleration architecture

Startup detects platform and selects providers:

    providers = (
        [("QNNExecutionProvider", {"backend_path": "QnnHtp.dll"}), "CPUExecutionProvider"]
        if is_arm64_windows() else
        ["CPUExecutionProvider"]
    )

QNN first, CPU as fallback in the same list — so an unsupported graph degrades gracefully instead of crashing. The active provider is reported in `/api/health` and recorded in every benchmark run, so no result is ever ambiguous about which hardware produced it.

## 16. Security

Loopback binding only · file-type and magic-byte validation · size and page caps · filenames sanitised, never used as paths (UUID storage names) · no shell execution · no `pickle` · CORS restricted to the local origin · PDF text treated strictly as **data** in delimited context blocks, never as instructions.

## 17. Privacy

No telemetry, analytics, or crash reporting. Logs record events and timings, never document content or transcripts. Audio never touches disk. Delete is hard delete across SQLite rows and the vector array. Any future network call must be opt-in and visibly surfaced.

## 18. Failure handling

Model load failure → degraded mode with a clear banner, other features stay usable · LLM backend down → explicit message plus start instructions · OOM → suggest the smaller model tier · corrupt PDF → per-document failure, never a global one · ASR failure → fall back to text input.

## 19. Logging

Local rotating file. Levels: startup config (incl. active EP), ingest timings, retrieval scores, inference latencies, errors. **Never** document text, questions, answers, or transcripts. Content-redaction is enforced at the logging helper, not left to each call site.

## 20. Telemetry

**None.** Deliberate. Benchmark data is written locally and shared only if the student chooses to.

## 21. Testing

- Unit: chunking boundaries, citation parsing/validation, cosine ranking, relevance gate.
- Integration: ingest → ask → cited answer; quiz → score → weak topic.
- **Groundedness:** a fixed eval set with known answers and known out-of-corpus probes; refusal must be 100 % on probes.
- **Offline:** networking disabled; full loop must pass.
- **Egress assertion:** no outbound sockets during a full cycle.
- Per ponytail: one runnable self-check per non-trivial module, `assert`-based, no framework ceremony.

## 22. Deployment

Single command: `python -m campusos` → starts backend, opens browser. First run downloads models with visible progress and a stated size. A `scripts/setup_snapdragon.md` documents the ARM64 path (GenieX install, ORT QNN plugin, Python 3.11+). One codebase, two runtime configurations.

## 23. Performance benchmarking

`benchmarks/run.py` measures, on a fixed corpus and question set: model load time · ingest throughput (pages/s) · embedding latency · ASR latency vs audio duration · retrieval latency · time-to-first-token · tokens/s · peak RSS · CPU utilisation · offline pass/fail.

Every result records: machine, CPU, RAM, OS, **active execution provider**, model + quantization, and commit hash. Output is a Markdown table committed to the repo.

**Rules, non-negotiable:** the harness must run on Snapdragon unmodified, so the numbers are directly comparable when hardware becomes available. Snapdragon columns stay **empty and labelled "requires hardware"** until genuinely measured. No estimated, extrapolated, or vendor-quoted figure is ever presented as our own measurement.
