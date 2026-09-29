# CampusOS AI — MVP Scope Control

**Date:** 2026-09-21 · **Deadline:** 2026-09-30 23:59 IST · **Build window: 9 days, solo**

Scope here is set by one rule: **Technical Implementation is the top-ranked criterion**, and a feature that is not demonstrable in the video does not score. Everything below is judged against "can one person build, test, and demo this in the remaining days?"

---

## The one-sentence product

> CampusOS AI turns a student's own PDFs into a private, offline study loop: **ask by voice → get a cited explanation in your language → get quizzed on it → find out what you actually don't know.**

If a feature does not serve that sentence, it is not in the MVP.

---

## MUST HAVE — the submission fails without these

| # | Feature | Why it is essential | Demo-visible? |
|---|---|---|---|
| M1 | Digital PDF ingest + page-aware chunking | No material, no product | ✅ |
| M2 | Local embeddings + retrieval (SQLite + NumPy) | The grounding substrate | indirectly |
| M3 | Local LLM via OpenAI-compatible endpoint | The Snapdragon story lives here | ✅ |
| M4 | **Grounded answer with page citations** | The trust mechanism; separates us from a chatbot | ✅ |
| M5 | **"Not in your material" refusal path** | Proves grounding is real, not decorative | ✅ |
| M6 | **Quiz generation from retrieved chunks** | Turns Q&A into a *learning loop* | ✅ |
| M7 | **Quiz evaluation + weak-topic detection** | The payoff; the anti-"PDF chatbot" feature | ✅ |
| M8 | English speech-to-text (push-to-talk, local Whisper) | "Voice-first" must be real | ✅ |
| M9 | **Hinglish / Hindi explanation output** | The multilingual claim, on the side that is actually feasible | ✅ |
| M10 | Student UI (single page, upload → ask → quiz) | The demo surface | ✅ |
| M11 | **Offline verification** (airplane-mode + no-egress assertion) | Converts "local-first" into a measured fact | ✅ |
| M12 | **Snapdragon deployment path + benchmark harness** | The competition-alignment artifact | ✅ (doc + harness) |

M4–M7 together are the product. M1–M3 are plumbing. **If time runs short, cut elsewhere — never here.**

---

## SHOULD HAVE — build if the MUST list closes early

| # | Feature | Cut cost if dropped |
|---|---|---|
| S1 | Hindi **speech input** (measure WER first, promise after) | Low — Hinglish output already carries the multilingual claim |
| S2 | Session history / progress across quizzes | Medium — strengthens "learning loop" narrative |
| S3 | Answer-depth control ("explain simpler" / "exam-ready") | Low — pure prompt work, high demo value per minute |
| S4 | Multi-document study set with per-source filtering | Low |

**S3 is the best value-per-hour item on this list** — it is prompt engineering, costs almost nothing, and visibly differentiates the product in the demo.

---

## COULD HAVE — only if everything else is done and tested

| # | Feature |
|---|---|
| C1 | TTS answer readback |
| C2 | Flashcard export from weak topics |
| C3 | Scanned-PDF OCR |
| C4 | DOCX ingest |
| C5 | Study analytics dashboard |

---

## NOT NOW — explicitly out of scope

Teacher/tutor mode · adaptive learning models · social or collaborative features · full LMS · institution management · cloud multi-tenancy · accounts and login · autonomous agents · unrestricted computer control · mobile app · handwritten-note recognition · **any measured NPU benchmark figure** (no hardware — see `FEASIBILITY.md` §15).

---

## Changes from the initial candidate list, with reasons

The brief's starting list was written before the deadline and hardware were known. Four changes:

| Change | From → To | Reason |
|---|---|---|
| **Quiz workflow promoted** | "basic quiz" → **M6/M7 core** | It is the only thing separating CampusOS from a PDF chatbot. Demoting it would realise risk R-09. |
| **Speech-to-text promoted** | SHOULD → **MUST (English)** | "Voice-first" is in the product definition. A voice-first product that cannot demo voice is mis-sold. Scoped to English to keep it safe. |
| **Hindi/Hinglish split** | SHOULD (undifferentiated) → **MUST (output) / SHOULD (input)** | Evidence-driven: generation is feasible, code-switched ASR carries a documented 30–50 % relative WER penalty. |
| **"Snapdragon deployment experiment" redefined** | implied hardware test → **path + harness + doc** | No hardware exists. The rules permit "intended to be optimized for". We ship a real harness, not invented numbers. |

---

## Definition of Done for the MVP

A single uninterrupted run, on the Intel dev machine, with **Wi-Fi physically off**:

1. Upload a real course PDF → ingest completes, chunk count reported.
2. Hold-to-talk, ask a question aloud in English → transcript appears.
3. Grounded answer returns **with page citations that open to the correct page**.
4. Ask something genuinely absent from the PDF → system says it is not in the material, and **does not invent an answer**.
5. Toggle to Hinglish → the same answer, re-explained, still cited.
6. Generate a quiz → answer it → receive a score plus a **named weak topic**.
7. Click the weak topic → jump back to the grounded explanation for it.
8. `benchmarks/` produces a real latency and memory table from this run.

That run *is* the demo video. Build toward it directly.
