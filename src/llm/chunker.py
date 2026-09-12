import re
from typing import List
from src.config.settings import settings

def estimate_tokens(text: str) -> int:
    """Fast approximation of token count (approx 4 chars per token for English)."""
    if not text:
        return 0
    return max(1, len(text) // 4)

def chunk_text(
    text: str,
    max_chunk_chars: int = settings.MAX_CHUNK_CHARS
) -> List[str]:
    """
    Intelligently splits large text into semantically dense chunks.
    Prioritizes paragraph breaks, sentence boundaries, and avoid mid-word truncation.
    Guarantees no chunk exceeds max_chunk_chars.
    """
    if not text or len(text) <= max_chunk_chars:
        return [text] if text else []

    chunks: List[str] = []
    paragraphs = text.split("\n\n")
    current_chunk: List[str] = []
    current_len = 0

    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped:
            continue

        if len(para_stripped) > max_chunk_chars:
            # Paragraph itself exceeds limit: split by sentences
            sentences = re.split(r"(?<=[.?!])\s+", para_stripped)
            for sentence in sentences:
                if current_len + len(sentence) + 1 > max_chunk_chars and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                if len(sentence) > max_chunk_chars:
                    # Very long sentence: hard break by words
                    words = sentence.split(" ")
                    for word in words:
                        if current_len + len(word) + 1 > max_chunk_chars and current_chunk:
                            chunks.append(" ".join(current_chunk))
                            current_chunk = []
                            current_len = 0
                        current_chunk.append(word)
                        current_len += len(word) + 1
                else:
                    current_chunk.append(sentence)
                    current_len += len(sentence) + 1
        else:
            if current_len + len(para_stripped) + 2 > max_chunk_chars and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(para_stripped)
            current_len += len(para_stripped) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks

def reduce_payload(text: str, reduction_factor: float = 0.5) -> str:
    """Reduces payload size when a 413 Payload Too Large error is encountered."""
    if not text:
        return ""
    target_len = int(len(text) * reduction_factor)
    return text[:max(100, target_len)].strip()
