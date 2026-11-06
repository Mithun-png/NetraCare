"""Standalone script to build or rebuild the NetraCare Knowledge Base Index."""
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.rag.indexer import build_index

if __name__ == "__main__":
    print("Building NetraCare Knowledge Base Index...")
    chunks = build_index(force=True)
    print(f"Done! Total chunks indexed: {len(chunks)}")
    for i, c in enumerate(chunks[:5], 1):
        print(f"  {i}. [{c.source}] > {c.section} (id: {c.chunk_id})")

