"""
Audit trail: writes a companion JSON for every generated report.
Required for 21 CFR Part 11 electronic record traceability.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self, config: dict):
        self.config = config

    def write(
        self,
        event: dict,
        sections: dict,
        passages: list,
        doc_path: Path,
    ) -> Path:
        audit = {
            "audit_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "model": self.config["llm"]["model"],
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "batch_number": event.get("batch_number"),
            "report_file": str(doc_path),
            "llm_config": {
                "model": self.config["llm"]["model"],
                "temperature": self.config["llm"]["temperature"],
                "max_tokens": self.config["llm"]["max_tokens"],
            },
            "retrieval_config": {
                "top_k": self.config["retrieval"]["top_k"],
                "embedding_model": self.config["retrieval"]["embedding_model"],
            },
        }

        if self.config["audit"].get("include_retrieved_chunks"):
            audit["retrieved_passages"] = [
                {"source": p.source, "score": round(p.score, 4), "text": p.text[:200]}
                for p in passages
            ]

        if self.config["audit"].get("include_prompt_versions"):
            audit["section_lengths"] = {
                k: len(v) for k, v in sections.items()
            }

        audit_path = doc_path.with_suffix(".audit.json")
        with open(audit_path, "w") as f:
            json.dump(audit, f, indent=2, default=str)

        logger.info(f"Audit trail written: {audit_path}")
        return audit_path
