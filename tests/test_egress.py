"""No-egress assertion (NFR-05): during a full ingest+retrieve cycle, no socket may
leave the loopback interface. Models must already be downloaded -- that is the point.
"""
import os, sys, socket, tempfile, pathlib
os.environ["CAMPUSOS_DATA"] = tempfile.mkdtemp(prefix="campusos-egress-")
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

LOOPBACK = ("127.0.0.1", "localhost", "::1")
violations = []
_connect = socket.socket.connect


def guarded(self, addr):
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if host not in LOOPBACK:
        violations.append(host)
        raise OSError(f"EGRESS BLOCKED: {host}")
    return _connect(self, addr)


socket.socket.connect = guarded

from tests.test_pipeline import make_pdf  # noqa: E402
from backend import ingest, retrieve      # noqa: E402


def main():
    doc = ingest.ingest_pdf(make_pdf(), "Offline.pdf")
    hits, grounded = retrieve.gated_search("What is Ohm's law?")
    assert grounded and hits, "retrieval failed with networking blocked"
    assert not violations, f"OUTBOUND CONNECTIONS ATTEMPTED: {violations}"
    print(f"no-egress OK: {doc['chunks']} chunks ingested, retrieval grounded, 0 outbound connections")


if __name__ == "__main__":
    main()
