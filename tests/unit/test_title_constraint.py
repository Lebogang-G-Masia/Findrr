"""Tests for ML-001 constrained decoding (D-007): only real, non-repeated titles can be produced."""

from findrr.ml.title_constraint import TitleTrieConstraint

PAD, EOS, COMMA = 0, 1, 2


class WordTokenizer:
    """Fake tokenizer: one id per word, ',' is its own token; 'X3,' merges like T5's '3,'."""

    pad_token_id, eos_token_id = PAD, EOS

    def __init__(self):
        self.vocab = {",": COMMA}

    def _id(self, word):
        return self.vocab.setdefault(word, len(self.vocab) + 10)

    def convert_tokens_to_ids(self, tok):
        return self.vocab[tok]

    def __call__(self, text, add_special_tokens=False):
        ids = []
        for word in text.replace(",", " , ").split():
            ids.append(COMMA if word == "," else self._id(word))
        if text.endswith("X3,"):  # simulate a piece that swallows the separator
            ids = ids[:-2] + [self._id("X3,")]
        return {"input_ids": ids}

    def decode(self, ids, skip_special_tokens=True):
        inv = {v: k for k, v in self.vocab.items()}
        return " ".join(inv[i] for i in ids if i not in (PAD, EOS))


TITLES = ["Software Engineer", "Software Developer", "Web Developer", "Nurse",
          "Manager, Sales", "Track X3"]


def _ids(tok, text):
    return tok(text)["input_ids"]


def test_dictionary_build_skips_comma_and_merging_titles():
    tok = WordTokenizer()
    c = TitleTrieConstraint(TITLES, tok)
    assert "Manager, Sales" in c.skipped and "Track X3" in c.skipped
    assert set(c.titles) == {"Software Engineer", "Software Developer", "Web Developer", "Nurse"}


def test_only_dictionary_continuations_are_allowed():
    tok = WordTokenizer()
    c = TitleTrieConstraint(TITLES, tok)
    start = set(c.allowed_tokens([]))
    assert start == {_ids(tok, "Software")[0], _ids(tok, "Web")[0], _ids(tok, "Nurse")[0]}
    after_software = set(c.allowed_tokens(_ids(tok, "Software")))
    assert after_software == {_ids(tok, "Engineer")[0], _ids(tok, "Developer")[0]}
    # A complete title may be followed by a separator or the end of the output.
    assert set(c.allowed_tokens(_ids(tok, "Nurse"))) == {COMMA, EOS}


def test_repeat_cannot_even_be_started():
    """Regression (Kaggle run 2, repetition 0.28): a repeat used to be spelled out in full and
    then forced to end the output. A branch is now closed once all its titles are used."""
    tok = WordTokenizer()
    c = TitleTrieConstraint(TITLES, tok)
    after_nurse = c.allowed_tokens(_ids(tok, "Nurse") + [COMMA])
    assert _ids(tok, "Nurse")[0] not in after_nurse
    # 'Software' stays open while one of its two titles is unused...
    one = _ids(tok, "Software Engineer") + [COMMA]
    assert _ids(tok, "Software")[0] in c.allowed_tokens(one)
    assert set(c.allowed_tokens(one + _ids(tok, "Software"))) == {_ids(tok, "Developer")[0]}
    # ...and closes once both are used.
    both = one + _ids(tok, "Software Developer") + [COMMA]
    assert _ids(tok, "Software")[0] not in c.allowed_tokens(both)


def test_greedy_walk_never_repeats():
    """Always taking the first allowed token must terminate with distinct titles only."""
    tok = WordTokenizer()
    c = TitleTrieConstraint(TITLES, tok)
    seq = []
    for _ in range(50):
        nxt = sorted(c.allowed_tokens(seq), key=lambda t: (t in (EOS,), t))[0]
        seq.append(nxt)
        if nxt == EOS:
            break
    titles = c.complete_titles(seq, tok)
    assert len(titles) == len(set(titles)) == 4


def test_max_titles_forces_end():
    tok = WordTokenizer()
    c = TitleTrieConstraint(TITLES, tok, max_titles=2)
    seq = _ids(tok, "Nurse") + [COMMA] + _ids(tok, "Web Developer")
    assert set(c.allowed_tokens(seq)) == {EOS}


def test_complete_titles_drops_partial_and_duplicate_segments():
    tok = WordTokenizer()
    c = TitleTrieConstraint(TITLES, tok)
    seq = (_ids(tok, "Nurse") + [COMMA] + _ids(tok, "Nurse") + [COMMA]
           + _ids(tok, "Web Developer") + [COMMA] + _ids(tok, "Software"))  # cut off
    assert c.complete_titles([PAD] + seq + [EOS], tok) == ["Nurse", "Web Developer"]


def test_prefix_fn_strips_decoder_start_and_accepts_lists():
    tok = WordTokenizer()
    c = TitleTrieConstraint(TITLES, tok)
    fn = c.prefix_allowed_tokens_fn(decoder_start_token_id=PAD)
    assert set(fn(0, [PAD] + _ids(tok, "Nurse"))) == {COMMA, EOS}
    assert set(fn(0, [PAD, EOS])) == {PAD, EOS}
