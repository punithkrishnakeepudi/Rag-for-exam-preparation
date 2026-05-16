from examlens.api.retrieval import split_into_chunks, extract_keywords


def test_chunking_splits_paragraphs():
    text = "A\n\nB\n\nC"
    chunks = split_into_chunks(text, chunk_size=10, overlap=2)
    assert chunks == ["A", "B", "C"]


def test_keywords():
    kws = extract_keywords("Photosynthesis converts light energy into chemical energy", 3)
    assert len(kws) == 3

