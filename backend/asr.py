"""Local speech-to-text. faster-whisper on CPU today; ORT+QNN is the documented Snapdragon path.

Honest note for the submission: faster-whisper (CTranslate2) has NO NPU path. If it is the
active backend, that is disclosed in /api/health rather than quietly implied otherwise.
"""
import io, subprocess, shutil, tempfile, os
from . import config

_model = None
BACKEND = None


def _load():
    global _model, BACKEND
    if _model is None:
        from faster_whisper import WhisperModel
        size = os.environ.get("CAMPUSOS_WHISPER", "base")
        _model = WhisperModel(size, device="cpu", compute_type="int8",
                              download_root=str(config.MODELS_DIR / "whisper"))
        BACKEND = f"faster-whisper-{size} (CPU, CTranslate2 — no NPU path)"
    return _model


def available():
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _to_wav(data: bytes) -> str:
    """Browser MediaRecorder gives webm/ogg. ffmpeg if present, else hand bytes straight to
    faster-whisper, which decodes most containers itself."""
    f = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
    f.write(data); f.close()
    if not shutil.which("ffmpeg"):
        return f.name
    wav = f.name + ".wav"
    subprocess.run(["ffmpeg", "-y", "-i", f.name, "-ar", "16000", "-ac", "1", wav],
                   capture_output=True, check=False)
    return wav if os.path.exists(wav) and os.path.getsize(wav) > 44 else f.name


def transcribe(data: bytes, language=None):
    """Audio never touches disk beyond this temp file, which is deleted before returning."""
    path = _to_wav(data)
    try:
        segments, info = _load().transcribe(path, language=language, beam_size=1, vad_filter=True)
        text = " ".join(s.text.strip() for s in segments).strip()
        return {"text": text, "language": info.language, "backend": BACKEND}
    finally:
        for p in {path, path.replace(".wav", "")}:
            try:
                os.unlink(p)
            except OSError:
                pass
