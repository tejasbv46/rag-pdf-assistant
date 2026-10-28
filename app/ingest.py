import fitz  # PyMuPDF
from app import config


def extract_pages(path):
    """Return [{'page': 1, 'text': '...'}, ...]. Page numbers are 1-based."""
    with fitz.open(path) as doc:
        return [{"page": i + 1, "text": p.get_text()} for i, p in enumerate(doc)]


def chunk_text(text, size, overlap):
    text = " ".join(text.split())  # collapse whitespace/newlines
    out, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):  # prefer to cut at a space, not mid-word
            cut = text.rfind(" ", start + size // 2, end)
            if cut != -1:
                end = cut
        piece = text[start:end].strip()
        if len(piece) >= 40:
            out.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return out


def chunk_pages(pages, doc_name, size=None, overlap=None):
    """Chunk each page separately so a chunk never spans two pages (accurate citations)."""
    size = size or config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP if overlap is None else overlap
    chunks = []
    for p in pages:
        for piece in chunk_text(p["text"], size, overlap):
            chunks.append({"text": piece, "doc": doc_name, "page": p["page"]})
    return chunks
