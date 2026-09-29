# CampusOS AI — Feasibility Report

**Phase:** 0 (Research → Feasibility)
**Date:** 2026-09-21
**Dev machine:** HP 15s-fr4xxx · Intel i5-1155G7 (x86_64) · 7.7 GB RAM · Iris Xe · Windows 11 build 26200
**Status:** GO, with a materially re-scoped MVP driven by a 9-day deadline.

---

## 1. Executive Summary

CampusOS AI is feasible as a local-first, voice-enabled, source-grounded study assistant **within the deadline**, provided the MVP is scoped to what can be demonstrated on the available x86_64 hardware while being architecturally and verifiably portable to Snapdragon.

Three findings dominate every other consideration:

1. **The deadline is 2026-09-30 23:59 IST — 9 days away.** Verified directly from Unstop's API (`end_date: 2026-09-30T23:59:00+05:30`), not from a blog. This is the binding constraint on all scope.

2. **Snapdragon hardware is NOT required to submit.** The official rules say the solution must be *"designed, developed, **or intended to be optimized for** Snapdragon-powered HP PCs."* The disjunction is decisive: a solution architected and evidenced for Snapdragon satisfies the rule. This retires the single largest project risk.

3. **GenieX makes the dev/target gap nearly free.** Qualcomm's GenieX runtime runs **GGUF** models on Snapdragon NPU/GPU/CPU and exposes an **OpenAI-compatible HTTP server**. `llama.cpp` and LM Studio run the *same GGUF files* behind the *same OpenAI-compatible API* on x86_64. The application therefore targets one interface and swaps hosts via a single base-URL environment variable — no rewrite, no abstraction layer we had to invent.

The honest caveat: the machine has **7.7 GB RAM and no NPU**. Measured NPU numbers cannot be produced. The submission must present Snapdragon performance as a *documented, cited deployment path plus a benchmark harness*, never as measured results we did not measure.

---

## 2. Competition Research

### A) Exact competition evidence (high confidence)

| Field | Value |
|---|---|
| Name | Snapdragon® AI Lab Build & Present Challenge |
| Host | Qualcomm |
| Platform | Unstop, opportunity id `1748893` |
| Submission window | 2026-09-04 12:00 IST → **2026-09-30 23:59 IST** |
| Participation | **Individual.** "Only one submission per participant"; work "solely owned by the participant" |
| Eligibility | Residents of India, 18+ |
| Language | All materials in English |
| IP | Retained by participant. Submissions are **public, non-confidential** |

**Requirement, verbatim:**
> "The proposed solution must be designed, developed, or intended to be optimized for Snapdragon-powered HP PCs."

> "If the proposal existed before the Challenge Submission Period, it must have been significantly modified to add AI models from Qualcomm AI Hub or other open-source platforms."

Note the second clause permits **"or other open-source platforms"** — AI Hub use is encouraged but not strictly mandatory. We will use AI Hub anyway, because it is the strongest available evidence for the Technical Implementation criterion.

**Evaluation criteria**, in the order the rules list them — and the rules state ties are broken *"by comparing scores in the first applicable criterion listed above, then the next as needed."* That ordering is therefore an implicit priority ranking:

1. **Technical Implementation** ← highest tie-break weight
2. Application Use Case & Innovation
3. Deployment & Accessibility
4. Presentation & Documentation

**Strategic consequence:** a working, technically substantive build outranks documentation volume. Twenty-one speculative planning documents written before any code would invert the scoring priority. Phase 0 is therefore compressed to six decision-critical documents.

### B) Related Qualcomm competition evidence (medium confidence)

The brief named prior projects (Tutor AI, REDACT, GameSense, EdgeFit Coach, SignBridge, EasyForm). I could **partially** verify these:

- **SignBridge** and **EasyForm** are confirmed as outcomes of the Qualcomm Edge AI Developer Hackathon in **Paris**, documented on Qualcomm's official developer blog (Oct 2025). SignBridge does on-device speech→text→translation for hearing-impaired users; EasyForm does on-device document-driven form filling.
- A **Bengaluru** Edge AI hackathon (Nov 2025) is confirmed, with projects described as LLM-driven gameplay commentary and real-time posture coaching — consistent with the names *GameSense* and *EdgeFit Coach*, but I could not retrieve the blog body to confirm those names, models, or runtimes.
- **Tutor AI** and **REDACT**: **not verified.** I found no official Qualcomm source naming them.

