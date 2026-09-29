# CampusOS AI — Architecture Decisions

Recorded as built, not as planned. Each entry states what was decided, what it cost, and
what would reverse it.

---

## ADR-01 — The LLM runs out-of-process behind an OpenAI-compatible endpoint

**Decision.** `backend/llm.py` speaks HTTP to `/v1/chat/completions`. It never loads a model.

**Why.** The LLM is simultaneously the largest memory consumer and the most platform-specific
component. Putting it in-process would couple the app's lifetime to the model's and make the
Snapdragon swap an engineering task instead of an environment variable.

**Cost.** Two terminals to start, and a failure mode ("backend unreachable") that does not exist
in a single-process design. Mitigated by `/api/health` and an error message that contains the
exact command to fix it.

**Reversed if.** A single-process ARM64 runtime with better performance appears and the
two-terminal start becomes the dominant usability complaint.

---

## ADR-02 — Brute-force cosine, no vector index

**Decision.** One matrix multiply over all vectors in `backend/retrieve.py`.

**Why.** Measured at 20.7 ms mean including query embedding. An ANN index would add a
dependency, an index-rebuild path on delete, and a tuning surface, to optimise something
that is not the bottleneck — the LLM is.

**Cost.** Linear in corpus size. Marked in code as `ponytail:` with the upgrade threshold.

**Reversed if.** A corpus exceeds roughly 50k chunks. Add `hnswlib` then, not before.

---

## ADR-03 — Citations are validated against the chunks actually supplied

**Decision.** `answer.validate_citations()` drops any `[doc, p.N]` that does not match a chunk
the model was given in this turn.

**Why.** This is the difference between a citation and a decoration. A small model will
occasionally cite a page it finds plausible, and a student cannot tell the difference — they
are precisely the population least able to catch it. Prompting alone does not prevent this;
post-hoc validation does.

**Cost.** A correct citation formatted unusually gets dropped, so the answer loses a reference
it deserved. Silently dropping a real citation is a far cheaper failure than displaying a fake one.

---

## ADR-04 — The relevance gate refuses before the LLM is called

**Decision.** If the top cosine score is below `CAMPUSOS_GATE` (default 0.78), `answer.ask()`
returns the refusal without invoking the model.

**Why.** Two reasons, both load-bearing. It makes the refusal path independent of model
behaviour — the model cannot talk itself past the gate. And it makes refusal instant and free,
which means it stays correct even when the LLM is down.

**Cost.** The threshold is a single global number tuned on a small set. Set too high it refuses
answerable questions.

**Measured.** On the synthetic check: in-corpus 0.866, out-of-corpus 0.731. The margin is real
but not large — **this threshold must be re-tuned against `eval/eval_set.json` on real PDFs
before the submission.** Treating the current value as validated would be overclaiming.

---

## ADR-05 — Quiz questions carry their source chunk id from generation

**Decision.** Each generated question stores `chunk_id` and `source`.

**Why.** It makes the per-question explanation grounded by construction rather than by a second
retrieval round that might land somewhere else, and it makes the weak topic traceable to a page.
It costs nothing at generation time and cannot be retrofitted reliably afterwards.

**Cost.** None observed.

---

## ADR-06 — Vanilla frontend, no build step

**Decision.** Three static files.

**Why.** A bundler adds a Node dependency and an ARM64 toolchain story for zero user-visible
benefit in a single-screen app, and removes an entire class of deployment failure on the
target machine.

**Cost.** Manual DOM work; no component reuse. Acceptable at this size.

---

## ADR-07 — faster-whisper on CPU, disclosed as having no NPU path

**Decision.** Ship CTranslate2 ASR for the MVP; document the ORT+QNN AI Hub path as unimplemented.

**Why.** ONNX Whisper integration was the single largest schedule risk (`PLAN.md` R-003), and
the honest version of the NPU claim costs nothing while a fabricated one would invalidate the
submission.

**Cost.** Forfeits the NPU argument for the ASR workload specifically. `/api/health` names the
active backend so the running system never implies otherwise.

**Reversed if.** Hardware becomes available, or the ORT QNN Whisper path is implemented and
measured — in that order.

---

## ADR-08 — Hard delete compacts the vector array and reindexes rows

**Decision.** `store.delete_document()` rebuilds `vectors.npy` and remaps every `vec_row`.

**Why.** Tombstoning would be less code, but it leaves the student's deleted material on disk
while the UI says it is gone. For a product whose central promise is privacy, that gap is the
wrong place to be lazy.

**Cost.** O(n) rewrite per delete. Irrelevant at this scale, and asserted in `tests/test_pipeline.py`.

---

## ADR-09 — Multilingual output is a second pass, not a combined instruction

