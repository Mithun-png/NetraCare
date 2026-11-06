"""Hybrid Retriever combining BM25 keyword search and Vector similarity.
Implements:
1. BM25 with text lowercasing and punctuation stripping (e.g. 'Menon?' matches 'Menon')
2. Vector search using Chroma with NetraCareEmbeddingFunction
3. Hybrid rank fusion (equal 50/50 weighting) returning top 4 chunks
4. Staff search-debug view reporting keyword, vector, and hybrid top-4 results
"""
from dataclasses import dataclass
import string
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
import numpy as np
import chromadb

from app.rag.indexer import (
    get_cached_chunks,
    DocumentChunk,
    get_chroma_dir,
    clean_tokens,
    NetraCareEmbeddingFunction,
    generate_dense_embedding,
)

class BM25Retriever:
    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        self.corpus = [
            clean_tokens(f"{c.source} {c.section} {c.content}")
            for c in self.chunks
        ]
        self.bm25 = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunk, float]]:
        tokens = clean_tokens(query)
        if not tokens:
            return [(c, 0.0) for c in self.chunks[:top_k]]
        scores = self.bm25.get_scores(tokens)
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.chunks[i], float(scores[i])) for i in sorted_indices]

class VectorRetriever:
    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        self.chroma_dir = get_chroma_dir()
        self.collection = None
        self._init_chroma()

    def _init_chroma(self):
        try:
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            embedding_func = NetraCareEmbeddingFunction()
            self.collection = client.get_collection(
                name="netracare_clinic_docs",
                embedding_function=embedding_func,
            )
        except Exception:
            self.collection = None

    def search(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunk, float]]:
        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=min(top_k, len(self.chunks)),
                )
                if results and results["ids"] and len(results["ids"][0]) > 0:
                    matched_ids = results["ids"][0]
                    distances = results["distances"][0] if results.get("distances") else [0.0] * len(matched_ids)
                    id_to_chunk = {c.chunk_id: c for c in self.chunks}
                    ret = []
                    for cid, dist in zip(matched_ids, distances):
                        chunk = id_to_chunk.get(cid)
                        if chunk:
                            sim = max(0.0, 1.0 - dist)
                            ret.append((chunk, float(sim)))
                    if ret:
                        return ret
            except Exception:
                pass

        # Fallback dense calculation directly with NetraCareEmbeddingFunction
        q_vec = np.array(generate_dense_embedding(query), dtype=np.float32)
        scores = []
        for c in self.chunks:
            c_vec = np.array(generate_dense_embedding(f"{c.section} {c.content}"), dtype=np.float32)
            sim = float(np.dot(q_vec, c_vec))
            scores.append(sim)

        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.chunks[i], float(scores[i])) for i in sorted_indices]

class HybridRetriever:
    def __init__(self):
        self.chunks = get_cached_chunks()
        self.bm25_retriever = BM25Retriever(self.chunks)
        self.vector_retriever = VectorRetriever(self.chunks)

    def search(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunk, float]]:
        """Combine BM25 and Vector search with equal 50/50 weighting."""
        bm25_results = self.bm25_retriever.search(query, top_k=len(self.chunks))
        vector_results = self.vector_retriever.search(query, top_k=len(self.chunks))

        # Normalize BM25 scores to [0, 1]
        bm25_max = max([s for _, s in bm25_results], default=1.0) or 1.0
        bm25_scores = {c.chunk_id: (s / bm25_max) for c, s in bm25_results}

        # Normalize Vector scores to [0, 1]
        vec_max = max([s for _, s in vector_results], default=1.0) or 1.0
        vector_scores = {c.chunk_id: (s / vec_max) for c, s in vector_results}

        # Equal weight combination (alpha = 0.5)
        combined: Dict[str, float] = {}
        for c in self.chunks:
            cid = c.chunk_id
            b_score = bm25_scores.get(cid, 0.0)
            v_score = vector_scores.get(cid, 0.0)
            combined[cid] = 0.5 * b_score + 0.5 * v_score

        # Sort descending
        sorted_cids = sorted(combined.keys(), key=lambda k: combined[k], reverse=True)[:top_k]
        id_to_chunk = {c.chunk_id: c for c in self.chunks}
        return [(id_to_chunk[cid], combined[cid]) for cid in sorted_cids]

    def search_debug(self, query: str, top_k: int = 4) -> Dict[str, Any]:
        """Return side-by-side keyword, vector, and hybrid top-4 results for Staff."""
        bm25_results = self.bm25_retriever.search(query, top_k=top_k)
        vector_results = self.vector_retriever.search(query, top_k=top_k)
        hybrid_results = self.search(query, top_k=top_k)

        def format_results(res_list):
            return [
                {
                    "chunk_id": chunk.chunk_id,
                    "source": chunk.source,
                    "section": chunk.section,
                    "score": round(score, 4),
                    "snippet": chunk.content[:200] + ("..." if len(chunk.content) > 200 else ""),
                }
                for chunk, score in res_list
            ]

        return {
            "query": query,
            "keyword": format_results(bm25_results),
            "vector": format_results(vector_results),
            "hybrid": format_results(hybrid_results),
        }

_hybrid_retriever: HybridRetriever | None = None

def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever

def reset_retriever():
    global _hybrid_retriever
    _hybrid_retriever = None
