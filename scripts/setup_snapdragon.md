# Running CampusOS AI on Snapdragon X (ARM64 Windows 11)

**Status of this document: a deployment path, not a test report.** No step below has been
executed on Snapdragon hardware by this project. Every claim carries a source. Where we
have not measured something, this document says so rather than estimating.

The application code requires **no changes**. Both host-specific pieces are reached through
an interface that already has an ARM64 implementation:

| Workload | Interface | x86_64 (dev) | ARM64 (target) |
|---|---|---|---|
| LLM | OpenAI-compatible HTTP `/v1` | llama.cpp server (CPU) | GenieX / llama.cpp ARM64 |
| Embeddings | ONNX Runtime session | `CPUExecutionProvider` | `QNNExecutionProvider` |
| ASR | see note below | faster-whisper (CPU) | ORT QNN + AI Hub Whisper |

---

## 1. Prerequisites

- Windows 11 on Snapdragon X Elite / X Plus
- **Python 3.11 or newer, ARM64 build.** Python 3.10 has no ARM64 `onnxruntime-qnn` wheel.
- Qualcomm AI Runtime (QAIRT) / GenieX SDK, installed per Qualcomm's own instructions

## 2. Python environment

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip uninstall onnxruntime
pip install onnxruntime-qnn          # ARM64 Windows only
```

`onnxruntime-qnn` replaces the CPU-only package. Installing both causes an import conflict,
so the uninstall is required, not optional.

## 3. Provider selection — already in the code

`backend/config.py` detects the platform at startup:

```python
[("QNNExecutionProvider", {"backend_path": "QnnHtp.dll"}), "CPUExecutionProvider"]
```

QNN is listed **first with CPU after it in the same list**, so an operator QNN cannot handle
falls back to CPU instead of crashing the session. The provider that actually loaded is
reported at `/api/health` and recorded in every benchmark row, so no result is ever
ambiguous about which hardware produced it.

Verify after install:

```powershell
python -c "import onnxruntime; print(onnxruntime.get_available_providers())"
curl http://127.0.0.1:8000/api/health
```

If `embed_provider` reads `CPUExecutionProvider` on an ARM64 machine, QNN did not load.
That is a real result and should be reported as one, not worked around silently.

## 4. LLM backend

The GGUF file is unchanged across both hosts. Either:

- **llama.cpp ARM64 build** — same command line as the dev host, or
- **GenieX** — serve the same GGUF over an OpenAI-compatible endpoint and point
  `CAMPUSOS_LLM_URL` at it.

```powershell
$env:CAMPUSOS_LLM_URL = "http://127.0.0.1:8090/v1"
python -m backend
```

Because the LLM is a separate process reached over HTTP, swapping it is a configuration
change. This is the main reason the architecture puts it out-of-process at all.

## 5. ASR — the honest caveat

The dev build uses **faster-whisper (CTranslate2, CPU), which has no NPU path.** Shipping it
on Snapdragon would forfeit the NPU argument for this workload.

The intended ARM64 path is Qualcomm AI Hub's Whisper (`qualcomm/Whisper-Small-Quantized`),
supplied as a QAIRT context binary targeting Snapdragon X Elite, executed through ORT's QNN
EP. That swap was **not implemented or measured here** — it is scoped as the first post-MVP
task, and `/api/health` names the active ASR backend so the running system never implies
otherwise.

## 6. Benchmarking on the target

```powershell
python benchmarks\run.py
```

The harness is unmodified across hosts, which is what makes the two columns comparable.
Fill the Snapdragon column in `benchmarks/RESULTS.md` **only** with numbers this harness
produced on that machine.

## 7. What we expect, and why we are not claiming it

Per Qualcomm's published documentation, the NPU advantage on LLM *decode* is expected to
appear in sustained throughput and power draw rather than as a large per-token latency win,
because decode is memory-bandwidth-bound. Embeddings and ASR are the encoder-style workloads
where an NPU typically helps most.

**None of this is our measurement.** Until the harness runs on the hardware, these remain
expectations drawn from vendor documentation, and are labelled as such everywhere they appear.
