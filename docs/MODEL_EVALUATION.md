# CampusOS AI — Model Evaluation Matrix

**Date:** 2026-09-21
**Selection constraints:** ≤7.7 GB RAM dev box (no NPU) · must have a documented Snapdragon path · permissive licence · integrable within 9 days.

**Status legend** — `VERIFIED` = confirmed against an official source this session · `TO-VERIFY` = plausible and widely used, but licence/size/availability must be confirmed before it is cited in the submission · `REJECTED` = ruled out with a reason.

> **Licensing is a submission field.** No model ships in the final build until its licence has been read, not assumed. Several popular small models carry non-Apache licences with real restrictions, so this is treated as a gate rather than a formality.

---

## 1. Speech-to-Text

| Model | Source | Params | Runtime | Snapdragon target | NPU | Licence | Memory | Status |
|---|---|---|---|---|---|---|---|---|
| **Whisper-Tiny** | Qualcomm AI Hub / HF `qualcomm/Whisper-Tiny` | 39 M | ONNX Runtime, QAIRT ctx binary | Snapdragon X Elite | ✅ QNN HTP | MIT (OpenAI weights) | ~150 MB | **VERIFIED** |
| **Whisper-Small-Quantized** | HF `qualcomm/Whisper-Small-Quantized` | 244 M | ONNX Runtime + QAIRT v2.4x | Snapdragon X Elite | ✅ QNN HTP | MIT | ~500 MB (quant) | **VERIFIED** |
| Whisper-Base | OpenAI / `faster-whisper` CTranslate2 | 74 M | CTranslate2 CPU | — | ❌ | MIT | ~290 MB | TO-VERIFY |
| whisper-hinglish-preview | HF `Trelis/...` | 1.55 B (large-v3) | PyTorch | — | ❌ | check | ~3 GB+ | **REJECTED** — exceeds RAM budget alongside the LLM; adds unacceptable deadline risk |

**PRIMARY: `Whisper-Small-Quantized` (Qualcomm AI Hub).**
Reasoning, objective: it is the *only* candidate that is simultaneously (a) published by Qualcomm with a Snapdragon X Elite target, (b) supplied as a QNN context binary so NPU execution needs no conversion work from us, and (c) small enough to co-reside with a 3B LLM in 7.7 GB. Criteria (a) and (b) directly serve Technical Implementation; no other candidate satisfies both.

**SECONDARY: `Whisper-Tiny` (Qualcomm AI Hub)** — same pipeline, same provenance, ~3× smaller. The fallback if memory pressure appears during simultaneous ASR + LLM load, at a measurable accuracy cost.

**FALLBACK: `faster-whisper` base on CPU** — used only if ONNX Whisper integration stalls. Chosen because CTranslate2 is fast on CPU and the API is trivial, but it is a *dev-only* fallback: it has **no Snapdragon NPU path**, so shipping it would forfeit the NPU argument.

**Hindi/Hinglish note:** Whisper is multilingual, but per `FEASIBILITY.md` §5, code-switched speech carries a documented **30–50 % relative WER increase**. Hindi input is measured before it is promised; Hinglish input is **not** promised for the MVP.

---

## 2. Text Generation (LLM)

| Model | Params | Quant | Resident | Format | Snapdragon path | Multilingual (HI) | Licence | Status |
|---|---|---|---|---|---|---|---|---|
| **Qwen2.5-1.5B-Instruct** | 1.5 B | Q4_K_M | ~1.1 GB | GGUF | GenieX (GGUF) | strong | **Apache-2.0** | **TO-VERIFY** (licence confirmed as Apache for 1.5B; re-read before ship) |
| Qwen2.5-3B-Instruct | 3 B | Q4_K_M | ~2.0 GB | GGUF | GenieX (GGUF) | strong | ⚠️ **Qwen Research Licence** on the 3B tier — *not* Apache | **TO-VERIFY — licence is the blocker** |
| Phi-3.5-mini-instruct | 3.8 B | Q4_K_M | ~2.4 GB | GGUF | GenieX (GGUF) | moderate | MIT | TO-VERIFY |
| Llama-3.2-3B-Instruct | 3 B | Q4_K_M | ~2.0 GB | GGUF | Genie (AI Hub binaries exist) | moderate | ⚠️ Llama Community Licence | TO-VERIFY |
| Gemma-4-E2B-it | ~2 B | — | — | GenieX featured | ✅ featured on AI Hub | good | ⚠️ Gemma Terms of Use | TO-VERIFY |
| Qwen3.5-2B | ~2 B | — | — | GenieX featured | ✅ **featured on AI Hub** | strong | TO-VERIFY | TO-VERIFY |
| Llama-v3-8B-Instruct | 8 B | Q4 | ~4.8 GB | Genie | ✅ documented | moderate | Llama Community | **REJECTED** — will not run reliably in 7.7 GB alongside Whisper |

