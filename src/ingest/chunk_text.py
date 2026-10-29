
def chunk_text(text: str, chunk_size: int = 180, overlap: int = 40) -> list[str]:
    """Split text into word-based chunks with a small overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size.")

    words = text.split()
    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))

        if start + chunk_size >= len(words):
            break

    return chunks
