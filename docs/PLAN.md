# CampusOS AI — Development Plan, Risks & Prerequisites

**Date:** 2026-09-21 · **Deadline: 2026-09-30 23:59 IST** · **Solo · 9 days**

---

## Strategy

Build the **thinnest vertical slice that runs end to end on day 1**, then thicken it. The alternative — building ingest fully, then retrieval fully, then the LLM — means the first end-to-end run happens on day 6, and any integration surprise is then fatal. A working ugly loop on day 1 converts every later day from *risk* into *improvement*.

**Day 8 is a hard freeze.** Day 9 is for submission mechanics only. Anything unfinished on day 8 gets cut, not rushed.

---

## Prerequisites

### Hardware

| Item | Status |
|---|---|
| Dev machine (Intel x64, 7.7 GB) | **AVAILABLE** |
| Microphone (Intel Smart Sound array) | **AVAILABLE** |
| Webcam | **AVAILABLE** (not needed) |
| Free disk ≥ 6 GB | **AVAILABLE** (45.9 GB) |
| Snapdragon X device | **MISSING — NOT BLOCKING.** Rules permit "intended to be optimized for" |
| NPU profiling access | **MISSING — NOT BLOCKING** for MVP |

### Software

| Item | Status | Action |
|---|---|---|
| Windows 11 build 26200 | AVAILABLE | — |
| Python 3.10.2 | AVAILABLE | Sufficient for MVP |
| Python 3.11+ | **MISSING** | **OPTIONAL** — only needed for QNN AOT work |
| Node 22.12 / npm | AVAILABLE | Not needed (no build step) |
| Git 2.52 | AVAILABLE | — |
| CMake 4.2 | AVAILABLE | — |
| VS Build Tools 2026 | AVAILABLE | — |
| winget | **MISSING** | OPTIONAL — install manually instead |
| llama.cpp server binary | MISSING | **BLOCKING** — day 1 |
| `onnxruntime`, `fastapi`, `uvicorn`, `pymupdf`, `numpy`, `psutil` | MISSING | **BLOCKING** — day 1 (all small, pip) |
| GGUF LLM weights (~1.1 GB) | MISSING | **BLOCKING** — day 1 |
| Whisper ONNX | MISSING | BLOCKING — day 3 |
| Embedding model ONNX | MISSING | **BLOCKING** — day 1 |

### Accounts & assets

| Item | Status |
|---|---|
| Qualcomm AI Hub account | **MISSING — recommended** (needed to download AI Hub artefacts; free) |
| GitHub account + public repo | **ASSUMED AVAILABLE — required for submission** |
| Unstop registration | **UNKNOWN — VERIFY TODAY** |
| 3–5 real course PDFs | **MISSING — BLOCKING for evaluation.** Must be genuine material, not lorem ipsum |
| Recorded audio samples (EN + HI) | MISSING — can self-record |

> **Two non-technical blockers worth checking before writing code:** Unstop registration status, and whether you have real course PDFs. The evaluation set is worthless without authentic material, and a great build cannot be submitted from an unregistered account.

---

## Phases

### Phase 1 — Environment & vertical slice · Day 1 *(Difficulty: M)*

**Objective:** text question → cited answer, from a real PDF, end to end. Ugly is fine.

**Tasks:** create repo + structure · install deps · download GGUF + embedding ONNX · start llama.cpp server, confirm `/v1/chat/completions` · PyMuPDF extract one PDF · chunk · embed · NumPy cosine · one grounded prompt · print answer + page cite in the terminal.

**Also (30 min, high value):** verify licences for the chosen LLM, and check whether **Qwen3.5-2B via GenieX** is viable — it is AI-Hub-featured, which is the strongest evidence for the Technical Implementation criterion (`MODEL_EVALUATION.md` §2).

**Measure and record:** model load time, peak RSS, tokens/s. This replaces the projected memory table with real numbers.

**DoD:** one terminal command answers a real question about a real PDF with a correct page citation. **Verification:** open the cited page; the claim is there.
**Risk:** model too slow or too large on 7.7 GB → drop to a smaller quant or Whisper-Tiny tier. *Finding this out on day 1 is the entire point of this phase.*

---

### Phase 2 — Backend, store & refusal gate · Day 2 *(M)*

**Objective:** the slice becomes a real API with persistence and an honest failure mode.

