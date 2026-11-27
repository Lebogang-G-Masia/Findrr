"""ONNX Runtime inference for ML-001 (Flan-T5): constrained beam search with a KV cache (D-004).

Pure NumPy + ONNX Runtime + ``tokenizers``: no torch, no transformers. Used verbatim by both
the Findrr runner and ``notebooks/01_train_title_expander.ipynb`` (the notebook generator embeds
this file's source), so the notebook evaluates exactly what the app runs.

Bundle layout (written by ``t5_onnx_export``):
- ``encoder.onnx``: ``inputs_embeds (B,S,D)``, ``attention_mask (B,S)`` -> ``hidden (B,S,D)``
- ``decoder.onnx``: one decoding step. Inputs ``inputs_embeds (B,1,D)``,
  ``encoder_hidden_states``, ``encoder_attention_mask``, ``past_keys`` and ``past_values``
  ``(L,B,H,P,Dk)``; outputs ``logits (B,V)``, ``present_keys`` and ``present_values``
  ``(L,B,H,P+1,Dk)``.
- ``embeddings.npy``: the shared token embedding (V,D), memory-mapped and stored once.

The beam search mirrors transformers' ``generate(num_beams=N, do_sample=False,
length_penalty=1.0, early_stopping=False, prefix_allowed_tokens_fn=...)``.
"""

from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np


class TokenizersAdapter:
    """The slice of the Hugging Face tokenizer API that ``TitleTrieConstraint`` needs."""

    def __init__(self, tokenizer_json: Path, eos_token_id: int = 1, pad_token_id: int = 0,
                 max_length: int = 128) -> None:
        from tokenizers import Tokenizer

        self.tokenizer = Tokenizer.from_file(str(tokenizer_json))
        self.tokenizer.enable_truncation(max_length=max_length)
        self.tokenizer.no_padding()
        self.eos_token_id = eos_token_id
        self.pad_token_id = pad_token_id

    def convert_tokens_to_ids(self, token: str) -> Optional[int]:
        return self.tokenizer.token_to_id(token)

    def __call__(self, text: str, add_special_tokens: bool = True) -> dict:
        return {"input_ids": self.tokenizer.encode(text, add_special_tokens=add_special_tokens).ids}

    def decode(self, ids: Sequence[int], skip_special_tokens: bool = True) -> str:
        return self.tokenizer.decode(list(ids), skip_special_tokens=skip_special_tokens)


def _log_softmax(x: np.ndarray) -> np.ndarray:
    m = x.max(axis=-1, keepdims=True)
    return x - m - np.log(np.exp(x - m).sum(axis=-1, keepdims=True))


class T5OnnxGenerator:
    """Encoder + KV-cached decoder sessions with constrained beam search."""

    def __init__(self, bundle_dir: Path, threads: int = 4) -> None:
        import onnxruntime as ort

        bundle_dir = Path(bundle_dir)
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        providers = ["CPUExecutionProvider"]
        self.encoder = ort.InferenceSession(str(bundle_dir / "encoder.onnx"), options,
                                            providers=providers)
        self.decoder = ort.InferenceSession(str(bundle_dir / "decoder.onnx"), options,
                                            providers=providers)
        # Memory-mapped: only the rows that are looked up are paged in.
        self.embeddings = np.load(bundle_dir / "embeddings.npy", mmap_mode="r")
        past = {i.name: i.shape for i in self.decoder.get_inputs()}["past_keys"]
        self.num_layers, self.num_heads, self.head_dim = int(past[0]), int(past[2]), int(past[4])

    def _embed(self, ids: np.ndarray) -> np.ndarray:
        return np.asarray(self.embeddings[ids], dtype=np.float32)

    def encode(self, input_ids: Sequence[int]) -> Tuple[np.ndarray, np.ndarray]:
        ids = np.array([list(input_ids)], dtype=np.int64)
        mask = np.ones_like(ids)
        hidden = self.encoder.run(None, {"inputs_embeds": self._embed(ids),
                                         "attention_mask": mask})[0]
        return hidden, mask

    def generate(
        self,
        input_ids: Sequence[int],
        allowed_tokens: Callable[[List[int]], List[int]],
        num_beams: int,
        max_new_tokens: int,
        decoder_start_token_id: int = 0,
        eos_token_id: int = 1,
    ) -> List[int]:
        """Best beam's generated token IDs (without the start token, ending in EOS if any)."""
        hidden, mask = self.encode(input_ids)
        nb = num_beams
        hidden = np.repeat(hidden, nb, axis=0)
        mask = np.repeat(mask, nb, axis=0)
        shape = (self.num_layers, nb, self.num_heads, 0, self.head_dim)
        past_k = np.zeros(shape, dtype=np.float32)
        past_v = np.zeros(shape, dtype=np.float32)
        seqs: List[List[int]] = [[decoder_start_token_id] for _ in range(nb)]
        beam_scores = np.array([0.0] + [-1e9] * (nb - 1))
        hyps: List[Tuple[float, List[int]]] = []

        def add_hypothesis(seq: List[int], sum_logprobs: float, generated_len: int) -> None:
            hyps.append((sum_logprobs / generated_len, seq))
            hyps.sort(key=lambda h: -h[0])
            del hyps[nb:]

        finished_by_score = False
        for _ in range(max_new_tokens):
            last = np.array([[s[-1]] for s in seqs], dtype=np.int64)
            logits, past_k, past_v = self.decoder.run(None, {
                "inputs_embeds": self._embed(last),
                "encoder_hidden_states": hidden,
                "encoder_attention_mask": mask,
                "past_keys": past_k,
                "past_values": past_v,
            })
            logprobs = _log_softmax(logits.astype(np.float64))
            masked = np.full_like(logprobs, -np.inf)
            for b in range(nb):
                allowed = allowed_tokens(seqs[b][1:])
                masked[b, allowed] = logprobs[b, allowed]
            scores = (masked + beam_scores[:, None]).reshape(-1)
            vocab = logprobs.shape[1]
            top = np.argsort(-scores, kind="stable")[: 2 * nb]
            cur_len = len(seqs[0]) + 1
            next_seqs: List[List[int]] = []
            next_scores: List[float] = []
            next_rows: List[int] = []
            for rank, idx in enumerate(top):
                beam, token = divmod(int(idx), vocab)
                score = float(scores[idx])
                if not np.isfinite(score):
                    continue
                if token == eos_token_id:
                    if rank < nb:
                        add_hypothesis(seqs[beam] + [token], score, cur_len - 1)
                else:
                    next_seqs.append(seqs[beam] + [token])
                    next_scores.append(score)
                    next_rows.append(beam)
                if len(next_seqs) == nb:
                    break
            best_running = float(scores[top[0]])
            if len(hyps) >= nb and hyps[-1][0] >= best_running / (cur_len - 1):
                finished_by_score = True
                break
            if not next_seqs:
                finished_by_score = True
                break
            while len(next_seqs) < nb:  # keep the batch shape; a dead beam never wins
                next_seqs.append(next_seqs[-1])
                next_scores.append(-1e9)
                next_rows.append(next_rows[-1])
            rows = np.array(next_rows)
            past_k, past_v = past_k[:, rows], past_v[:, rows]
            seqs, beam_scores = next_seqs, np.array(next_scores)
        if not finished_by_score:
            for seq, score in zip(seqs, beam_scores):
                add_hypothesis(seq, float(score), len(seq) - 1)
        return hyps[0][1][1:]
