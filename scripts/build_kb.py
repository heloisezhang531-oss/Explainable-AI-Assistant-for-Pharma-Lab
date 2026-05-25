"""
One-time script: ingest all PDFs in data/raw/ into the ChromaDB knowledge base.

Usage:
    python scripts/build_kb.py
    python scripts/build_kb.py --data-dir /path/to/pdfs
"""
import argparse
import logging
from pathlib import Path
import sys
sys.path.insert(0, ".")

import yaml

from src.rag.ingestion import KnowledgeBaseBuilder
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/raw",
                        help="Directory containing regulatory PDF files")
    parser.add_argument("--config", default="configs/settings.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    pdf_dir = Path(args.data_dir)
    if not pdf_dir.exists():
        logger.error(f"Data directory not found: {pdf_dir}")
        logger.info("Create data/raw/ and add FDA/ICH PDFs. See docs/knowledge_sources.md")
        sys.exit(1)

    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found. See docs/knowledge_sources.md for sources.")
        sys.exit(0)

    logger.info(f"Found {len(pdfs)} PDF(s) in {pdf_dir}")
    builder = KnowledgeBaseBuilder(config)
    total = builder.ingest_directory(pdf_dir)
    logger.info(f"Knowledge base ready. Total chunks: {total}")


if __name__ == "__main__":
    main()
