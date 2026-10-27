import fitz  # PyMuPDF

def extract_pages(path):
    doc = fitz.open(path)
    return [{"page": i + 1, "text": p.get_text()} for i, p in enumerate(doc)]

def chunk_pages(pages, doc_name, size=700, overlap=100):
    chunks = []
    for p in pages:
        text = p["text"]
        for start in range(0, len(text), size - overlap):
            piece = text[start:start + size].strip()
            if len(piece) > 50:
                chunks.append({"text": piece, "doc": doc_name, "page": p["page"]})
    return chunks