**PRIMARY: Qwen2.5-1.5B-Instruct (GGUF Q4_K_M).**
Objective reasoning, in order of the constraints that actually bind:
1. **Fits.** ~1.1 GB resident leaves headroom for Whisper (~500 MB) + embeddings + OS on a 7.7 GB machine. The 3B candidates leave almost none.
2. **Licence is clean.** Apache-2.0 at the 1.5B tier, unlike the 3B tier of the same family, the Llama tiers, or Gemma.
3. **Hindi/Hinglish generation.** Qwen2.5 is trained on substantially more Indic and multilingual data than Phi-3.5, which directly serves M9.
4. **Runs unchanged on both hosts.** GGUF → llama.cpp here, GGUF → GenieX on Snapdragon. Zero porting work.

**SECONDARY: Qwen3.5-2B via GenieX**, *conditional on licence verification*. It is **featured on Qualcomm AI Hub**, which is the single strongest possible evidence for the "uses AI Hub models" requirement. If its licence is permissive and it loads in our RAM budget, it displaces the primary on competition-alignment grounds. **This check is the first task of Phase 1.**

**FALLBACK: Phi-3.5-mini-instruct (MIT).** Chosen strictly for licence certainty — MIT is unambiguous. Accepted cost: weaker Hindi/Hinglish, so selecting it would force M9 to degrade to Hindi-only or English-only.

**Explicitly not ranked as "best."** Each selection above is decided by a binding constraint (memory ceiling, licence class, Indic coverage, runtime portability), not by general quality impressions.

---

## 3. Embeddings

| Model | Params | Dim | Runtime | Snapdragon path | Multilingual | Licence | Status |
|---|---|---|---|---|---|---|---|
| **multilingual-e5-small** | 118 M | 384 | ONNX / ORT | ORT QNN EP (provider swap) | ✅ 100+ langs incl. Hindi | MIT | **TO-VERIFY** |
| paraphrase-multilingual-MiniLM-L12-v2 | 118 M | 384 | ONNX / ORT | ORT QNN EP | ✅ 50+ langs | Apache-2.0 | TO-VERIFY |
| all-MiniLM-L6-v2 | 22 M | 384 | ONNX / ORT | ORT QNN EP | ❌ English only | Apache-2.0 | TO-VERIFY |
| BGE-M3 | 568 M | 1024 | ONNX | heavy | ✅ excellent | MIT | **REJECTED** — 5× the size for retrieval quality we do not need at this corpus scale |

**PRIMARY: `multilingual-e5-small`.** Reasoning: retrieval must work when a student's *question* is Hindi/Hinglish but their *PDF* is English — a cross-lingual retrieval problem that an English-only encoder cannot solve at all. That makes multilingual capability a hard requirement, not a preference. At 384 dimensions it also keeps the brute-force NumPy search trivially fast.

**SECONDARY: `paraphrase-multilingual-MiniLM-L12-v2`** — same size class, Apache-2.0, fewer languages; a straight swap if e5 conversion misbehaves.

**FALLBACK: `all-MiniLM-L6-v2`** — English-only. Would silently break cross-lingual retrieval, so it is a last resort and its adoption must be disclosed as a capability regression.

---

## 4. OCR / Document Understanding

**Not in the MVP.** PyMuPDF handles digital-text PDFs, which covers the target material (textbooks, slide exports, question papers). AI Hub publishes TrOCR-class models with Snapdragon targets, recorded as the roadmap path. Integrating OCR costs more of the 9-day window than its demo value justifies.

## 5. Translation

**No dedicated model.** The instruct LLM performs Hindi/Hinglish explanation directly — a separate translation model would add a process, memory, and failure mode for a capability we already get free. Revisit only if generated Hinglish quality fails the `EVALUATION` gate.

## 6. TTS

