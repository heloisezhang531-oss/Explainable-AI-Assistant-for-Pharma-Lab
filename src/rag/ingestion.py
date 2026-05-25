"""
Knowledge base ingestion: PDF chunking, embedding, and ChromaDB upsert.

Run via:  python scripts/build_kb.py
"""
from __future__ import annotations
import hashlib
import logging
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import PyPDF2

logger = logging.getLogger(__name__)

SUPPORTED_SOURCES = [
    # Download these manually — see docs/knowledge_sources.md
    "fda_oos_guidance_2006.pdf",       # FDA: Investigating OOS Test Results
    "ich_q10_pharmaceutical_quality.pdf",
    "ich_q9_quality_risk_management.pdf",
    "21_cfr_211_subpart_j.pdf",        # Current Good Manufacturing Practice
    "eu_gmp_chapter6_qc.pdf",
]


class KnowledgeBaseBuilder:
    def __init__(self, config: dict):
        self.config = config
        ef = SentenceTransformerEmbeddingFunction(
            model_name=config["retrieval"]["embedding_model"]
        )
        client = chromadb.PersistentClient(
            path=config.get("chroma_db_path", "./data/knowledge_base")
        )
        self.collection = client.get_or_create_collection(
            name=config["retrieval"]["collection_name"],
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

    def ingest_directory(self, pdf_dir: Path) -> int:
        """Ingest all PDFs in directory. Returns total chunks added."""
        total = 0
        for pdf_path in sorted(pdf_dir.glob("*.pdf")):
            logger.info(f"Ingesting: {pdf_path.name}")
            chunks = self._chunk_pdf(pdf_path)
            self._upsert_chunks(chunks, source=pdf_path.name)
            total += len(chunks)
            logger.info(f"  -> {len(chunks)} chunks")
        return total

    def _chunk_pdf(self, path: Path) -> list[dict]:
        """Extract text and split into overlapping chunks."""
        chunk_size = self.config["retrieval"]["chunk_size"]
        overlap = self.config["retrieval"]["chunk_overlap"]

        reader = PyPDF2.PdfReader(str(path))
        full_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        )
        words = full_text.split()

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            chunk_id = hashlib.md5(
                f"{path.name}:{start}".encode()
            ).hexdigest()
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "metadata": {
                    "source": path.name,
                    "chunk_start": start,
                    "chunk_end": end,
                },
            })
            start += chunk_size - overlap

        return chunks

    def _upsert_chunks(self, chunks: list[dict], source: str) -> None:
        if not chunks:
            return
        self.collection.upsert(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks],
        )
