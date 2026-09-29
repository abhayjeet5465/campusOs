"""One-time downloader. Run once with internet; everything after is offline.

Kept as a script rather than app startup logic so the offline guarantee is easy to
audit: the app itself only downloads the embedding model on first use.
"""
import sys, pathlib, zipfile, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from backend import config

# Llama Community Licence, not Apache. Chosen over Qwen2.5-1.5B (Apache) because the 1.5B
# tier's Hindi/Hinglish output was measured as unusable -- see docs/DECISIONS.md ADR-10.
LLM_REPO = "bartowski/Llama-3.2-3B-Instruct-GGUF"
LLM_FILE = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
# Prebuilt CPU server so there is no build toolchain step on either host.
# The release tag is resolved at run time: llama.cpp tags every build (b#####), so a
# hardcoded tag rots within days.
LLAMA_RELEASES = "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=20"


def llm():
    from huggingface_hub import hf_hub_download
    out = config.MODELS_DIR / LLM_FILE.lower()
    if out.exists():
        print(f"LLM present: {out}")
        return out
    print(f"Downloading {LLM_FILE} (~2.0 GB)...")
    p = hf_hub_download(LLM_REPO, LLM_FILE)
    out.write_bytes(open(p, "rb").read())
    print(f"LLM -> {out}")
    return out


def server():
    import json, platform
    d = config.MODELS_DIR / "llama.cpp"
    for existing in d.rglob("llama-server.exe"):
        print(f"llama-server present: {existing}")
        return existing
    arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
    want = f"-bin-win-cpu-{arch}.zip"
    with urllib.request.urlopen(LLAMA_RELEASES) as r:
        releases = json.load(r)
    asset = next((a for rel in releases for a in rel["assets"] if a["name"].endswith(want)), None)
    if not asset:
        raise SystemExit(f"No llama.cpp release asset matching *{want}. "
                         "Download llama-server.exe manually into models/llama.cpp/.")
    d.mkdir(parents=True, exist_ok=True)
    z = d / "llama.zip"
    print(f"Downloading {asset['name']}...")
    urllib.request.urlretrieve(asset["browser_download_url"], z)
    with zipfile.ZipFile(z) as f:
        f.extractall(d)
    z.unlink()
    for exe in d.rglob("llama-server.exe"):
        print(f"llama-server -> {exe}")
        return exe
    raise SystemExit("llama-server.exe not found inside the release archive")


def embeddings():
    from backend import embed
    print(f"Embeddings -> {embed.ensure_downloaded()}")


def whisper():
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper not installed — skipping (pip install faster-whisper)")
        return
    WhisperModel("base", device="cpu", compute_type="int8",
                 download_root=str(config.MODELS_DIR / "whisper"))
    print("Whisper base ready")


if __name__ == "__main__":
    which = sys.argv[1:] or ["embeddings", "llm", "server", "whisper"]
    for name in which:
        globals()[name]()
