from backend.rsvp_tokens import split_paragraphs, tokenize_paragraphs


def test_tokenize_paragraphs_marks_punctuation():
    text = "Hello world. Next, line.\n\nNew para!"
    paragraphs = split_paragraphs(text)
    tokens = tokenize_paragraphs(paragraphs)

    assert paragraphs == ["Hello world. Next, line.", "New para!"]
    assert tokens[1]["text"] == "world"
    assert tokens[1]["punct"] == "."
    assert tokens[-1]["text"] == "para"
    assert tokens[-1]["punct"] == "!"
    assert tokens[-1]["paragraph_index"] == 1
