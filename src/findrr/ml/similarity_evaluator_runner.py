"""Model 2 runner: Semantic Similarity Evaluator (MiniLM Bi-Encoder ONNX)."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    import numpy as np

from findrr.ml.base import IModelRunner
from findrr.ml.manifest import load_manifest, verify_artifact_integrity

logger = logging.getLogger(__name__)


def _compute_mock_similarity(text_a: str, text_b: str) -> float:
    """Deterministic token/ngram similarity heuristic for Mock Model 2."""
    if text_a.lower().strip() == text_b.lower().strip():
        return 1.0

    tokens_a = set(text_a.lower().replace("-", " ").replace("/", " ").split())
    tokens_b = set(text_b.lower().replace("-", " ").replace("/", " ").split())

    if not tokens_a or not tokens_b:
        return 0.0

    # Synonyms dictionary for high scoring test assertions
    synonym_clusters = [
        {"software", "developer", "engineer", "programmer", "coder"},
        {"backend", "server", "api", "systems"},
        {"frontend", "ui", "web", "client"},
        {"data", "scientist", "machine", "learning", "ai", "analyst"},
        {"devops", "cloud", "infrastructure", "sre", "platform"},
    ]

    shared_tokens = tokens_a.intersection(tokens_b)
    synonym_matches = 0
    for cluster in synonym_clusters:
        if tokens_a.intersection(cluster) and tokens_b.intersection(cluster):
            synonym_matches += 1

    if shared_tokens and synonym_matches:
        base_score = 0.85 + (len(shared_tokens) / max(len(tokens_a), len(tokens_b))) * 0.10
        return min(0.99, round(base_score, 4))

    # Token overlap Jaccard
    union = tokens_a.union(tokens_b)
    jaccard = len(shared_tokens) / len(union) if union else 0.0

    if synonym_matches > 0:
        return min(0.80, round(0.50 + (jaccard * 0.3), 4))

    return round(min(0.30, jaccard * 0.5), 4)


class MockSimilarityEvaluatorRunner(IModelRunner):
    """Explicit test and offline mock runner for Model 2 (ML-002)."""

    def __init__(self, version: str = "1.0.0-mock"):
        self._version = version
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("Loaded MOCK Model 2 (Similarity Evaluator)")

    def unload(self) -> None:
        self._loaded = False
        logger.info("Unloaded MOCK Model 2 (Similarity Evaluator)")

    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def is_mock(self) -> bool:
        return True

    @property
    def version(self) -> str:
        return self._version

    def evaluate_pair(self, text_a: str, text_b: str) -> float:
        """Compute semantic similarity between two texts."""
        if not self.is_loaded():
            self.load()
        return _compute_mock_similarity(text_a, text_b)

    def evaluate_batch(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """Compute semantic similarity across a batch of text pairs."""
        return [self.evaluate_pair(a, b) for a, b in pairs]


class SimilarityEvaluatorRunner(IModelRunner):
    """Production runner executing ONNX Runtime bi-encoder session."""

    def __init__(self, artifact_dir: Path, version: str = "1.0.0"):
        self.artifact_dir = artifact_dir
        self._version = version
        self._session = None
        self._tokenizer = None

    def load(self) -> None:
        """Verify integrity and load ONNX Runtime session."""
        manifest_path = self.artifact_dir / "manifest.json"
        manifest = load_manifest(manifest_path)
        verify_artifact_integrity(manifest, self.artifact_dir)

        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer

            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = 4
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            onnx_path = self.artifact_dir / "model.onnx"
            self._session = ort.InferenceSession(
                str(onnx_path),
                sess_options,
                providers=["CPUExecutionProvider"],
            )
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.artifact_dir))
            logger.info("Successfully loaded verified Model 2 from %s", self.artifact_dir)
        except ImportError as err:
            raise RuntimeError(
                f"Required ONNX / Tokenizer dependencies missing: {err}. "
                "Ensure onnxruntime and transformers are installed."
            ) from err

    def unload(self) -> None:
        self._session = None
        self._tokenizer = None
        logger.info("Unloaded Model 2 from memory")

    def is_loaded(self) -> bool:
        return self._session is not None and self._tokenizer is not None

    @property
    def is_mock(self) -> bool:
        return False

    @property
    def version(self) -> str:
        return self._version

    def evaluate_pair(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts via ONNX bi-encoder."""
        results = self.evaluate_batch([(text_a, text_b)])
        return results[0]

    def _embed_text(self, text: str) -> "np.ndarray":
        """Compute normalized dense embedding for a single text using batch size 1."""
        import numpy as np

        encoded = self._tokenizer(
            text,
            truncation=True,
            max_length=128,
            return_tensors="np",
        )
        ort_inputs = {
            "input_ids": encoded["input_ids"],
            "attention_mask": encoded["attention_mask"],
        }
        input_names = [inp.name for inp in self._session.get_inputs()]
        if "token_type_ids" in input_names:
            ort_inputs["token_type_ids"] = encoded.get(
                "token_type_ids",
                np.zeros_like(encoded["input_ids"]),
            )

        outputs = self._session.run(None, ort_inputs)
        # Apply mean pooling over token embeddings
        token_embeddings = outputs[0]  # shape: (1, seq_len, hidden_dim)
        attention_mask = encoded["attention_mask"]
        input_mask_expanded = np.broadcast_to(
            np.expand_dims(attention_mask, -1),
            token_embeddings.shape,
        )
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask

        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / np.clip(norms, a_min=1e-9, a_max=None)
        return normalized[0]

    def evaluate_batch(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """Execute forward passes and compute cosine similarity with embedding caching."""
        if not pairs:
            return []

        if not self.is_loaded():
            self.load()

        import numpy as np

        embedding_cache: Dict[str, np.ndarray] = {}
        for text_a, text_b in pairs:
            if text_a not in embedding_cache:
                embedding_cache[text_a] = self._embed_text(text_a)
            if text_b not in embedding_cache:
                embedding_cache[text_b] = self._embed_text(text_b)

        results: List[float] = []
        for text_a, text_b in pairs:
            emb_a = embedding_cache[text_a]
            emb_b = embedding_cache[text_b]
            sim = float(np.dot(emb_a, emb_b))
            results.append(float(np.clip(sim, 0.0, 1.0)))

        return results
