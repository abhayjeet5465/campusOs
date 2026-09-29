"""Groundedness + refusal scoring against a fixed eval set.

The gate that matters: refusal on out-of-corpus probes must be 100 %. A single
invented answer there is a product failure, not a percentage point.
"""
import os, sys, json, tempfile, pathlib
os.environ.setdefault("CAMPUSOS_DATA", tempfile.mkdtemp(prefix="campusos-eval-"))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend import ingest, answer, llm, retrieve

HERE = pathlib.Path(__file__).parent


def load_set():
    p = HERE / "eval_set.json"
    if not p.exists():
        raise SystemExit(f"Missing {p}. Create it from your real course PDFs — see eval/README.md")
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    spec = load_set()
    pdf_dir = HERE / "pdfs"
    ingested = []
    for f in sorted(pdf_dir.glob("*.pdf")):
        ingested.append(ingest.ingest_pdf(f.read_bytes(), f.name))
    if not ingested:
        raise SystemExit(f"No PDFs in {pdf_dir}. The eval set is worthless without real material.")
    print(f"Ingested {len(ingested)} docs, {sum(d['chunks'] for d in ingested)} chunks\n")

    use_llm = llm.healthy()
    if not use_llm:
        print("llama-server not running — scoring retrieval and the gate only.\n")

    grounded_ok = cited_ok = 0
    for q in spec["in_corpus"]:
        hits, passed = retrieve.gated_search(q["question"])
        pages = {h["page"] for h in hits}
        hit = bool(pages & set(q.get("pages", [])))  if q.get("pages") else passed
        grounded_ok += hit
        mark = "PASS" if hit else "FAIL"
        line = f"[{mark}] {q['question'][:60]:62} gate={passed} pages={sorted(pages)}"
        if use_llm:
            r = answer.ask(q["question"])
            cited = bool(r["citations"])
            cited_ok += cited and r["grounded"]
            line += f" cites={len(r['citations'])}"
        print(line)

    refused = 0
    print()
    for q in spec["out_of_corpus"]:
        r = answer.ask(q) if use_llm else (
            {"grounded": retrieve.gated_search(q)[1]})
        ok = not r["grounded"]
        refused += ok
        print(f"[{'PASS' if ok else 'FAIL — INVENTED AN ANSWER'}] probe: {q[:60]}")

    n_in, n_out = len(spec["in_corpus"]), len(spec["out_of_corpus"])
    print(f"\nRetrieval groundedness : {grounded_ok}/{n_in} = {grounded_ok/n_in:.0%}  (gate: >= 90%)")
    if use_llm:
        print(f"Answers with citations : {cited_ok}/{n_in} = {cited_ok/n_in:.0%}")
    print(f"Out-of-corpus refusal  : {refused}/{n_out} = {refused/n_out:.0%}  (gate: 100%)")
    if refused < n_out:
        print("\nREFUSAL GATE FAILED. Raise CAMPUSOS_GATE before shipping — refusing is the correct failure.")
        sys.exit(1)


if __name__ == "__main__":
    main()
