"""Measure time-to-first-token and total time for whichever model the LLM server has loaded.

TTFT is the number that decides whether the app feels alive. Total time decides whether the
demo is watchable. Both are reported, because optimising one while ignoring the other is how
a benchmark flatters a product that is unpleasant to use.
"""
import os, sys, time, pathlib, statistics
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import psutil
from backend import llm, config

CONTEXT = """--- BLOCK 1 | [Electronics.pdf, p.1] ---
Ohm's Law. The current through a conductor between two points is directly proportional to the
voltage across the two points. The constant of proportionality is the resistance, giving
V = I R. Resistance is measured in ohms and depends on the material, its length and its
cross-sectional area. A longer wire has higher resistance than a shorter one.

--- BLOCK 2 | [Electronics.pdf, p.2] ---
Capacitors store energy in an electric field between two conducting plates separated by a
dielectric. Capacitance C equals the charge Q divided by the voltage V. The energy stored in a
capacitor is one half C times V squared."""

QUESTIONS = ["What is Ohm's law?", "How do capacitors store energy?"]


def model_name():
    try:
        import httpx
        return httpx.get(f"{config.LLM_BASE_URL}/models", timeout=3).json()["data"][0]["id"]
    except Exception:
        return "unknown"


def main():
    if not llm.healthy():
        raise SystemExit(f"No LLM server at {config.LLM_BASE_URL}")
    name = model_name()
    m = psutil.virtual_memory()
    print(f"model            : {name}")
    print(f"system RAM       : {m.total/1e9:.1f} GB total, {m.available/1e9:.1f} GB available "
          f"({m.percent:.0f}% used)")
    server = next((p.info["memory_info"].rss / 1e6
                   for p in psutil.process_iter(["name", "memory_info"])
                   if p.info["name"] == "llama-server.exe"), None)
    if server:
        print(f"llama-server RSS : {server:.0f} MB")

    ttfts, totals, words = [], [], []
    for q in QUESTIONS:
        prompt = f"CONTEXT:\n{CONTEXT}\n\nSTUDENT QUESTION: {q}\nCite as [doc, p.N]."
        t0 = time.perf_counter()
        first, n = None, 0
        parts = []
        for tok in llm.chat_stream([{"role": "user", "content": prompt}], max_tokens=200):
            if first is None:
                first = time.perf_counter() - t0
            parts.append(tok)
            n += 1
        total = time.perf_counter() - t0
        ttfts.append(first or total)
        totals.append(total)
        words.append(len("".join(parts).split()) / total)
        print(f"  {q[:34]:36} TTFT {first:5.2f} s   total {total:6.2f} s   {n:3d} chunks")

    print(f"\nmedian TTFT      : {statistics.median(ttfts):.2f} s")
    print(f"median total     : {statistics.median(totals):.2f} s")
    print(f"median words/s   : {statistics.median(words):.1f}")


if __name__ == "__main__":
    main()
