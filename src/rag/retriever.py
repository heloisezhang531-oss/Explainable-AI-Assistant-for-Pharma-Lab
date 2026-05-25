"""
Semantic retriever: query the ChromaDB knowledge base and return ranked passages.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

logger = logging.getLogger(__name__)


@dataclass
class RetrievedPassage:
    text: str
    source: str
    score: float  # cosine similarity (higher = more relevant)


class Retriever:
    def __init__(self, config: dict):
        ef = SentenceTransformerEmbeddingFunction(
            model_name=config["retrieval"]["embedding_model"]
        )
        client = chromadb.PersistentClient(
            path=config.get("chroma_db_path", "./data/knowledge_base")
        )
        self.collection = client.get_or_create_collection(
            name=config["retrieval"]["collection_name"],
            embedding_function=ef,
        )
        self.top_k = config["retrieval"]["top_k"]

    def query(self, query_text: str, top_k: int | None = None) -> list[RetrievedPassage]:
        k = top_k or self.top_k
        results = self.collection.query(
            query_texts=[query_text],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        passages = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            passages.append(RetrievedPassage(
                text=doc,
                source=meta.get("source", "unknown"),
                score=1.0 - dist,  # convert distance to similarity
            ))
        logger.debug(f"Retrieved {len(passages)} passages for: {query_text[:60]}")
        return passages

    def format_context(self, passages: list[RetrievedPassage]) -> str:
        """Format passages into a single context block for the LLM prompt."""
        blocks = []
        for i, p in enumerate(passages, 1):
            blocks.append(
                f"[SOURCE {i}: {p.source} | similarity={p.score:.2f}]\n{p.text}"
            )
        return "\n\n---\n\n".join(blocks)
