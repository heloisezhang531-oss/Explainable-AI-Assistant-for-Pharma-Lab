"""Tests for the retriever (uses in-memory ChromaDB)."""
import pytest
from unittest.mock import MagicMock, patch

CONFIG = {
    "retrieval": {
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 3,
        "chunk_size": 512,
        "chunk_overlap": 64,
        "collection_name": "test_collection",
    },
    "chroma_db_path": ":memory:",
}


def test_format_context():
    from src.rag.retriever import Retriever, RetrievedPassage
    with patch("chromadb.PersistentClient"),          patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction"):
        retriever = Retriever(CONFIG)
        passages = [
            RetrievedPassage(text="FDA requires thorough OOS investigation.", source="fda_oos.pdf", score=0.92),
            RetrievedPassage(text="Phase I must precede Phase II.", source="ich_q10.pdf", score=0.85),
        ]
        context = retriever.format_context(passages)
        assert "SOURCE 1" in context
        assert "fda_oos.pdf" in context
        assert "0.92" in context