**I am explicitly not inventing details for the unverified projects.** Per the brief's own instruction, this is recorded as a gap rather than filled with plausible-sounding fabrication.

**What the verified subset supports:** the confirmed projects (SignBridge, EasyForm) are both **on-device, privacy-motivated, document/speech-centric** applications. That is directly consistent with the brief's prior research. It supports — but on a sample of two, does not conclusively prove — a local-first preference.

**Overlap risk for CampusOS:** SignBridge overlaps on *local speech-to-text*; EasyForm overlaps on *local document understanding*. Neither is an education/learning workflow. CampusOS's whitespace is the **study loop** (ingest → grounded explain → quiz → weak-topic detection), not the individual primitives.

### C) Our engineering recommendation

**Local-first, as a hard requirement.** Justified independently of the winner evidence, on three grounds that hold regardless:

- The rules reward "designed... for Snapdragon-powered HP PCs" — cloud inference makes the Snapdragon PC irrelevant to the product and forfeits the strongest framing for criteria 1 and 3.
- Student academic material is private by default.
- Offline operation is a genuine, demonstrable capability, not a marketing adjective (see §10).

---

## 3. Hardware Feasibility

### Development environment (measured 2026-09-21)

| Property | Value |
|---|---|
| Model | HP HP Laptop 15s-fr4xxx |
| CPU | Intel Core i5-1155G7, 4C/8T, x86_64 |
| RAM | **7.7 GB** |
| GPU | Intel Iris Xe (shared memory) |
| NPU | **None** |
| OS | Windows 11 Home SL, build 26200 |
| Free disk | 45.9 GB |
| Audio in | Intel Smart Sound digital mic array ✅ |
| Camera | HP TrueVision HD ✅ |
| Python | 3.10.2 |
| Node | v22.12.0 · npm 10.9.0 |
| Git | 2.52.0 |
| CMake | 4.2.0 |
| Build tools | Visual Studio Build Tools 2026 ✅ |
| winget | **Missing** |

### Target deployment environment

