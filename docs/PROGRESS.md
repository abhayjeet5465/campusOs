# CampusOS AI — Build Progress

**Built:** 2026-09-29 · single session, Intel x64 dev box, no Snapdragon hardware.

Status is what was *verified*, not what was written. A module that exists but was never run
against the real stack is not counted as done.

---

## MVP requirements

| # | Feature | Status | Verified by |
|---|---|---|---|
| M1 | Digital PDF ingest + page-aware chunking | ✅ | `tests/test_pipeline.py`, `python -m backend.ingest` |
| M2 | Local embeddings + retrieval | ✅ | real e5-small ONNX, 10.1 ms retrieval |
| M3 | Local LLM via OpenAI-compatible endpoint | ✅ | llama.cpp server, live |
| M4 | Grounded answer with page citations | ✅ | citations validated to the correct page |
| M5 | "Not in your material" refusal | ✅ | probe refused, no model call made |
| M6 | Quiz generation from retrieved chunks | ✅ | valid MCQs, source chunk attached |
| M7 | Quiz evaluation + weak-topic detection | ✅ | score → named topic → page link |
| M8 | English speech-to-text, push-to-talk | ✅ | `tests/test_asr.py`, 4/4 content words |
| M9 | Hinglish / Hindi explanation output | ✅ | required a model change — see ADR-10 |
| M10 | Student UI (upload → ask → quiz) | ✅ | served, wired, `tests/test_frontend.py` |
| M11 | Offline verification | ✅ | `tests/test_egress.py`, 0 outbound sockets |
| M12 | Snapdragon path + benchmark harness | ✅ | `setup_snapdragon.md`, `benchmarks/run.py` |

## Should-have

| # | Feature | Status |
|---|---|---|
| S1 | Hindi speech input | ❌ not attempted — WER unmeasured, so not promised |
| S2 | Session/quiz history | ◐ persisted in SQLite (`attempts`), no UI |
| S3 | Answer-depth control | ✅ simpler / exam-ready, wired to the UI |
| S4 | Multi-doc study set with per-source filtering | ✅ source selector filters retrieval |

## Not done

C1 TTS · C2 flashcard export · C3 OCR · C4 DOCX ingest · C5 analytics dashboard — all out of
scope per `MVP_SCOPE.md`, none started.

---

## Measured (this machine, CPU only)

| Metric | Value |
|---|---|
| Ingest throughput | 11.9 pages/s |
| Query embedding | 6.5 ms |
| Retrieval | 10.1 ms |
| Backend RSS | 756 MB (+ ~2 GB llama-server) |
| Embedding EP | `CPUExecutionProvider` |

Full table with environment: `benchmarks/RESULTS.md`. Snapdragon column empty by design.

---

## What went wrong, and what it cost

**Qwen2.5-1.5B could not do Hindi or Hinglish.** The model selected in planning was rejected
after measurement — it rendered *conductor* as इमारत (*building*). Four prompt strategies were
tried before concluding the cause was model capacity. Replaced with Llama-3.2-3B, at the cost of
a non-Apache licence. Recorded in ADR-10 with the failing output kept.

**Citations were silently absent at first.** The model answered correctly and cited nothing.
Fixed with a worked example plus an end-of-prompt reminder; a 1.5B model weights the end of the
prompt most heavily.

**Hindi translated the citation markers themselves** into Devanagari, so validation dropped them
and correct answers came back uncited. Fixed by masking markers to opaque tokens before the
translation pass and restoring them after — a marker with no translatable content cannot be
translated.

> Each of these was caught by running the thing, not by reading the code. The day-1 vertical
> slice strategy in `PLAN.md` is what surfaced them early enough to fix.

---

## Outstanding — needs the user, not the code

1. **Real course PDFs in `eval/pdfs/`.** The relevance gate (0.78) is tuned on synthetic text
   with a thin margin (0.866 in-corpus vs 0.731 out-of-corpus). The groundedness ≥ 90 % and
   refusal = 100 % gates in `PLAN.md` Phase 7 are **unmeasured** until real material exists.
2. **Unstop registration** (R-012) — unrecoverable if missed.
3. **Demo video** — script ready in `docs/DEMO.md`.
4. **Git repo** — not initialised. `benchmarks/run.py` records the commit hash and currently
   writes "not a git repo".
