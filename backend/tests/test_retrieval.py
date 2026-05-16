from examlens.api.retrieval import split_into_chunks, extract_keywords


def test_chunking_splits_paragraphs():
    text = "A\n\nB\n\nC"
    # The current implementation joins paragraphs if they fit in chunk_size.
    # With chunk_size=10, "A\n\nB\n\nC" has length 7, so it stays as one chunk.
    # Let's use a smaller chunk_size to force a split.
    chunks = split_into_chunks(text, chunk_size=2, overlap=0)
    assert chunks == ["A", "B", "C"]


def test_keywords():
    kws = extract_keywords("Photosynthesis converts light energy into chemical energy", 3)
    assert len(kws) == 3

