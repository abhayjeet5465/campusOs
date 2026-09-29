"""End-to-end check that needs no LLM: make a PDF, ingest it, retrieve, and verify the gate."""
import os, sys, tempfile, pathlib
os.environ["CAMPUSOS_DATA"] = tempfile.mkdtemp(prefix="campusos-test-")
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pymupdf
from backend import ingest, retrieve, store, config

PAGES = [
    "Ohm's Law. The current through a conductor between two points is directly proportional "
    "to the voltage across the two points. The constant of proportionality is the resistance, "
    "giving V = I R. Resistance is measured in ohms and depends on the material, its length "
    "and its cross-sectional area. A longer wire has higher resistance than a shorter one.",
    "Capacitors store energy in an electric field between two conducting plates separated by "
    "a dielectric. Capacitance C equals the charge Q divided by the voltage V. The energy "
    "stored in a capacitor is one half C times V squared. Capacitors in parallel add directly, "
    "while capacitors in series add as reciprocals.",
]


def make_pdf():
    d = pymupdf.open()
    for text in PAGES:
        p = d.new_page()
        p.insert_textbox(pymupdf.Rect(60, 60, 540, 700), text, fontsize=12)
    return d.tobytes()


def main():
    doc = ingest.ingest_pdf(make_pdf(), "Electronics.pdf")
    assert doc["pages"] == 2 and doc["chunks"] >= 2, doc
    print(f"ingest ok: {doc['chunks']} chunks from {doc['pages']} pages")

    hits, grounded = retrieve.gated_search("How is resistance related to voltage and current?")
    assert grounded, f"in-corpus question must pass the gate, top score {hits[0]['score']:.3f}"
    assert hits[0]["page"] == 1, hits[0]["page"]
    print(f"retrieval ok: p.{hits[0]['page']} score {hits[0]['score']:.3f}")

    hits2, grounded2 = retrieve.gated_search("What is the capital of France and who founded it?")
    print(f"out-of-corpus top score {hits2[0]['score']:.3f} -> grounded={grounded2}")
    assert not grounded2, "OUT-OF-CORPUS PROBE PASSED THE GATE — threshold is too low"

    assert store.delete_document(doc["id"]), "delete failed"
    assert store.vectors().shape[0] == 0, "vectors not hard-deleted"
    assert store.list_documents() == []
    print("hard delete ok")
    print("\nPIPELINE OK")


if __name__ == "__main__":
    main()