**Tasks:** FastAPI app · SQLite schema (documents, chunks, quizzes, attempts) · vectors.npy · `/api/documents` (POST/GET/DELETE incl. hard delete) · `/api/ask` · **relevance-gate refusal path** · citation validation against supplied chunks · upload validation (size, magic bytes, page cap).

**DoD:** multi-document ingest; `/api/ask` returns answer + validated citations; out-of-corpus question triggers refusal **without inventing an answer**.
**Risk:** poor chunking hurts retrieval → tune size/overlap against the eval set, not by feel.

---

### Phase 3 — UI · Day 3 *(S)*

**Objective:** the demo surface.

**Tasks:** single page, three zones (Library / Ask / Quiz) · upload with progress · answer rendering with **clickable citations that open the source page** · language selector · keyboard-accessible throughout · AA contrast.

**DoD:** the full Phase-2 loop is usable in a browser by mouse *and* by keyboard alone.

---

### Phase 4 — Speech · Day 4 *(L — highest technical risk)*

**Objective:** voice-first becomes real.

**Tasks:** Whisper ONNX via ORT with the provider-selection logic from `TRD.md` §15 · `MediaRecorder` push-to-talk · 16 kHz mono decode · `/api/transcribe` · **show transcript for confirmation before querying** · discard audio buffer · mic-denied fallback to text.

**DoD:** hold button → speak English question → transcript → cited answer. Measure ASR latency vs audio duration.
**Risk:** ONNX Whisper integration is the likeliest day-sink. **Timebox to one day.** If it stalls, fall back to `faster-whisper` (CPU) to keep the feature, and document that the fallback has no NPU path.

---

### Phase 5 — Quiz loop · Day 5 *(M — highest product value)*

**Objective:** the differentiator. **The single most important phase for Innovation scoring.**

**Tasks:** chunk sampling spread across the document · LLM generates questions **each carrying its source chunk id** · `/api/quiz`, `/api/quiz/{id}/submit` · scoring · per-question explanation from the source chunk · cluster wrong answers into a named weak topic · link weak topic back into `/api/ask`.

**DoD:** generate → answer → score → **named weak topic** → one click returns a grounded explanation of exactly that topic.
**Risk:** a 1.5B model writes weak distractors → constrain with a strict output schema and few-shot examples; validate parseability and regenerate on failure.

---

### Phase 6 — Multilingual output · Day 6 morning *(S)*

**Tasks:** language selector wired to prompt · Hinglish / Hindi / English system prompts · verify citations survive translation · manual quality review.

**DoD:** the same question answered in all three, citations intact, reviewed by a native speaker (you).
**Risk:** weak Hinglish → fall back to Hindi-only and say so plainly. Do not ship a claim the output does not support.

---

### Phase 7 — Evaluation & benchmarks · Day 6 afternoon – Day 7 *(M)*

**Tasks:** build the eval set (20–30 Q/A from real PDFs + 10 out-of-corpus probes) · groundedness and refusal scoring · quiz correctness review · `benchmarks/run.py` (load, ingest, ASR, retrieval, TTFT, tok/s, peak RSS, active EP) · **airplane-mode test + zero-egress assertion** · commit the results table.

**DoD:** a committed benchmark table with real numbers from this machine, and a Snapdragon column **left empty and labelled "requires hardware."**
**Gates:** groundedness ≥ 90 % · refusal 100 % · quiz correctness ≥ 85 %. Miss a gate → fix before adding features.

---

### Phase 8 — Snapdragon path & packaging · Day 7–8 *(M)*

**Tasks:** `scripts/setup_snapdragon.md` (GenieX install, GGUF reuse, ORT QNN plugin, Python 3.11+, `QnnHtp.dll` backend path) · verify the provider-selection code path by unit test (cannot execute QNN here) · `python -m campusos` single-command start · first-run model download with progress · README with the 8 GB floor.

**DoD:** a reviewer with a Snapdragon laptop could follow the doc and run it. Every NPU claim carries a citation and an explicit "not measured by us."

---

### Phase 9 — Freeze, docs & demo · Day 8 *(M)*

**FEATURE FREEZE at the start of this day.**

**Tasks:** generate the remaining documents **from the built system** — `DECISIONS.md` (ADRs as actually decided), `BENCHMARKING.md` + `EVALUATION.md` (real results), `SECURITY_PRIVACY.md`, `THREAT_MODEL.md`, `DIFFERENTIATION.md`, `COMPETITIVE_ANALYSIS.md`, `COMPETITION_MAPPING.md`, `DEMO.md`, `PROGRESS.md` · record the demo video following `MVP_SCOPE.md` "Definition of Done", **Wi-Fi visibly off** · screenshots.