**Decision.** `answer.ask()` always generates the grounded, cited answer in English, then calls
`answer.relanguage()` to re-explain it in Hindi or Hinglish. Citation validation runs on the
**final** text, after re-explanation.

**Why.** Measured, not assumed. Asking a small model to ground, cite, and switch language in one
pass loses the language instruction: the "use only these blocks, copy exactly" framing dominates
and the answer returns in the source language. Three placements were tried — language first,
language last, language in the system prompt — and all three produced English.

Splitting the passes also means groundedness never competes with style. If the second pass fails
or the model is down, the fallback is the English answer *with its citations intact*, which is a
degraded answer rather than a wrong one.

**Cost.** One extra LLM call for non-English answers, roughly doubling their latency. Accepted:
correctness of the citation is worth more than latency on a path the student opts into.

**Validation placement.** Running validation after the re-explanation means a citation the model
mangles while translating is dropped exactly like an invented one. The guarantee cannot silently
weaken when the student switches language — which is precisely when they are least able to check.

---

## ADR-10 — Model tier changed from Qwen2.5-1.5B to Llama-3.2-3B for Indic quality

**Decision.** The 1.5B model was replaced after measuring its Hindi and Hinglish output.

**Why.** `MODEL_EVALUATION.md` selected Qwen2.5-1.5B partly on the expectation of strong Indic
generation. Measured on the actual pipeline, that expectation did not hold at the 1.5B tier:

| Language | Observed output |
|---|---|
| Hindi | Fluent Devanagari, wrong meaning — "conductor" rendered as इमारत (*building*) |
| Hinglish | Correct register, but the physics was corrupted and the citation marker was dropped |

English answers, citations, refusal, and quiz generation were all **fine** at 1.5B. The failure is
specific to cross-lingual re-explanation, which is exactly the MUST-have M9.

**Licence trade.** Llama-3.2-3B ships under the Llama Community Licence, not Apache-2.0. This is a
real downgrade in licence cleanliness from the original selection and is recorded here rather than
glossed: the alternative with better Hindi, Qwen2.5-3B, carries the Qwen **Research** Licence
(non-commercial), which is a harder blocker for a competition submission.

**Cost.** ~2 GB resident instead of ~1.1 GB, and slower generation. Re-measured in
`benchmarks/RESULTS.md` rather than estimated.

**Reversed if.** An Apache or MIT model at the 3B tier demonstrates comparable Hinglish quality.

> The 1.5B result is kept in this record deliberately. It is the measurement that justifies the
> licence trade, and deleting it would make the final choice look arbitrary.

---

## ADR-11 — Answers stream; the model is warmed at startup

**Decision.** `/api/ask/stream` sends server-sent events, and the backend fires a one-token
request at startup to prefill the model.

**Why.** Measured on this machine, Llama-3.2-3B:

| | Qwen 1.5B | Llama 3B |
|---|---|---|
| Cold time-to-first-token | 2.1 s | **10.9 s** |
| Warm time-to-first-token | 0.3 s | **0.7 s** |
| Median total response | 7.1 s | 13.3 s |
| Generation rate | 10.8 words/s | 3.7 words/s |

Two separate problems hide inside "the 3B model is slow", and they need different fixes.

**Cold prefill (10.9 s).** Paid once, by whoever asks first — which in a demo is the moment the
product is judged. llama.cpp caches the prompt prefix, so the second question costs 0.7 s. The
fix is to make sure the first *real* question is never the cold one. A background warm-up call
at startup costs nothing and moves that 10.9 s into the launch window.

**Generation rate (3.7 words/s).** Cannot be fixed by scheduling; it is what a 3B model does on
4 CPU cores. But 3.7 words/s is near adult reading speed, so streaming makes it watchable
rather than something to wait out. Waiting 13 s for a block of text and reading text as it
arrives at reading speed are very different experiences of the same 13 seconds.

**What streaming does not change.** Citations are validated on the completed text, exactly as in
`ask()`, and citation chips render only from the final validated payload. Streamed tokens are
inserted with `textContent`, never as HTML. The student never sees a clickable citation that has
not been checked against the chunks the model was given.

Non-English answers do not stream token-by-token: the re-explanation pass needs the finished
English text (ADR-09), so the UI shows "Answering, then re-explaining…" and delivers one block.
Overstating this as "streaming" for all languages would be a lie the user would catch in a second.

**Cost.** A second endpoint, and SSE frame parsing in the frontend. `/api/ask` is kept because
the tests and the eval harness want one call with one result.

> **Caveat on these numbers:** they were taken with the machine at 96 % memory use, with an IDE
> and a browser running. They are therefore pessimistic, and honest about the conditions rather
> than measured on an artificially idle box.