**Not in the MVP.** No candidate selected. Roadmap item C1.

---

## Total MVP memory budget (projected, to be measured in Phase 1)

| Component | Resident |
|---|---|
| Qwen2.5-1.5B-Instruct Q4_K_M | ~1.1 GB |
| Whisper-Small-Quantized | ~0.5 GB |
| multilingual-e5-small | ~0.15 GB |
| Python + FastAPI + SQLite + vectors | ~0.4 GB |
| **Total** | **~2.2 GB** |
| Available after Windows (~3.5 GB of 7.7 GB) | ~4.2 GB |
| **Headroom** | **~2.0 GB** ✅ |

Projected, not measured. **Phase 1 task B1 replaces every number in this table with a measured one.**

---

## Verification checklist before submission

- [ ] Read and record the exact licence of the selected LLM (do not assume from the family)
- [ ] Confirm Qwen3.5-2B availability, licence, and RAM footprint via GenieX
- [ ] Confirm GenieX's own licence
- [ ] Confirm Whisper AI Hub artefact licence and download size
- [ ] Record every model's exact revision/commit hash for reproducibility
- [ ] Replace all projected memory figures with measured ones

---

## Addendum — measured results, 2026-09-29

The tables above were written before any model was run. This section records what the selected
models actually did on the built pipeline. Where a measurement contradicts the earlier
expectation, the measurement wins and the expectation is left visible rather than edited away.

### LLM: Qwen2.5-1.5B-Instruct — **REJECTED after measurement**

Selected as PRIMARY on four criteria. Three held; one did not.

| Criterion | Expected | Measured |
|---|---|---|
| Fits in 7.7 GB | ~1.1 GB resident | ✅ confirmed |
| Apache-2.0 licence | clean | ✅ confirmed |
| English grounding + citation | good | ✅ correct answers, citations validated to the right page |
| Quiz generation | adequate | ✅ valid MCQs with usable distractors |
| **Hindi / Hinglish generation** | **"strong"** | ❌ **unusable** |

The Hindi failure, concretely: asked to re-explain Ohm's law, it produced fluent Devanagari that
translated *conductor* as **इमारत** (*building*) and *resistance* as *the building's land*. The
Hinglish attempt used the correct register but corrupted the physics and dropped the citation
marker.

This was tested with the language instruction placed first, placed last, placed in the system
prompt, and as a separate second-pass call. All four produced either English or wrong Hindi, so
the cause is model capacity, not prompt construction.

**The earlier "strong multilingual" rating came from the Qwen2.5 family's general reputation, not
from testing the 1.5B tier specifically.** That is the error worth recording: family-level
capability claims do not transfer down to the smallest tier, and this project's MUST-have M9
depended entirely on the tier.

### LLM: Llama-3.2-3B-Instruct — **PROMOTED to PRIMARY**

Chosen for Indic generation quality at a size that still fits the memory budget (~2 GB Q4_K_M).

**Licence cost, stated plainly:** Llama Community Licence, not Apache-2.0. This is a genuine
regression against the original selection criteria. It was accepted because the alternative with
the best Hindi — Qwen2.5-3B — ships under the Qwen **Research** Licence (non-commercial), which is
a harder blocker for a competition submission than the Llama terms.

Attribution required by the licence is carried in `README.md` and `LICENSE`.

### Embeddings: multilingual-e5-small — **CONFIRMED**

Downloaded, converted, and running under ORT. Query embedding 6.5 ms, retrieval 10.1 ms.
The `query:` / `passage:` prefix requirement is implemented; omitting it measurably degrades
retrieval, so it is applied in `backend/embed.py` rather than left to call sites.

### ASR: faster-whisper base — **CONFIRMED as the dev fallback, with its caveat**

Tested end to end with synthesized speech: *"What is Ohms law and how does resistance work"* →
*"What is Om's law and how does resistance work?"* — 4/4 content words, and semantic retrieval
absorbs the "Ohms"/"Om's" difference.

**This is the FALLBACK from §1, not the PRIMARY.** It has no Snapdragon NPU path. The Qualcomm AI
Hub Whisper path remains documented and unimplemented. `/api/health` names the active backend so
the running system never implies otherwise.

Synthetic speech is also far cleaner than a student in a hostel at 1 am — this result proves the
pipeline is wired, **not** that WER is acceptable. Real WER needs recorded human samples.
