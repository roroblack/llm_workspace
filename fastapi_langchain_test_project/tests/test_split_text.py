from app.services.summarize_service import MAX_CHARS_PER_CHUNK, split_text


def test_short_text_stays_single_chunk():
    text = "First paragraph.\n\nSecond paragraph."
    chunks = split_text(text)
    assert chunks == ["First paragraph.\n\nSecond paragraph."]


def test_paragraphs_are_packed_up_to_max():
    para = "a" * 5000
    text = f"{para}\n\n{para}\n\n{para}"
    chunks = split_text(text, max_chars=12000)
    # 5000 + 5000 fits in one chunk (with the "\n\n" join), the third rolls over.
    assert len(chunks) == 2
    assert all(len(chunk) <= 12000 for chunk in chunks)


def test_oversized_paragraph_is_hard_split():
    text = "b" * 30000
    chunks = split_text(text, max_chars=12000)
    assert len(chunks) == 3
    assert all(len(chunk) <= 12000 for chunk in chunks)
    assert "".join(chunks) == text


def test_empty_text_returns_one_empty_chunk():
    chunks = split_text("")
    assert chunks == [""]


def test_default_max_chars_is_respected():
    text = "c" * (MAX_CHARS_PER_CHUNK * 2)
    chunks = split_text(text)
    assert all(len(chunk) <= MAX_CHARS_PER_CHUNK for chunk in chunks)
