"""
End-to-end pipeline: event → retrieved context → LLM sections → docx report.
"""
from __future__ import annotations
import logging
from pathlib import Path

import anthropic
import yaml

from src.pipeline.event_parser import parse_event, enrich_event
from src.rag.retriever import Retriever
from src.rag.prompts import (
    SYSTEM_PROMPT,
    build_phase1_prompt,
    build_phase2_prompt,
    build_capa_prompt,
    build_conclusion_prompt,
)
from src.report.builder import ReportBuilder
from src.utils.audit import AuditLogger

logger = logging.getLogger(__name__)


def load_config(path: str = "configs/settings.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class InvestigationPipeline:
    def __init__(self, config_path: str = "configs/settings.yaml"):
        self.config = load_config(config_path)
        self.client = anthropic.Anthropic()
        self.retriever = Retriever(self.config)
        self.audit = AuditLogger(self.config)

    def run(self, raw_event: dict, output_dir: str | None = None) -> Path:
        """
        Full pipeline run.

        Parameters
        ----------
        raw_event : dict
            Raw LIMS event dict (validated by LIMSEvent schema)
        output_dir : str, optional
            Override default output directory from config

        Returns
        -------
        Path to generated .docx file
        """
        # 1. Parse & enrich
        event = enrich_event(parse_event(raw_event))
        logger.info(f"Processing event {event['event_id']} ({event['event_type']})")

        # 2. Retrieve regulatory context (multiple targeted queries)
        queries = [
            f"{event['event_type']} investigation {event['parameter']}",
            f"Phase I laboratory investigation OOS analyst error",
            f"CAPA corrective preventive action pharmaceutical quality",
            f"21 CFR 211 out of specification investigation requirements",
        ]
        all_passages = []
        for q in queries:
            all_passages.extend(self.retriever.query(q, top_k=3))
        # Deduplicate by text
        seen, unique_passages = set(), []
        for p in all_passages:
            if p.text not in seen:
                seen.add(p.text)
                unique_passages.append(p)

        context = self.retriever.format_context(unique_passages[:8])

        # 3. Generate report sections via LLM
        sections = {}

        sections["phase1"] = self._call_llm(
            build_phase1_prompt(event, context)
        )
        sections["phase2"] = self._call_llm(
            build_phase2_prompt(event, context, sections["phase1"])
        )
        sections["capa"] = self._call_llm(
            build_capa_prompt(
                event,
                root_cause="To be determined pending Phase II completion",
                context=context,
            )
        )
        sections["conclusion"] = self._call_llm(
            build_conclusion_prompt(
                event,
                root_cause="Pending",
                impact="Under assessment",
            )
        )

        # 4. Build Word report
        builder = ReportBuilder(self.config)
        out_dir = Path(output_dir or self.config["report"]["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        doc_path = builder.build(event, sections, out_dir)

        # 5. Write audit trail
        self.audit.write(event, sections, unique_passages, doc_path)

        logger.info(f"Report generated: {doc_path}")
        return doc_path

    def _call_llm(self, user_prompt: str) -> str:
        """Single LLM call with the shared system prompt."""
        msg = self.client.messages.create(
            model=self.config["llm"]["model"],
            max_tokens=self.config["llm"]["max_tokens"],
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text
