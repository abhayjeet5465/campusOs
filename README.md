# CampusOS AI

**A private, offline study assistant.** Turns a student's own course PDFs into a voice-driven
learning loop: ask by voice → get a cited explanation in your language → get quizzed on it →
find out what you actually don't know.

Built for the Snapdragon AI Lab Build & Present Challenge.

---

## What makes it not a "chat with PDF" tool

1. **It refuses.** If your material doesn't cover something, it says so and shows you what it
   *did* find nearby. It does not fill the gap with plausible text.
2. **Every citation is verified.** A page reference the model invented for a chunk it was
   never shown gets dropped before you see it. Citations are clickable and open the source text.
3. **The loop ends in a quiz, not an answer.** Each question carries the chunk it came from, so
   the explanation is grounded by construction and the weak topic it names is real.
4. **Hinglish output.** Material is in English; understanding often isn't. One click re-explains
   in the register students actually think in, citations intact.
5. **Offline is the normal case.** Proven by a test that blocks every non-loopback socket and
   runs the full pipeline anyway.

---

## Quick start

```powershell
pip install -r requirements.txt
python scripts\fetch_models.py          # one time, ~2.6 GB, needs internet

# Terminal 1 — the LLM server
powershell -File scripts\start_llm.ps1

# Terminal 2 — the app
python -m backend                       # opens http://127.0.0.1:8000
```

Then: drop in a PDF → hold the mic button and ask → click a citation → press **Quiz me**.

## Verify the claims yourself

```powershell
python tests\test_pipeline.py    # ingest, retrieval, the refusal gate, hard delete
python tests\test_egress.py      # blocks all non-loopback sockets, runs the pipeline anyway
python benchmarks\run.py         # writes benchmarks/RESULTS.md from this machine
python eval\run_eval.py          # groundedness + refusal, needs your PDFs in eval/pdfs/
```

Each module also self-checks: `python -m backend.ingest`, `-m backend.retrieve`,
`-m backend.answer`, `-m backend.quiz`.

## Requirements

- Windows 11, 8 GB RAM, ~6 GB free disk
- Python 3.10+ on x86_64 · **3.11+ on ARM64** (QNN wheel requirement)
- No accounts, no API keys, no cloud services — by design

## Models

| Role | Model | Licence |
|---|---|---|
| LLM | Llama-3.2-3B-Instruct (GGUF Q4_K_M) | Llama Community Licence |
| Embeddings | multilingual-e5-small (ONNX, 384-d) | MIT |
| ASR | faster-whisper base (CPU) | MIT |

Multilingual embeddings are a hard requirement, not a preference: a student's question may be
in Hindi while their PDF is in English, and an English-only encoder cannot solve that at all.

The LLM started as Qwen2.5-1.5B (Apache-2.0) and was changed after its Hindi output was measured
and found unusable — it rendered "conductor" as इमारत (*building*). The licence trade and the
measurement that forced it are recorded in [ADR-10](docs/DECISIONS.md).

## On Snapdragon and the NPU

**No NPU execution has been measured. This machine has no NPU.**

The code selects `QNNExecutionProvider` first with CPU fallback in the same list on ARM64
Windows, the LLM is out-of-process behind an OpenAI-compatible endpoint so GenieX is a config
swap, and the benchmark harness runs unmodified on both hosts. The Snapdragon column in
`benchmarks/RESULTS.md` is deliberately empty and labelled *requires hardware*.

Full path, with its caveats: [`scripts/setup_snapdragon.md`](scripts/setup_snapdragon.md).

## Privacy

Documents, vectors, and quiz history live in `%LOCALAPPDATA%\CampusOS\`. No telemetry, no
analytics, no crash reporting. Audio is transcribed and discarded, never written to disk.
Delete removes the SQLite rows *and* compacts the vector array — `tests/test_pipeline.py`
asserts it.

## Layout

```
backend/     config · store · ingest · embed · retrieve · answer · quiz · asr · app
frontend/    one page, no build step
benchmarks/  harness + RESULTS.md
eval/        groundedness + refusal harness
tests/       pipeline + no-egress assertion
scripts/     model fetch · LLM launcher · setup_snapdragon.md
docs/        PRD · TRD · plan · feasibility · model evaluation
```

## Attribution

Built with Llama. Llama 3.2 is licensed under the Llama 3.2 Community License,
Copyright © Meta Platforms, Inc. All Rights Reserved.

Model weights are downloaded from their original publishers at first run and are not
redistributed here. Full third-party licence notices: [`LICENSE`](LICENSE).
