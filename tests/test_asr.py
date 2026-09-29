"""ASR smoke test using Windows SAPI to synthesize the probe audio.

Synthetic speech is cleaner than a real student in a hostel at 1 am, so this proves the
pipeline is wired, NOT that WER is acceptable. Real WER needs recorded human samples.
"""
import os, sys, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

PHRASE = "What is Ohms law and how does resistance work"


def speak(text, path):
    import win32com.client
    sp = win32com.client.Dispatch("SAPI.SpVoice")
    fs = win32com.client.Dispatch("SAPI.SpFileStream")
    fs.Open(path, 3)
    sp.AudioOutputStream = fs
    sp.Speak(text)
    fs.Close()


def main():
    from backend import asr
    if not asr.available():
        print("SKIP: faster-whisper not installed")
        return
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        print("SKIP: pywin32 not available to synthesize probe audio")
        return

    path = os.path.join(tempfile.gettempdir(), "campusos_asr_probe.wav")
    speak(PHRASE, path)
    r = asr.transcribe(open(path, "rb").read())
    os.unlink(path)

    heard = r["text"].lower()
    # Content words, not exact match: Whisper adds punctuation and renders "Ohms" as "Om's".
    hits = sum(w in heard for w in ("law", "resistance", "work", "what"))
    assert hits >= 3, f"transcript lost the question: {r['text']!r}"
    print(f"expected: {PHRASE}\nheard   : {r['text']}\nbackend : {r['backend']}\nASR OK ({hits}/4 key words)")


if __name__ == "__main__":
    main()
