"""Central config. All paths local; nothing here reaches the network at runtime."""
import os, platform, pathlib

APP_DIR = pathlib.Path(os.environ.get("CAMPUSOS_DATA") or
                       (pathlib.Path(os.environ["LOCALAPPDATA"]) / "CampusOS"
                        if os.name == "nt" else pathlib.Path.home() / ".campusos"))
DB_PATH = APP_DIR / "campusos.db"
VEC_PATH = APP_DIR / "vectors.npy"
MODELS_DIR = pathlib.Path(os.environ.get("CAMPUSOS_MODELS", pathlib.Path(__file__).parent.parent / "models"))

LLM_BASE_URL = os.environ.get("CAMPUSOS_LLM_URL", "http://127.0.0.1:8090/v1")
LLM_MODEL = os.environ.get("CAMPUSOS_LLM_MODEL", "local")

EMBED_DIM = 384
# Chunk size and TOP_K are latency controls, not just retrieval knobs: prompt tokens go
# through prefill at a measured ~28 tok/s on this memory-starved box, so time-to-first-token
# is roughly linear in (CHUNK_TOKENS x TOP_K). 400x3 keeps a typical prompt near 1200 tokens.
# Smaller chunks also sharpen retrieval precision, so this is not purely a speed trade.
CHUNK_TOKENS, CHUNK_OVERLAP = 400, 80
TOP_K = 3
# Relevance gate: below this cosine score we refuse rather than guess (TRD §7).
# Tuned against eval/ probes -- not a feel-good default.
RELEVANCE_THRESHOLD = float(os.environ.get("CAMPUSOS_GATE", "0.78"))
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_PAGES = 1200


def is_arm64_windows() -> bool:
    return os.name == "nt" and platform.machine().lower() in ("arm64", "aarch64")


def ort_providers():
    """QNN first on ARM64 so an unsupported graph falls back to CPU in the same list (TRD §15)."""
    if is_arm64_windows():
        return [("QNNExecutionProvider", {"backend_path": "QnnHtp.dll"}), "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]


APP_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
