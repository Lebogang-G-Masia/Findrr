"""ML-001 ONNX runtime (D-004): beam search with a KV cache, and export parity."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from findrr.ml.t5_onnx_decoding import T5OnnxGenerator  # noqa: E402

REAL_BUNDLE = Path(__file__).resolve().parents[2] / "models" / "title-expander" / "v2.1.0"
VOCAB = 6  # 0 pad/start, 1 eos, 2-5 ordinary tokens


class _FakeEncoder:
    def run(self, _outputs, feeds):
        b, s, d = feeds["inputs_embeds"].shape
        return [np.zeros((b, s, d), dtype=np.float32)]


class _FakeDecoder:
    """Log-probability table indexed by the previous token; checks the KV-cache contract."""

    def __init__(self, table):
        self.table = np.log(np.asarray(table, dtype=np.float64))
        self.past_lengths = []

    def run(self, _outputs, feeds):
        pk, pv = feeds["past_keys"], feeds["past_values"]
        assert pk.shape == pv.shape and pk.shape[1] == feeds["inputs_embeds"].shape[0]
        self.past_lengths.append(pk.shape[3])
        last = feeds["inputs_embeds"][:, 0, 0].astype(int)  # embeddings encode the token id
        logits = self.table[last].astype(np.float32)
        step = np.ones(pk.shape[:3] + (1,) + pk.shape[4:], dtype=np.float32)
        return [logits, np.concatenate([pk, step], axis=3), np.concatenate([pv, step], axis=3)]


def _generator(table):
    gen = T5OnnxGenerator.__new__(T5OnnxGenerator)
    gen.encoder = _FakeEncoder()
    gen.decoder = _FakeDecoder(table)
    gen.embeddings = np.repeat(np.arange(VOCAB, dtype=np.float32)[:, None], 4, axis=1)
    gen.num_layers, gen.num_heads, gen.head_dim = 2, 1, 4
    return gen


def _table(rows):
    """rows: {prev_token: {next_token: prob}}, remaining mass spread over the other tokens."""
    table = np.full((VOCAB, VOCAB), 1e-6)
    for prev, nxt in rows.items():
        for tok, prob in nxt.items():
            table[prev, tok] = prob
    return table / table.sum(axis=1, keepdims=True)


def test_beam_search_respects_allowed_tokens_and_grows_the_cache():
    table = _table({0: {5: 0.9, 3: 0.1}, 3: {1: 0.9}, 4: {1: 0.9}, 5: {4: 0.5, 1: 0.5}})
    gen = _generator(table)

    def allowed(generated):  # never allow token 5
        return [3, 4, 1] if generated else [3, 4]

    out = gen.generate([2, 3, 1], allowed, num_beams=2, max_new_tokens=5)
    assert 5 not in out and out[-1] == 1
    assert gen.decoder.past_lengths[:2] == [0, 1]


def test_finished_hypotheses_are_length_normalised():
    # [3, eos] scores log(0.4)/2 = -0.46; [5, 4, eos] scores log(0.6 * 0.5 * 1.0)/3 = -0.40,
    # so transformers' length_penalty=1.0 prefers the longer hypothesis.
    table = np.full((VOCAB, VOCAB), 1e-9)
    table[0, 5], table[0, 3] = 0.6, 0.4
    table[3, 1] = 1.0
    table[5, 4], table[5, 2] = 0.5, 0.5
    table[4, 1] = table[2, 1] = 1.0
    gen = _generator(table / table.sum(axis=1, keepdims=True))
    out = gen.generate([2], lambda g: list(range(1, VOCAB)) if g else [3, 5], num_beams=2,
                       max_new_tokens=4)
    assert out in ([5, 4, 1], [5, 2, 1])


def test_beam_search_stops_at_max_new_tokens():
    table = _table({t: {2: 0.99} for t in range(VOCAB)})
    gen = _generator(table)
    out = gen.generate([1], lambda g: [2, 3], num_beams=2, max_new_tokens=3)
    assert len(out) == 3 and 1 not in out


def test_onnx_export_and_decoding_match_transformers_generate(tmp_path):
    """A tiny random T5 v1.1: exported graphs and NumPy beam search equal model.generate."""
    pytest.importorskip("onnx")
    pytest.importorskip("onnxruntime")
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    from findrr.ml.t5_onnx_export import export_t5_bundle

    torch.manual_seed(0)
    cfg = transformers.T5Config(
        vocab_size=64, d_model=32, d_kv=8, d_ff=48, num_layers=2, num_decoder_layers=2,
        num_heads=4, feed_forward_proj="gated-gelu", tie_word_embeddings=False,
        decoder_start_token_id=0, eos_token_id=1, pad_token_id=0,
    )
    model = transformers.T5ForConditionalGeneration(cfg).eval()
    with torch.no_grad():  # sharpen the output so near-ties cannot flip on rounding
        model.lm_head.weight.mul_(30.0)
    stats = export_t5_bundle(model, tmp_path)  # raises above 1e-3 (logits are scaled 30x)
    assert stats["decoder_logits_max_abs_diff"] < 1e-3

    gen = T5OnnxGenerator(tmp_path, threads=1)
    allowed_set = [t for t in range(2, 64) if t % 3] + [1]

    def prefix_fn(_batch, ids):
        return allowed_set

    for seed in range(4):
        rng = np.random.default_rng(seed)
        ids = [int(t) for t in rng.integers(2, 64, size=6)] + [1]
        with torch.no_grad():
            ref = model.generate(torch.tensor([ids]), num_beams=2, do_sample=False,
                                 max_new_tokens=12, prefix_allowed_tokens_fn=prefix_fn)[0].tolist()
        ref = ref[1:]
        while ref and ref[-1] == 0:
            ref.pop()
        ours = gen.generate(ids, lambda g: allowed_set, num_beams=2, max_new_tokens=12)
        assert ours == ref


def test_runner_modules_do_not_import_torch():
    """The app's ML-001 path must never pull in torch or transformers."""
    pytest.importorskip("onnxruntime")
    pytest.importorskip("tokenizers")
    script = textwrap.dedent("""
        import json, sys
        import findrr.ml.title_expander_runner as runner_mod
        import findrr.ml.t5_onnx_decoding as dec
        print(json.dumps({"torch": "torch" in sys.modules,
                          "transformers": "transformers" in sys.modules}))
    """)
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    loaded = json.loads(out.stdout.strip().splitlines()[-1])
    assert loaded == {"torch": False, "transformers": False}


@pytest.mark.skipif(
    not (REAL_BUNDLE / "manifest.json").exists(), reason="ML-001 v2.1.0 not installed"
)
def test_real_bundle_expands_without_torch():
    from findrr.ml.title_expander_runner import TitleExpanderRunner

    runner = TitleExpanderRunner(REAL_BUNDLE, version="2.1.0")
    runner.load()
    titles = runner.expand("Truck Driver", [])
    assert 3 <= len(titles) <= 5 and "Truck Driver" not in titles
