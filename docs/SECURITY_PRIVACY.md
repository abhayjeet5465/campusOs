# CampusOS AI — Security & Privacy

The product's central promise is that a student's private course material never leaves their
laptop. This document states how that is enforced and where the limits are.

---

## Threat model, briefly

**In scope:** a hostile PDF; accidental data egress; material persisting after deletion;
another local process reading app data.

**Out of scope:** an attacker with an account on the machine, physical access, or admin rights.
This is a single-user local app with no authentication by design — the operating system's user
account *is* the security boundary. Pretending otherwise would be security theatre.

---

## Network

| Control | Where |
|---|---|
| Backend binds loopback only | `backend/__main__.py` — `host="127.0.0.1"` |
| CORS restricted to the local origin | `backend/app.py` |
| LLM endpoint is loopback | `config.LLM_BASE_URL` |
| No telemetry, analytics, or crash reporting | none exists in the codebase |
| **Egress asserted in a test** | `tests/test_egress.py` |

The egress test patches `socket.socket.connect`, raises on any non-loopback address, and runs a
full ingest + retrieval cycle. It passes with **zero** outbound connections. This is the only
form of "we don't phone home" that is worth anything, because it is checkable.

**The one exception, stated plainly:** first-run model download (`scripts/fetch_models.py`, and
`embed.ensure_downloaded()` on first use) fetches weights from Hugging Face. It is a one-time
setup step, it is in a script the user runs deliberately, and nothing about the student's
documents is involved. After it, the app never needs the network again.

## Input handling

PDFs are untrusted input.

| Control | Where |
|---|---|
| Size cap (50 MB) | `ingest.ingest_pdf()` |
| `%PDF` magic-byte check, not extension-trust | `ingest.ingest_pdf()` |
| Page cap (1200) | `ingest.ingest_pdf()` |
| Encrypted PDFs rejected by name | `doc.needs_pass` |
| Uploaded filenames never used as filesystem paths | documents are keyed by UUID |
| No `pickle`, no `eval`, no shell execution | — |

**Prompt injection.** Extracted PDF text is passed to the LLM as *data* inside delimited,
labelled blocks, and the system prompt states that instructions appearing inside those blocks
are part of the document and must be ignored.

This is mitigation, not a guarantee — prompt injection is not a solved problem, and a
sufficiently crafted document may still steer the model. The reason the impact is bounded here
is architectural rather than prompt-based: **the model has no tools.** It cannot read files,
make network calls, or execute anything. The worst outcome of a successful injection is a wrong
or manipulated answer on screen, and citation validation means it still cannot fabricate a page
reference to support one.

## Storage & deletion

Everything lives in `%LOCALAPPDATA%\CampusOS\` — SQLite rows, the vector array, quiz history.
File-system permissions are the OS user's; the app adds no encryption at rest, which is stated
here rather than implied.

**Deletion is hard deletion.** `store.delete_document()` removes the SQLite rows, rebuilds
`vectors.npy` without the deleted vectors, and reindexes every remaining `vec_row`.
`tests/test_pipeline.py` asserts the vector count returns to zero.

Tombstoning would have been less code. It was rejected: leaving the student's deleted material
on disk while the UI says it is gone is the wrong place to save effort in a privacy product
(ADR-08).

## Audio

Audio is written to a single temp file only because the decoder needs a path, and that file is
deleted in a `finally` block before the transcript returns. It is never written to the app data
directory and never persisted. The transcript is shown to the student for confirmation before
it is used as a query.

## Logging

Logs record events and timings. They must never record document text, questions, answers, or
transcripts.

## Known limitations

Stated because omitting them would undercut the rest of this document:

1. **No encryption at rest.** Anyone who can read the user's profile directory can read the
   documents and vectors. Mitigating this properly requires a key the student supplies, which
   is out of scope for the MVP.
2. **No authentication.** Any process running as that user can reach `127.0.0.1:8000`.
   Deliberate for a single-user local app; it does mean a hostile local process could query
   the student's material.
3. **Prompt injection is mitigated, not eliminated.** See above.
4. **The first-run download is a network event.** Unavoidable, deliberate, and scoped to weights.
