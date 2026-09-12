import pytest
from src.llm.chunker import estimate_tokens, chunk_text, reduce_payload
from src.extraction.html_cleaner import clean_html, extract_evidence_snippet

def test_estimate_tokens():
    text = "Hello world from the AI extraction pipeline."
    tokens = estimate_tokens(text)
    assert tokens > 0
    assert tokens <= len(text)

def test_chunk_text_bounds():
    long_para = "This is a sentence for chunking testing. " * 50
    chunks = chunk_text(long_para, max_chunk_chars=200)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 200

def test_reduce_payload_on_413():
    text = "A" * 1000
    reduced = reduce_payload(text, reduction_factor=0.5)
    assert len(reduced) == 500

def test_clean_html_strips_scripts_and_noise():
    raw_html = """
    <html>
        <head><style>body { color: red; }</style></head>
        <body>
            <script>alert('noise');</script>
            <nav><a href="#">Nav item</a></nav>
            <div class="cookie-banner">Please accept cookies.</div>
            <h1>Article Title</h1>
            <p>Main content of the article describing the new AI model.</p>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    cleaned = clean_html(raw_html, max_chars=500)
    assert "alert('noise')" not in cleaned
    assert "cookie" not in cleaned.lower()
    assert "Main content of the article" in cleaned

def test_evidence_snippet_bounded():
    long_text = "start " + ("padding " * 100) + "target_keyword " + ("padding " * 100)
    snippet = extract_evidence_snippet(long_text, match_term="target_keyword", max_chars=100)
    assert "target_keyword" in snippet
    assert len(snippet) <= 120 # with ellipsis
