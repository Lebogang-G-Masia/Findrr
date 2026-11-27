"""ML-002 runner loads its tokenizer without transformers/torch (memory budget, spec §12)."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from findrr.ml.similarity_evaluator_runner import SimilarityEvaluatorRunner, load_tokenizer

REAL_BUNDLE = Path(__file__).resolve().parents[2] / "models" / "similarity-evaluator" / "v1.1.0"


def _write_bert_tokenizer(directory: Path) -> None:
    """A tiny BERT-style tokenizer.json (WordPiece + [CLS]/[SEP]), like MiniLM's."""
    tokenizers = pytest.importorskip("tokenizers")
    from tokenizers import models, normalizers, pre_tokenizers, processors

    vocab = {t: i for i, t in enumerate(
        ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "software", "developer", "engineer", "nurse"])}
    tok = tokenizers.Tokenizer(models.WordPiece(vocab, unk_token="[UNK]"))
    tok.normalizer = normalizers.BertNormalizer(lowercase=True)
    tok.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
    tok.post_processor = processors.TemplateProcessing(
        single="[CLS] $A [SEP]", special_tokens=[("[CLS]", 2), ("[SEP]", 3)])
    tok.save(str(directory / "tokenizer.json"))


class _Input:
    def __init__(self, name):
        self.name = name


class _FakeSession:
    """Returns token embeddings equal to the token ID in every dimension."""

    def __init__(self):
        self.feeds = []

    def get_inputs(self):
        return [_Input("input_ids"), _Input("attention_mask"), _Input("token_type_ids")]

    def run(self, _outputs, feeds):
        import numpy as np

        self.feeds.append(feeds)
        ids = feeds["input_ids"].astype(np.float32)
        return [np.repeat(ids[..., None], 4, axis=-1)]


def test_tokenizer_adds_special_tokens_and_truncates(tmp_path):
    _write_bert_tokenizer(tmp_path)
    tok = load_tokenizer(tmp_path)
    assert tok.encode("Software Developer").ids == [2, 4, 5, 3]
    assert len(tok.encode(" ".join(["nurse"] * 500)).ids) == 128


def test_embedding_uses_ids_mask_and_type_ids(tmp_path):
    np = pytest.importorskip("numpy")
    _write_bert_tokenizer(tmp_path)
    runner = SimilarityEvaluatorRunner(artifact_dir=tmp_path)
    runner._tokenizer = load_tokenizer(tmp_path)
    runner._session = _FakeSession()

    vec = runner._embed_text("Software Engineer")

    feeds = runner._session.feeds[0]
    assert feeds["input_ids"].tolist() == [[2, 4, 6, 3]]
    assert feeds["attention_mask"].tolist() == [[1, 1, 1, 1]]
    assert feeds["token_type_ids"].tolist() == [[0, 0, 0, 0]]
    assert all(a.dtype == np.int64 for a in feeds.values())
    assert np.allclose(vec, np.full(4, 0.5))  # mean of IDs, then L2-normalised


def test_load_does_not_import_transformers_or_torch(tmp_path):
    pytest.importorskip("tokenizers")
    pytest.importorskip("onnxruntime")
    _write_bert_tokenizer(tmp_path)
    script = textwrap.dedent(f"""
        import json, sys
        import onnxruntime
        import findrr.ml.similarity_evaluator_runner as m
        m.load_manifest = lambda path: None
        m.verify_artifact_integrity = lambda manifest, path: None
        onnxruntime.InferenceSession = lambda *a, **k: object()
        r = m.SimilarityEvaluatorRunner(artifact_dir=__import__('pathlib').Path({str(tmp_path)!r}))
        r.load()
        print(json.dumps({{"loaded": r.is_loaded(),
                          "torch": "torch" in sys.modules,
                          "transformers": "transformers" in sys.modules}}))
    """)
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout.strip().splitlines()[-1]) == {
        "loaded": True, "torch": False, "transformers": False}


@pytest.mark.skipif(
    not (REAL_BUNDLE / "manifest.json").exists(), reason="ML-002 bundle not installed"
)
def test_real_bundle_scores_match_kaggle_acceptance_values():
    """Local evidence only: the bundle's Kaggle values (manifest) are reproduced exactly."""
    manifest = json.loads((REAL_BUNDLE / "manifest.json").read_text())["evaluation_summary"]
    runner = SimilarityEvaluatorRunner(artifact_dir=REAL_BUNDLE, version="1.1.0")
    runner.load()
    synonym = runner.evaluate_pair("Software Developer", "Software Engineer")
    distinct = runner.evaluate_pair("Software Developer", "Dental Assistant")
    assert synonym == pytest.approx(manifest["ac_ml_002_1_synonym_similarity"], abs=1e-4)
    assert distinct == pytest.approx(manifest["ac_ml_002_2_distinct_similarity"], abs=1e-4)
