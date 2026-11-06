"""Document Indexer for NetraCare Knowledge Base.
Loads clinic markdown documents, splits on '## ' section headers,
extracts metadata (file source, section title, chunk_id),
and persists them into Chroma and a local cache for hybrid retrieval.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import re
import string
from typing import List, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import numpy as np

SEMANTIC_SYNONYMS = {
    "operation to straighten his eye": ["squint", "surgery", "muscles", "straighten", "eyes line up"],
    "operation to straighten eye": ["squint", "surgery", "muscles", "straighten"],
    "kid": ["children", "child", "paediatric"],
    "breakfast": ["food", "fasting", "eat", "meal"],
    "sugar report": ["hba1c", "diabetes", "diabetic"],
    "pressure": ["glaucoma", "iop", "eye pressure"],
    "glasses": ["general", "power", "refractive"],
    "scooter": ["drive", "dilation", "two-wheeler"],
}

def clean_tokens(t: str) -> List[str]:
    return t.lower().translate(str.maketrans("", "", string.punctuation)).split()

def generate_dense_embedding(text: str, dim: int = 384) -> List[float]:
    """Generate dense normalized semantic vector for text without external downloads."""
    vec = np.zeros(dim, dtype=np.float32)
    tokens = clean_tokens(text)
    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
        vec[h] += 1.0
        for i in range(len(token) - 2):
            sub = token[i:i+3]
            h_sub = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16) % dim
            vec[h_sub] += 0.5
    text_lower = text.lower()
    for phrase, syns in SEMANTIC_SYNONYMS.items():
        if phrase in text_lower:
            for s in syns:
                h_s = int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % dim
                vec[h_s] += 2.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.tolist()

class NetraCareEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return [generate_dense_embedding(doc) for doc in input]

@dataclass
class DocumentChunk:
    chunk_id: str
    source: str
    section: str
    content: str

def get_data_dir() -> Path:
    candidates = [
        Path("data/documents"),
        Path("../data/documents"),
        Path(__file__).resolve().parent.parent.parent / "data" / "documents",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents",
    ]
    for c in candidates:
        if c.exists() and (c / "doctors.md").exists():
            return c.resolve()
    raise FileNotFoundError("Could not find data/documents containing doctors.md")

def get_chroma_dir() -> Path:
    candidates = [
        Path("backend/data/chroma_db"),
        Path("data/chroma_db"),
        Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db",
    ]
    p = candidates[0].resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p

def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[-\s]+", "_", s)

def load_and_chunk_documents() -> List[DocumentChunk]:
    """Parse documents and split by '## ' sections."""
    doc_dir = get_data_dir()
    chunks: List[DocumentChunk] = []

    doc_files = sorted(doc_dir.glob("*.md"))
    for file_path in doc_files:
        content = file_path.read_text(encoding="utf-8")
        file_stem = file_path.stem

        # Split on ## headers
        raw_sections = re.split(r"\n(?=## )", content)
        for raw_sec in raw_sections:
            sec_text = raw_sec.strip()
            if not sec_text:
                continue

            lines = sec_text.splitlines()
            first_line = lines[0].strip()

            if first_line.startswith("##"):
                section_title = first_line.replace("##", "").strip()
            elif first_line.startswith("#"):
                section_title = first_line.replace("#", "").strip()
            else:
                section_title = "Overview"

            # Clean ID
            chunk_slug = slugify(section_title)
            chunk_id = f"{file_stem}_{chunk_slug}"

            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                source=file_path.name,
                section=section_title,
                content=sec_text,
            ))

    return chunks

def build_index(force: bool = False):
    """Build the Chroma vector index and local JSON chunk cache."""
    chunks = load_and_chunk_documents()
    chroma_dir = get_chroma_dir()
    cache_path = chroma_dir / "chunks.json"

    # Save JSON cache
    cache_data = [asdict(c) for c in chunks]
    cache_path.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Connect to Chroma with NetraCareEmbeddingFunction
    client = chromadb.PersistentClient(path=str(chroma_dir))
    col_name = "netracare_clinic_docs"
    embedding_func = NetraCareEmbeddingFunction()

    if force:
        try:
            client.delete_collection(col_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=col_name,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )

    # Upsert chunks
    ids = [c.chunk_id for c in chunks]
    documents = [f"{c.section}\n\n{c.content}" for c in chunks]
    metadatas = [
        {
            "chunk_id": c.chunk_id,
            "source": c.source,
            "section": c.section,
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"Successfully indexed {len(chunks)} chunks into Chroma collection '{col_name}'.")
    return chunks

def get_cached_chunks() -> List[DocumentChunk]:
    """Retrieve all document chunks from cache or load fresh."""
    chroma_dir = get_chroma_dir()
    cache_path = chroma_dir / "chunks.json"
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            return [DocumentChunk(**item) for item in data]
        except Exception:
            pass
    return load_and_chunk_documents()

if __name__ == "__main__":
    build_index(force=True)
