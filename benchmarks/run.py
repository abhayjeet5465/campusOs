"""Benchmark harness. Runs unmodified on Snapdragon so numbers are directly comparable.

Non-negotiable: every figure here is measured on the machine that ran it. Snapdragon
columns stay empty and labelled "requires hardware" until genuinely measured.
"""
import os, sys, time, platform, subprocess, tempfile, pathlib, json
os.environ.setdefault("CAMPUSOS_DATA", tempfile.mkdtemp(prefix="campusos-bench-"))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import psutil
from tests.test_pipeline import make_pdf
from backend import ingest, retrieve, embed, llm, config

QUESTIONS = ["What is Ohm's law?", "How do capacitors store energy?",
             "What happens to resistance when a wire gets longer?"]


def rss_mb():
    return psutil.Process().memory_info().rss / 1e6


def llm_model_name():
    """Ask the server what it loaded. Recording the configured name instead would let the
    table drift from reality the moment someone starts a different GGUF."""
    try:
        import httpx
        r = httpx.get(f"{config.LLM_BASE_URL}/models", timeout=3)
        return r.json()["data"][0]["id"]
    except Exception:
        return "unavailable (server not running)"


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip() or "not a git repo"
    except OSError:
        return "git unavailable"


def main():
    rows = []
    base = rss_mb()

    t = time.perf_counter()
    embed.embed(["warmup"])
    rows.append(("Embedding model load", f"{time.perf_counter()-t:.2f} s"))

    pdf = make_pdf()
    t = time.perf_counter()
    doc = ingest.ingest_pdf(pdf, "Bench.pdf")
    dt = time.perf_counter() - t
    rows.append(("Ingest (2 pages)", f"{dt:.2f} s"))
    rows.append(("Ingest throughput", f"{doc['pages']/dt:.2f} pages/s"))

    t = time.perf_counter()
    embed.embed_query("what is resistance")
    rows.append(("Query embedding latency", f"{(time.perf_counter()-t)*1000:.1f} ms"))

    lat = []
    for q in QUESTIONS:
        t = time.perf_counter()
        retrieve.gated_search(q)
        lat.append((time.perf_counter() - t) * 1000)
    rows.append(("Retrieval latency (mean of 3)", f"{sum(lat)/len(lat):.1f} ms"))

    if llm.healthy():
        ttft, tps = [], []
        for q in QUESTIONS:
            hits, _ = retrieve.gated_search(q)
            t = time.perf_counter()
            out = llm.chat([{"role": "user", "content": f"Context:\n{hits[0]['text']}\n\nQ: {q}"}],
                           max_tokens=120)
            el = time.perf_counter() - t
            ttft.append(el)
            tps.append(len(out.split()) / el)
        rows.append(("LLM full response (mean of 3)", f"{sum(ttft)/len(ttft):.2f} s"))
        rows.append(("LLM throughput (approx words/s)", f"{sum(tps)/len(tps):.1f}"))
    else:
        rows.append(("LLM latency", "SKIPPED — llama-server not running"))

    # Memory headroom is recorded because on an 8 GB machine it, not the CPU, sets the
    # latency. Publishing a TTFT without it would make an unreproducible number look precise.
    vm = psutil.virtual_memory()
    rows.append(("System RAM available during run", f"{vm.available/1e9:.1f} GB ({vm.percent:.0f}% used)"))
    server_rss = next((pr.info["memory_info"].rss / 1e6
                       for pr in psutil.process_iter(["name", "memory_info"])
                       if pr.info["name"] == "llama-server.exe"), None)
    if server_rss:
        rows.append(("llama-server RSS", f"{server_rss:.0f} MB"))
    rows.append(("Peak RSS (this process)", f"{rss_mb():.0f} MB"))
    rows.append(("RSS delta from baseline", f"{rss_mb()-base:.0f} MB"))

    env = [
        ("Machine", platform.machine()), ("Processor", platform.processor() or "unknown"),
        ("OS", f"{platform.system()} {platform.release()} {platform.version()}"),
        ("Python", platform.python_version()),
        ("RAM total", f"{psutil.virtual_memory().total/1e9:.1f} GB"),
        ("Active embedding EP", embed.active_provider()),
        ("Providers configured", ", ".join(p if isinstance(p, str) else p[0] for p in config.ort_providers())),
        ("LLM endpoint", config.LLM_BASE_URL), ("Relevance gate", str(config.RELEVANCE_THRESHOLD)),
        ("LLM model", llm_model_name()), ("Commit", git_commit()),
        ("Run at", time.strftime("%Y-%m-%d %H:%M:%S")),
    ]

    md = ["# CampusOS AI — Benchmark Results", "",
          "> Measured on the machine described below. **No NPU was present and none was used.**",
          "> The Snapdragon column is intentionally empty: we have no such hardware, and a",
          "> vendor-quoted or extrapolated figure is not a measurement.", "",
          "## Environment", "", "| Property | Value |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in env]
    md += ["", "## Results", "", "| Metric | This machine (x86_64, CPU) | Snapdragon X (NPU) |", "|---|---|---|"]
    md += [f"| {k} | {v} | _requires hardware_ |" for k, v in rows]
    md += ["", "## Offline verification", "",
           "`python tests/test_egress.py` blocks every non-loopback socket and runs a full",
           "ingest + retrieval cycle. Result is recorded in `EVALUATION.md`.", ""]

    out = pathlib.Path(__file__).parent / "RESULTS.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(f"{k:36} {v}" for k, v in rows))
    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
