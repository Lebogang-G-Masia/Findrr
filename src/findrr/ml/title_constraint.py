"""Constrained decoding for ML-001: generate only real titles from a fixed dictionary (D-007).

The model's output format is ``"Title A, Title B, Title C"``. A token trie over the dictionary
restricts every title segment to a known title, separated by the comma token, and a title that
has already been generated cannot be completed again. Invented and repeated titles are therefore
impossible by construction.

This module is pure Python (no torch import) and is used verbatim by both the Findrr runner
and ``notebooks/01_train_title_expander.ipynb`` (the notebook generator embeds this file's
source), so training-time evaluation and app inference use the same constraint.
"""

from typing import Dict, Iterable, List, Optional, Sequence, Tuple


class _Node:
    __slots__ = ("children", "terminal")

    def __init__(self) -> None:
        self.children: Dict[int, "_Node"] = {}
        self.terminal = False


class TitleTrieConstraint:
    """Token-level trie over dictionary titles, usable as ``prefix_allowed_tokens_fn``."""

    def __init__(
        self,
        titles: Iterable[str],
        tokenizer,
        max_titles: Optional[int] = None,
    ) -> None:
        self.comma_id = tokenizer.convert_tokens_to_ids(",")
        self.eos_id = tokenizer.eos_token_id
        self.pad_id = tokenizer.pad_token_id
        self.max_titles = max_titles
        self.root = _Node()
        self.titles: List[str] = []
        self.skipped: List[str] = []
        for title in titles:
            if "," in title:
                self.skipped.append(title)
                continue
            ids = list(tokenizer(title, add_special_tokens=False)["input_ids"])
            with_comma = list(tokenizer(title + ",", add_special_tokens=False)["input_ids"])
            # Skip titles whose last piece merges with the separator (e.g. '3,' in T5):
            # they could never be followed by the comma token in a real output.
            if not ids or with_comma != ids + [self.comma_id]:
                self.skipped.append(title)
                continue
            node = self.root
            for tok in ids:
                node = node.children.setdefault(tok, _Node())
            node.terminal = True
            self.titles.append(title)

    @staticmethod
    def _segments(generated: Sequence[int], comma_id: int) -> List[List[int]]:
        segments: List[List[int]] = [[]]
        for tok in generated:
            if tok == comma_id:
                segments.append([])
            else:
                segments[-1].append(tok)
        return segments

    def _walk(self, ids: Sequence[int]) -> Optional[_Node]:
        node = self.root
        for tok in ids:
            node = node.children.get(tok)
            if node is None:
                return None
        return node

    def allowed_tokens(self, generated: Sequence[int]) -> List[int]:
        """Token IDs allowed next, given the decoder tokens generated so far (no start token)."""
        if self.eos_id in generated:
            return [self.pad_id, self.eos_id]
        segments = self._segments(generated, self.comma_id)
        completed = {tuple(s) for s in segments[:-1]}
        current = segments[-1]
        node = self._walk(current)
        if node is None:
            return [self.eos_id]
        allowed = list(node.children)
        if node.terminal and tuple(current) not in completed:
            if self.max_titles is None or len(segments) < self.max_titles:
                allowed.append(self.comma_id)
            allowed.append(self.eos_id)
        return allowed or [self.eos_id]

    def prefix_allowed_tokens_fn(self, decoder_start_token_id: int):
        """Adapter for ``model.generate(prefix_allowed_tokens_fn=...)``."""

        def fn(batch_id: int, input_ids) -> List[int]:
            ids = input_ids.tolist() if hasattr(input_ids, "tolist") else list(input_ids)
            if ids and ids[0] == decoder_start_token_id:
                ids = ids[1:]
            return self.allowed_tokens(ids)

        return fn

    def complete_titles(self, generated: Sequence[int], tokenizer) -> List[str]:
        """Decode complete, distinct dictionary titles; drop a title cut off by max length."""
        ids = [t for t in generated if t not in (self.pad_id, self.eos_id)]
        out: List[str] = []
        seen: set = set()
        for seg in self._segments(ids, self.comma_id):
            node = self._walk(seg)
            key: Tuple[int, ...] = tuple(seg)
            if seg and node is not None and node.terminal and key not in seen:
                seen.add(key)
                out.append(tokenizer.decode(seg, skip_special_tokens=True).strip())
        return out
