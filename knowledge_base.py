from io import BytesIO
from pathlib import Path
import re

CHUNK_SIZE = 1100
CHUNK_OVERLAP = 180

def _extract_text(file_bytes: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import fitz
        pages = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text").strip()
                if text:
                    pages.append(f"[Page {i+1}]\n{text}")
        if not pages:
            raise ValueError("No selectable text was found in this PDF. It may be scanned; run OCR or provide a text-based PDF.")
        return "\n\n".join(pages)
    if suffix in {".txt", ".md"}:
        return file_bytes.decode("utf-8", errors="replace")
    if suffix == ".docx":
        from docx import Document
        doc = Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    raise ValueError("Unsupported file type. Upload PDF, TXT, MD, or DOCX.")

def _chunk_text(text: str, filename: str):
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    # Split into paragraphs first, then combine into manageable chunks.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= CHUNK_SIZE:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > CHUNK_SIZE:
                start = 0
                while start < len(para):
                    chunks.append(para[start:start + CHUNK_SIZE])
                    start += CHUNK_SIZE - CHUNK_OVERLAP
                current = ""
            else:
                current = para
    if current:
        chunks.append(current)
    return [
        {"text": chunk, "source": filename, "chunk": i + 1}
        for i, chunk in enumerate(chunks)
    ]

def build_knowledge_base(file_bytes: bytes, filename: str):
    text = _extract_text(file_bytes, filename)
    chunks = _chunk_text(text, filename)
    if not chunks:
        raise ValueError("No usable text was extracted from the document.")
    return chunks, filename

def retrieve_context(question: str, chunks, top_k: int = 5) -> str:
    """Use local sentence-transformer embeddings + FAISS when available; lexical fallback otherwise."""
    if not chunks:
        return ""
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        texts = [c["text"] for c in chunks]
        embeddings = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype("float32")
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        q = model.encode([question], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
        scores, ids = index.search(q, min(top_k, len(chunks)))
        selected = [(float(score), int(idx)) for score, idx in zip(scores[0], ids[0]) if idx >= 0]
        selected.sort(reverse=True)
        return "\n\n".join(
            f"[Source: {chunks[idx]['source']} | section {chunks[idx]['chunk']}]\n{chunks[idx]['text']}"
            for score, idx in selected
        )
    except Exception:
        # Basic lexical retrieval avoids breaking the app if model download/indexing fails.
        words = {w.lower() for w in re.findall(r"[A-Za-z0-9_+-]{3,}", question)}
        scored = []
        for i, chunk in enumerate(chunks):
            body = chunk["text"].lower()
            score = sum(body.count(word) for word in words)
            scored.append((score, i))
        selected = [i for score, i in sorted(scored, reverse=True)[:top_k] if score > 0]
        if not selected:
            selected = list(range(min(top_k, len(chunks))))
        return "\n\n".join(
            f"[Source: {chunks[idx]['source']} | section {chunks[idx]['chunk']}]\n{chunks[idx]['text']}"
            for idx in selected
        )
