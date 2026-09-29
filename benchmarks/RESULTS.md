# CampusOS AI — Benchmark Results

> Measured on the machine described below. **No NPU was present and none was used.**
> The Snapdragon column is intentionally empty: we have no such hardware, and a
> vendor-quoted or extrapolated figure is not a measurement.

## Environment

| Property | Value |
|---|---|
| Machine | AMD64 |
| Processor | Intel64 Family 6 Model 140 Stepping 2, GenuineIntel |
| OS | Windows 10 10.0.26200 |
| Python | 3.10.2 |
| RAM total | 8.2 GB |
| Active embedding EP | CPUExecutionProvider |
| Providers configured | CPUExecutionProvider |
| LLM endpoint | http://127.0.0.1:8090/v1 |
| Relevance gate | 0.78 |
| LLM model | models/llama-3.2-3b-instruct-q4_k_m.gguf |
| Commit | fd62040 |
| Run at | 2026-09-29 13:33:42 |

## Results

| Metric | This machine (x86_64, CPU) | Snapdragon X (NPU) |
|---|---|---|
| Embedding model load | 2.23 s | _requires hardware_ |
| Ingest (2 pages) | 1.16 s | _requires hardware_ |
| Ingest throughput | 1.72 pages/s | _requires hardware_ |
| Query embedding latency | 8.8 ms | _requires hardware_ |
| Retrieval latency (mean of 3) | 7.7 ms | _requires hardware_ |
| LLM full response (mean of 3) | 13.25 s | _requires hardware_ |
| LLM throughput (approx words/s) | 4.3 | _requires hardware_ |
| Peak RSS (this process) | 508 MB | _requires hardware_ |
| RSS delta from baseline | 426 MB | _requires hardware_ |

## Offline verification

`python tests/test_egress.py` blocks every non-loopback socket and runs a full
ingest + retrieval cycle. Result is recorded in `EVALUATION.md`.
