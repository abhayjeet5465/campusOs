"""Local embeddings: multilingual-e5-small via ONNX Runtime. Provider chosen by platform."""
import numpy as np, onnxruntime as ort
from tokenizers import Tokenizer
from . import config

REPO = "intfloat/multilingual-e5-small"
_sess = _tok = None


def _model_dir():
    return config.MODELS_DIR / "e5-small"


def ensure_downloaded():
    """First-run only. The one place the app touches the network, by design (PRD §17)."""
    d = _model_dir()
    if (d / "model.onnx").exists() and (d / "tokenizer.json").exists():
        return d
    from huggingface_hub import hf_hub_download
    d.mkdir(parents=True, exist_ok=True)
    for repo_file, local in (("onnx/model.onnx", "model.onnx"), ("tokenizer.json", "tokenizer.json")):
        p = hf_hub_download(REPO, repo_file)
        (d / local).write_bytes(open(p, "rb").read())
    return d


def _load():
    global _sess, _tok
    if _sess is None:
        d = ensure_downloaded()
        _tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        _tok.enable_truncation(512)
        _tok.enable_padding()
        _sess = ort.InferenceSession(str(d / "model.onnx"), providers=config.ort_providers())
    return _sess, _tok


def active_provider():
    return _load()[0].get_providers()[0] if _sess else "not loaded"


def embed(texts, prefix="passage: "):
    """e5 requires the query:/passage: prefix -- omitting it measurably degrades retrieval."""
    sess, tok = _load()
    out = np.zeros((len(texts), config.EMBED_DIM), dtype=np.float32)
    for s in range(0, len(texts), 32):
        batch = [prefix + t for t in texts[s:s + 32]]
        enc = tok.encode_batch(batch)
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": mask}
        names = {i.name for i in sess.get_inputs()}
        if "token_type_ids" in names:
            feed["token_type_ids"] = np.zeros_like(ids)
        hidden = sess.run(None, {k: v for k, v in feed.items() if k in names})[0]
        m = mask[..., None].astype(np.float32)
        pooled = (hidden * m).sum(1) / np.clip(m.sum(1), 1e-9, None)   # mean pooling
        out[s:s + len(batch)] = pooled
    return out / np.clip(np.linalg.norm(out, axis=1, keepdims=True), 1e-9, None)


def embed_query(text):
    return embed([text], prefix="query: ")[0]