Snapdragon X / X2 series Copilot+ HP OmniBook (the competition's own prize hardware): Oryon CPU, Adreno GPU, **Hexagon NPU**, Windows 11 on ARM64, typically 16 GB+ unified memory.

### The three constraints that actually shape the design

1. **7.7 GB RAM.** After Windows (~3–4 GB), roughly 3.5–4.5 GB is usable. This caps the local LLM at the **~1.5B–3B parameter class at 4-bit quantization** (~1–2 GB resident). An 8B model is not demonstrable here.
2. **No NPU.** All local inference is CPU. Latency here is a *floor*, not a prediction of Snapdragon performance. We report it as such.
3. **x86_64.** Per ONNX Runtime's QNN documentation, `win-x64` supports **quantization and AOT compilation only** — *"Windows ARM64 (for inferencing on local device with Qualcomm NPU)"*. **QNN inference cannot be executed on this machine.** We can *prepare and compile* NPU artifacts here; we cannot run them.

**Does the workload genuinely benefit from the NPU?** Yes, and specifically — this is not hand-waving:

- **Whisper encoder**: a fixed-shape, convolution-and-attention graph. This is the canonical NPU-friendly workload, and Qualcomm ships pre-compiled QNN binaries for it (§4).
- **Embedding model**: small, fixed-shape, high call volume during ingestion — batch-friendly, NPU-suited.
- **LLM decode**: memory-bandwidth-bound, not compute-bound. GenieX supports NPU here, but the honest expected benefit is **sustained throughput and power efficiency over a long study session**, not a dramatic single-token latency win. We will not overclaim this.

---

## 4. Qualcomm AI Hub Feasibility — GREEN

AI Hub publishes Snapdragon-targeted, pre-compiled models relevant to every CampusOS pipeline stage. Confirmed relevant assets:

- `qualcomm/Whisper-Tiny`, `qualcomm/Whisper-Small-Quantized` — published with Snapdragon X Elite targets, ONNX Runtime + QAIRT context binaries.
- **GenieX** — open-source on-device runtime, GGUF via a llama.cpp plugin plus QAIRT-optimized models; NPU/GPU/CPU; Windows ARM64; **OpenAI-compatible server**; CLI, Python, Java, Docker. Featured models include Qwen3-4B, Qwen3.5-2B, Gemma-4-E2B-it, with 300+ available.
- `qualcomm/ai-hub-apps` — includes an `llm_on_genie` tutorial covering the compile-to-QAIRT-context-binary → run-with-Genie workflow, with a documented Windows PowerShell path.

**Caution recorded:** AI Hub lists a Whisper-Small-Quantized inference time of ~3.78 ms on Snapdragon X Elite. This is a **per-component figure, not end-to-end transcription latency.** It must not be cited as "transcribes in 3.78 ms." Any latency claim we publish must come from our own harness.

---

## 5. Speech Feasibility

| Capability | Verdict | Basis |
|---|---|---|
| English ASR, local | **GREEN** | Whisper is mature; Qualcomm ships Snapdragon-targeted Whisper-Tiny/Small |
| Hindi ASR, local | **YELLOW** | Whisper multilingual supports Hindi, but small variants degrade noticeably; needs our own measurement |
| **Hinglish / code-switched ASR** | **YELLOW→RED for MVP** | Published research reports a **30–50 % relative WER increase** on code-switched speech vs monolingual, affecting Whisper specifically |
| Noisy environment | **YELLOW** | Needs push-to-talk + measurement, not assumption |

**The distinction that matters, and that the brief rightly demanded we not blur:**

- **Hinglish *input* (ASR)** — the hard, evidence-constrained problem. Dedicated fine-tunes exist (e.g. a Whisper-large-v3 Hinglish variant), but large-v3 is far too heavy for 7.7 GB and adds deadline risk. **MVP: not promised.**
- **Hinglish *output* (LLM explanation)** — a generation task, not a recognition task. A modern multilingual instruct model produces Hinglish explanations readily and this is verifiable in minutes. **MVP: promised, after a smoke test.**

This asymmetry is a genuine product insight, not a hedge: a student can **type or speak in English/Hindi and receive the explanation in Hinglish**, which is precisely the direction that matters pedagogically. Indian students overwhelmingly read technical material in English but *understand* explanation better in mixed register.

**MVP decision:** Whisper-base or -small for English + Hindi, push-to-talk. Hinglish **output** supported. Hinglish **ASR** listed as roadmap with the WER evidence cited.

---

## 6. LLM Feasibility — GREEN (with size discipline)

**Architecture decision — the load-bearing one for this project:**

Both GenieX (Snapdragon) and llama.cpp / LM Studio (x86_64) run **GGUF** behind an **OpenAI-compatible `/v1/chat/completions`** endpoint. CampusOS therefore speaks only OpenAI-compatible HTTP and selects its host with one environment variable:

    LLM_BASE_URL=http://localhost:8080/v1    # llama.cpp on Intel   (dev)
    LLM_BASE_URL=http://localhost:8080/v1    # GenieX on Snapdragon (target, NPU)

Identical application code. Identical model weights. The port of CampusOS to Snapdragon is a **runtime swap, not a code change** — which is exactly what "designed and intended to be optimized for Snapdragon" should mean in engineering terms rather than marketing terms.

**Model class:** ~1.5B–3B instruct, 4-bit quantized (Q4_K_M), ~1–2 GB resident. Fits 7.7 GB alongside Whisper and the vector store. Must be multilingual (Hindi/Hinglish output) and Apache-2.0/MIT licensed. Candidates and selection are in `MODEL_EVALUATION.md`.

**Risk:** a 1.5–3B model reasons more weakly than a frontier model. **Mitigation — and this is the core product argument:** strong RAG grounding plus tight prompt constraints substantially narrow the quality gap for *extractive, source-grounded explanation*, which is the only task we ask of it. We are not asking it to reason from scratch; we are asking it to explain retrieved text. That is a materially easier task and it is what makes a small local model viable.

---

## 7. RAG Feasibility — GREEN

Lowest-risk subsystem; all components are pure Python, CPU-cheap, and deadline-safe.

| Component | Choice | Rationale |
|---|---|---|
| Parsing | PyMuPDF | Fast, reliable digital-PDF text + layout |
| Chunking | Recursive, ~800 tok, ~120 overlap, page-aware | Page number retained for citation |
| Embeddings | Small multilingual sentence-transformer (ONNX) | Runs on ORT CPU now, QNN EP later — provider swap only |
| Vector store | **SQLite + NumPy brute force** | Corpus is one student's notes: hundreds-to-low-thousands of chunks. Brute-force cosine over a few thousand 384-d vectors is sub-millisecond. A dedicated vector DB is unjustified complexity at this scale. |
| Reranking | Not in MVP | Add only if retrieval evaluation shows it is needed |
| Citation | Mandatory page-level | Core to product identity |

**Hallucination mitigation:** retrieved context only, explicit "not found in your material" path, and answers that carry page citations the student can open and verify. *Groundedness is a feature surface, not just a safety measure* — being able to click a citation and land on the source page is the product's trust mechanism.

**Design note:** SQLite + NumPy is a deliberate simplification with a known ceiling — it is O(n) per query and will need an ANN index (`hnswlib` or `sqlite-vec`) if a corpus ever exceeds ~50k chunks. Recorded as a `ponytail:` comment in the code.

---

## 8. Multilingual Feasibility

| Capability | Verdict |
|---|---|
| English in / English out | **GREEN** |
| Hindi text in / Hindi out | **GREEN** (generation) |
| **Hinglish out** ("explain in Hinglish") | **GREEN** after smoke test — generation, not recognition |
| Hindi speech in | **YELLOW** — measure before promising |
| Hinglish speech in | **RED for MVP** — 30–50 % relative WER penalty documented |
| Bilingual side-by-side | **GREEN** — prompt-level, near-zero cost |

---

## 9. Document Ingestion Feasibility

| Format | Verdict | Notes |
|---|---|---|
| Digital PDF | **GREEN** | PyMuPDF |
| Lecture slides (PDF-exported) | **GREEN** | Same path |
| Scanned PDF / image | **YELLOW** | Needs OCR; adds a model + latency. AI Hub has OCR (TrOCR-class) but integration cost is real in 9 days |
| DOCX | **YELLOW** | `python-docx` is trivial; low priority |
| Handwritten notes | **RED** | Out of scope |

**MVP: digital PDF only.** OCR is the most expensive "nice to have" relative to its demo value, because most student material that matters (textbooks, slide exports, question papers) is already digital-text PDF.

---

## 10. Local / Offline Feasibility — GREEN

Every MVP component runs locally with zero network calls after setup. This is genuinely verifiable, and we will verify it rather than assert it: the benchmark harness includes an **airplane-mode test** plus an egress assertion that the process opens no outbound sockets during a full ingest→ask→quiz cycle. "Works offline" becomes a measured pass/fail, not a slogan.

---

## 11. Windows Deployment Feasibility

| Item | Dev (x64) | Target (ARM64) |
|---|---|---|
| Python | 3.10.2 ✅ | **3.11+ required** by `onnxruntime-qnn` ⚠️ |
| ORT CPU inference | ✅ | ✅ |
| **QNN EP inference** | ❌ **x64 = quantize/AOT only** | ✅ `backend_path: QnnHtp.dll` |
| llama.cpp GGUF | ✅ | ✅ |
| GenieX | ❌ | ✅ |
| Packaging | Local web app on `127.0.0.1` | Same |

**Prerequisite gap found:** local Python is **3.10.2**; `onnxruntime-qnn` requires **3.11–3.14**. Not blocking for the MVP (we use ORT CPU EP locally), but it blocks any QNN AOT-compilation work on this machine. Tracked in `PLAN.md`.

**Packaging decision:** a local web app served on `127.0.0.1`, opened in the browser. Rationale: a Python backend plus static frontend is ARM64-portable with zero native UI toolkit risk, whereas Electron/Tauri adds an ARM64 build matrix we cannot test and cannot afford to debug in 9 days.

---

## 12. Dependency & Licensing

| Dependency | License | Risk |
|---|---|---|
| PyMuPDF | AGPL-3.0 / commercial | ⚠️ **AGPL.** Fine for an open-source competition submission; flagged for future commercial use. `pypdfium2` (BSD) is the drop-in fallback. |
| ONNX Runtime | MIT | None |
| llama.cpp | MIT | None |
| GenieX | Stated open-source; **license not confirmed** | ⚠️ Verify before citing |
| FastAPI / Uvicorn / NumPy | MIT / BSD | None |
| Model weights | Must be Apache-2.0 or MIT | Gated in `MODEL_EVALUATION.md` |

**Action:** confirm GenieX's license and each chosen model's license before submission. Licensing is an explicit submission field.

---

## 13. Expected Hardware Requirements (product-facing)

- **Minimum:** Windows 11, x64 or ARM64, 8 GB RAM, ~6 GB disk. (CPU inference; this is our dev box — so the floor is measured, not guessed.)
- **Recommended:** Snapdragon X-series Copilot+ PC, 16 GB, NPU — GenieX NPU backend, ORT QNN EP for Whisper/embeddings.

---

## 14. Known Technical Risks

| ID | Risk | P | I | Mitigation |
|---|---|---|---|---|
| R-01 | 9-day deadline | **High** | **High** | Compressed Phase 0; vertical slice first; docs generated from the real build |
| R-02 | No Snapdragon hardware | Certain | Low | Rules permit "intended to be optimized for"; report path + harness, never fake numbers |
| R-03 | 7.7 GB RAM limits model size | Certain | Med | ≤3B @ 4-bit; RAG does the heavy lifting |
| R-04 | Hinglish ASR quality | High | Low | Not promised for MVP; Hinglish *output* delivered instead |
| R-05 | Small-model answer quality | Med | High | Strong grounding; extractive task; groundedness eval with pass/fail gate |
| R-06 | Prompt injection via PDF | Med | Med | Treat document text as data; delimit; never execute |
| R-07 | GenieX license unconfirmed | Low | Med | Verify before submission |
| R-08 | Python 3.10 vs QNN's 3.11+ | Certain | Low | Only blocks AOT work; documented as a target-side prerequisite |
| R-09 | Becomes a generic PDF chatbot | **Med** | **High** | Quiz + weak-topic loop is MUST-HAVE, not optional — it *is* the product |

---

## 15. Unknowns Requiring Physical Snapdragon Hardware

Honestly unresolvable without the device; labelled as such in the submission:

1. Actual NPU latency for Whisper and the LLM.
2. NPU vs CPU power draw over a study session.
3. GenieX install and model-load behaviour on Windows ARM64.
4. ORT QNN EP graph compatibility for our specific embedding model.
5. Real memory headroom under simultaneous ASR + LLM load.

---

## 16. Go / No-Go by Feature

| Feature | Verdict | MVP? |
|---|---|---|
| Digital PDF ingestion | 🟢 GREEN | ✅ |
| Chunking + embeddings + retrieval | 🟢 GREEN | ✅ |
| Grounded Q&A with page citations | 🟢 GREEN | ✅ |
| Local LLM (≤3B, GGUF, OpenAI-compatible) | 🟢 GREEN | ✅ |
| "Not in your material" refusal path | 🟢 GREEN | ✅ |
| Quiz generation from retrieved chunks | 🟢 GREEN | ✅ |
| Quiz evaluation + weak-topic detection | 🟢 GREEN | ✅ |
| Offline verification harness | 🟢 GREEN | ✅ |
| Snapdragon deployment path + benchmark harness | 🟢 GREEN | ✅ |
| English speech-to-text | 🟢 GREEN | ✅ |
| Hinglish/Hindi **output** | 🟢 GREEN | ✅ |
| Hindi **speech input** | 🟡 YELLOW | Stretch |
| Session history / progress | 🟡 YELLOW | Stretch |
| Scanned-PDF OCR | 🟡 YELLOW | ❌ |
| Hinglish **speech input** | 🔴 RED | ❌ |
| TTS | 🟡 YELLOW | ❌ |
| Adaptive learning | 🔴 RED | ❌ |
| Measured NPU benchmarks | 🔴 RED | ❌ (no hardware) |

---

## 17. Conclusion

**GO.** The product is feasible, the Snapdragon relevance is architectural rather than cosmetic, and the deadline is survivable — but only with the scope in `MVP_SCOPE.md`. The differentiator versus a generic PDF chatbot is the **closed study loop** (grounded explanation → quiz → weak-topic detection → targeted re-explanation), not any single primitive.

---

## Appendix — Source Log

### OFFICIAL / PRIMARY

- **Unstop public API**, opportunity `1748893` — `https://unstop.com/api/public/opportunity/search-result?opportunity=competitions&searchTerm=Snapdragon%20AI%20Lab` — accessed 2026-09-21. *Proves:* exact deadline, eligibility, individual participation, the "intended to be optimized for" clause, the four criteria and their tie-break ordering, prizes, IP terms. **Confidence: HIGH** (structured data from the host platform).
- **Competition page** — `https://unstop.com/competitions/crp-snapdragon-ai-lab-build-present-challenge-qualcomm-1748893` — accessed 2026-09-21. JS-rendered; content retrieved via the API above. **HIGH**
- **ONNX Runtime — QNN Execution Provider** — `https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html` — accessed 2026-09-21. *Proves:* win-arm64 is the inference target; x86_64 is quantization/AOT only; Python 3.11.x; `backend_path: QnnHtp.dll`. **HIGH**
- **onnxruntime-qnn repository** — `https://github.com/onnxruntime/onnxruntime-qnn` — accessed 2026-09-21. *Proves:* QNN EP ships as a standalone plugin (`onnxruntime-qnn>=2.0.0`) against stock ORT; platform/RID matrix. **HIGH**
- **Qualcomm AI Hub — GenieX** — `https://aihub.qualcomm.com/geniex` — accessed 2026-09-21. *Proves:* GGUF via llama.cpp plugin, NPU/GPU/CPU, Windows ARM64, **OpenAI-compatible APIs**, 300+ models. *This source underpins the core architecture decision.* **HIGH**
- **Qualcomm Genie (Windows on Snapdragon docs)** — `https://docs.qualcomm.com/doc/80-62010-1/topic/genie.html` — accessed 2026-09-21. **HIGH**
- **qualcomm/ai-hub-apps — `llm_on_genie`** — `https://github.com/qualcomm/ai-hub-apps/tree/main/tutorials/llm_on_genie` — accessed 2026-09-21. *Proves:* documented AI Hub → QAIRT context binary → Genie workflow incl. Windows. **HIGH**
- **qualcomm/Whisper-Tiny**, **qualcomm/Whisper-Small-Quantized** (Hugging Face) — accessed 2026-09-21. *Proves:* Snapdragon-targeted Whisper with QNN artifacts. **HIGH**
- **Qualcomm Developer Blog — Paris Edge AI Hackathon (SignBridge, EasyForm)** — `https://www.qualcomm.com/developer/blog/2025/10/qualcomm-edge-ai-paris-hackathon-signbridge-easyform` — accessed 2026-09-21. *Proves:* these two projects exist and are on-device. Body text not retrievable; title/summary only. **MEDIUM**
- **Qualcomm Developer Blog — Bengaluru Edge AI Hackathon** — `https://www.qualcomm.com/developer/blog/2025/11/qualcomm-edge-ai-developer-hackathon-2025-bengaluru` — accessed 2026-09-21. Body not retrievable. **LOW-MEDIUM**

### TECHNICAL / SECONDARY

- **"Adapting Whisper for Code-Switching through Encoding Refining and Language-Aware Decoding"** — `https://arxiv.org/html/2412.16507v2` — accessed 2026-09-21. *Proves:* code-switched speech carries a **30–50 % relative WER increase** for Whisper-class models. *Basis for the Hinglish-ASR YELLOW/RED rating.* **MEDIUM-HIGH**
- **Hindi-English Code-Switching Speech Corpus** — `https://arxiv.org/pdf/1810.00662` — accessed 2026-09-21. **MEDIUM**
- **Trelis/whisper-hinglish-preview** (Hugging Face) — accessed 2026-09-21. *Proves:* a Hinglish fine-tune exists, but on Whisper-large-v3 — too heavy for 7.7 GB. **MEDIUM**

### UNVERIFIED — recorded as gaps, deliberately not filled

- **Tutor AI**, **REDACT** — no official Qualcomm source located. Treated as unconfirmed.
- **GameSense**, **EdgeFit Coach** — consistent with Bengaluru coverage, but names/models/runtimes unconfirmed.
- AI Hub's Whisper-Small-Quantized "3.78 ms" — a per-component figure. **Must not be cited as end-to-end latency.**
