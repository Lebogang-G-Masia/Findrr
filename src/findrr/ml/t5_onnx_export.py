"""Export a fine-tuned Flan-T5 (ML-001) to the KV-cached ONNX bundle read by ``t5_onnx_decoding``.

Runs only in ``notebooks/01_train_title_expander.ipynb`` (the notebook generator embeds this
file's source) and in tests. The Findrr app never imports it, so torch stays out of the app.

The decoder step is written directly against the model weights (T5 v1.1: RMSNorm, relative
position bias, gated-GELU feed-forward) instead of tracing transformers' own decoder. The graph
therefore does not depend on the transformers version or its cache classes.
``export_t5_bundle`` checks the exported graphs against the model's own logits and raises if
they differ.
"""

import math
from pathlib import Path


def _build_modules(model):
    """Return (EncoderWrapper, DecoderStep) torch modules for a T5ForConditionalGeneration."""
    import torch

    cfg = model.config
    if not getattr(cfg, "is_gated_act", True) or "gelu" not in getattr(cfg, "dense_act_fn", ""):
        raise ValueError("Only T5 v1.1 / Flan-T5 (gated-gelu) checkpoints are supported.")
    eps = cfg.layer_norm_epsilon
    heads, d_kv = cfg.num_heads, cfg.d_kv
    num_buckets = cfg.relative_attention_num_buckets
    max_distance = cfg.relative_attention_max_distance

    def rms_norm(x, weight):
        variance = x.pow(2).mean(-1, keepdim=True)
        return weight * (x * torch.rsqrt(variance + eps))

    def gelu_new(x):
        return 0.5 * x * (1.0 + torch.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x.pow(3))))

    def split_heads(x):  # (B,T,H*Dk) -> (B,H,T,Dk)
        b, t = x.shape[0], x.shape[1]
        return x.view(b, t, heads, d_kv).transpose(1, 2)

    class EncoderWrapper(torch.nn.Module):
        def __init__(self, encoder):
            super().__init__()
            self.encoder = encoder

        def forward(self, inputs_embeds, attention_mask):
            return self.encoder(inputs_embeds=inputs_embeds,
                                attention_mask=attention_mask).last_hidden_state

    class DecoderStep(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.blocks = model.decoder.block
            self.final_norm = model.decoder.final_layer_norm
            self.lm_head = model.lm_head
            self.rel_bias = model.decoder.block[0].layer[0].SelfAttention.relative_attention_bias
            # Output scaling depends on the transformers version and how it reads
            # tie_word_embeddings, so export_t5_bundle chooses it by comparison with the model.
            self.scale = 1.0

        def position_bias(self, past_len):
            # Unidirectional buckets for query position == past_len over keys 0..past_len.
            keys = torch.arange(past_len + 1, dtype=torch.long)
            n = past_len - keys  # >= 0
            max_exact = num_buckets // 2
            is_small = n < max_exact
            safe = torch.clamp(n, min=1).float()
            large = max_exact + (
                torch.log(safe / max_exact) / math.log(max_distance / max_exact)
                * (num_buckets - max_exact)
            ).to(torch.long)
            large = torch.clamp(large, max=num_buckets - 1)
            bucket = torch.where(is_small, n, large)
            return self.rel_bias(bucket).permute(1, 0).unsqueeze(0).unsqueeze(2)  # (1,H,1,P+1)

        def forward(self, inputs_embeds, encoder_hidden_states, encoder_attention_mask,
                    past_keys, past_values):
            h = inputs_embeds
            bias = self.position_bias(past_keys.shape[3])
            neg = torch.finfo(h.dtype).min
            cross_mask = (1.0 - encoder_attention_mask[:, None, None, :].to(h.dtype)) * neg
            presents_k, presents_v = [], []
            for i, block in enumerate(self.blocks):
                sa, ca, ff = block.layer[0], block.layer[1], block.layer[2]
                x = rms_norm(h, sa.layer_norm.weight)
                q = split_heads(sa.SelfAttention.q(x))
                k = torch.cat([past_keys[i], split_heads(sa.SelfAttention.k(x))], dim=2)
                v = torch.cat([past_values[i], split_heads(sa.SelfAttention.v(x))], dim=2)
                presents_k.append(k)
                presents_v.append(v)
                attn = torch.softmax(q @ k.transpose(-1, -2) + bias, dim=-1) @ v
                h = h + sa.SelfAttention.o(attn.transpose(1, 2).reshape(h.shape[0], 1, -1))
                x = rms_norm(h, ca.layer_norm.weight)
                q = split_heads(ca.EncDecAttention.q(x))
                k = split_heads(ca.EncDecAttention.k(encoder_hidden_states))
                v = split_heads(ca.EncDecAttention.v(encoder_hidden_states))
                attn = torch.softmax(q @ k.transpose(-1, -2) + cross_mask, dim=-1) @ v
                h = h + ca.EncDecAttention.o(attn.transpose(1, 2).reshape(h.shape[0], 1, -1))
                x = rms_norm(h, ff.layer_norm.weight)
                d = ff.DenseReluDense
                h = h + d.wo(gelu_new(d.wi_0(x)) * d.wi_1(x))
            h = rms_norm(h, self.final_norm.weight) * self.scale
            logits = self.lm_head(h)[:, -1, :]
            return logits, torch.stack(presents_k), torch.stack(presents_v)

    return EncoderWrapper(model.encoder), DecoderStep(model)


def export_t5_bundle(model, out_dir: Path, opset: int = 17, tolerance: float = 1e-3) -> dict:
    """Write encoder.onnx, decoder.onnx and embeddings.npy to ``out_dir``; return parity stats.

    Raises ``RuntimeError`` if the ONNX graphs disagree with the model's own forward pass.
    """
    import numpy as np
    import onnxruntime as ort
    import torch

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model = model.cpu().eval()
    cfg = model.config
    encoder, step = _build_modules(model)
    emb = model.shared.weight.detach().float()
    np.save(out_dir / "embeddings.npy", emb.numpy())

    vocab = emb.shape[0]
    ids = torch.tensor([[t % vocab for t in (100, 200, 300, 400)] + [cfg.eos_token_id]])
    mask = torch.ones_like(ids)
    layers, heads, d_kv = cfg.num_decoder_layers, cfg.num_heads, cfg.d_kv
    seq = [cfg.decoder_start_token_id] + [t % vocab for t in (37, 1782, 6, 2116, 3, 9)]
    with torch.no_grad():
        hidden = encoder(emb[ids], mask)
        ref = model(input_ids=ids, attention_mask=mask,
                    decoder_input_ids=torch.tensor([seq])).logits[0]
        # Pick the decoder output scaling that reproduces the model's own first-step logits.
        empty = torch.zeros(layers, 1, heads, 0, d_kv)
        for scale in (1.0, cfg.d_model ** -0.5):
            step.scale = scale
            first = step(emb[torch.tensor([[seq[0]]])], hidden, mask, empty, empty)[0][0]
            if float((first - ref[0]).abs().max()) <= tolerance:
                break
        else:
            raise RuntimeError("Decoder step does not reproduce the model's logits.")
        ref = ref.numpy()
        torch.onnx.export(
            encoder, (emb[ids], mask), str(out_dir / "encoder.onnx"),
            input_names=["inputs_embeds", "attention_mask"], output_names=["hidden"],
            dynamic_axes={"inputs_embeds": {0: "batch", 1: "seq"},
                          "attention_mask": {0: "batch", 1: "seq"},
                          "hidden": {0: "batch", 1: "seq"}},
            opset_version=opset, dynamo=False,
        )
        past = torch.zeros(layers, 1, heads, 2, d_kv)
        torch.onnx.export(
            step, (emb[torch.tensor([[5]])], hidden, mask, past, past),
            str(out_dir / "decoder.onnx"),
            input_names=["inputs_embeds", "encoder_hidden_states", "encoder_attention_mask",
                         "past_keys", "past_values"],
            output_names=["logits", "present_keys", "present_values"],
            dynamic_axes={"inputs_embeds": {0: "batch"},
                          "encoder_hidden_states": {0: "batch", 1: "seq"},
                          "encoder_attention_mask": {0: "batch", 1: "seq"},
                          "past_keys": {1: "batch", 3: "past"},
                          "past_values": {1: "batch", 3: "past"},
                          "logits": {0: "batch"},
                          "present_keys": {1: "batch", 3: "total"},
                          "present_values": {1: "batch", 3: "total"}},
            opset_version=opset, dynamo=False,
        )

    # Parity: step-by-step ONNX decoding (starting from an empty cache) vs the full model.
    enc_s = ort.InferenceSession(str(out_dir / "encoder.onnx"), providers=["CPUExecutionProvider"])
    dec_s = ort.InferenceSession(str(out_dir / "decoder.onnx"), providers=["CPUExecutionProvider"])
    h = enc_s.run(None, {"inputs_embeds": emb[ids].numpy(), "attention_mask": mask.numpy()})[0]
    enc_diff = float(np.abs(h - hidden.numpy()).max())
    pk = np.zeros((layers, 1, heads, 0, d_kv), dtype=np.float32)
    pv = pk.copy()
    dec_diff = 0.0
    for t, tok in enumerate(seq):
        logits, pk, pv = dec_s.run(None, {
            "inputs_embeds": emb[torch.tensor([[tok]])].numpy(),
            "encoder_hidden_states": h, "encoder_attention_mask": mask.numpy(),
            "past_keys": pk, "past_values": pv})
        dec_diff = max(dec_diff, float(np.abs(logits[0] - ref[t]).max()))
    stats = {"encoder_max_abs_diff": enc_diff, "decoder_logits_max_abs_diff": dec_diff,
             "steps_checked": len(seq), "output_scale": step.scale}
    if enc_diff > tolerance or dec_diff > tolerance:
        raise RuntimeError(f"ONNX export does not match the model: {stats}")
    return stats