> Writing these now rather than on day 1 is deliberate: they describe what was built instead of what was hoped, which is both more accurate and directly better for the Presentation & Documentation criterion.

---

### Phase 10 — Submission · Day 9 *(S)*

**Tasks:** public repo with licences and attribution · `SUBMISSION_CHECKLIST.md` · verify every Unstop intake field · originality check · **submit with hours to spare.**

> **The rules state a submission cannot be changed after it is submitted.** Do not submit at 23:50. Target midday on day 9.

---

## Risk Register

| ID | Risk | P | I | Detection | Mitigation | Fallback |
|---|---|---|---|---|---|---|
| R-001 | No Snapdragon hardware | Certain | **Low** | Known | Rules permit "intended to be optimized for"; document path + harness | Present path + citations, never fake numbers |
| R-002 | Model can't run on NPU | Med | Low | Cannot test | QNN listed first, CPU fallback in the same provider list | CPU; disclose |
| R-003 | Whisper too large / too slow | Med | Med | Phase 4 | Whisper-Small-Quantized → Tiny | `faster-whisper` CPU (no NPU path — disclose) |
| R-004 | Hindi/Hinglish quality insufficient | Med | Low | Phase 6 | Output-side only; input not promised | Hindi-only, or English-only; state plainly |
| R-005 | LLM latency too high on 7.7 GB | Med | Med | **Phase 1, day 1** | 1.5B Q4 chosen for headroom | Smaller quant; stream tokens so perceived latency drops |
| R-006 | RAG hallucination | Med | **High** | Phase 7 gate | Relevance gate + citation validation against supplied chunks | Raise threshold; refuse more often — refusing is the correct failure |
| R-007 | Windows/ARM64 package incompatibility | Low | Med | Not testable here | Pure-Python + ORT + external LLM server; no exotic native deps | Documented alternatives |
| R-008 | Qualcomm runtime install issues | Med | Low | Not testable here | Follow official GenieX/QNN docs; cite versions | CPU backend via same GGUF |
| R-009 | Model licensing problem | **Med** | **High** | Phase 1 check | Licence is a gate, not a formality; 3B tiers and Llama/Gemma terms flagged | Phi-3.5-mini (MIT) |
| R-010 | Becomes a generic PDF chatbot | Med | **High** | Self-review | Quiz + weak-topic loop is MUST-HAVE; refusal path is visible | **Never cut Phase 5** |
| R-011 | **9-day deadline overrun** | **High** | **High** | Daily | Vertical slice first; day-8 freeze; docs generated from the build | Cut SHOULD/COULD ruthlessly; MUST list is the floor |
| R-012 | **Not registered on Unstop** | Unknown | **Critical** | **Check today** | Verify immediately | None — this is unrecoverable if missed |
| R-013 | No real course PDFs for evaluation | Med | Med | Day 1 | Gather before Phase 7 | Public university syllabus PDFs |

**R-011 and R-012 are the two that actually end the project.** R-012 costs five minutes to eliminate; do it first.

---

## Proposed repository structure

    campusos-ai/
      docs/            planning + generated documentation
      backend/         FastAPI app, ingest, retrieve, answer, asr, quiz
      frontend/        static HTML/CSS/JS, no build step
      models/          downloaded weights (gitignored)
      data/            local SQLite + vectors (gitignored)
      benchmarks/      harness + committed results
      tests/           unit + integration + offline/egress
      eval/            eval set + groundedness scoring
      scripts/         setup, incl. setup_snapdragon.md
      README.md · LICENSE · requirements.txt · .env.example

**Why this shape:** `backend/` and `frontend/` split because the browser is the UI but all AI is server-side. `models/` and `data/` are separate and gitignored because one is downloadable and the other is *the student's private material* — conflating them risks committing personal documents. `benchmarks/` and `eval/` are top-level rather than inside `tests/` because they produce **artefacts for the submission**, not pass/fail signals. `scripts/setup_snapdragon.md` sits beside the code it configures, so the deployment story is part of the repo rather than a claim in a PDF.

---

## What to do first, after approval

1. **Verify Unstop registration** (5 min, R-012).
2. **Confirm you have 3–5 real course PDFs** (R-013).
3. Create the repo and run **Phase 1 in full today** — the day-1 vertical slice is what converts every remaining risk from unknown into managed.
