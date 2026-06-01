"""
End-to-end pipeline orchestrator — Phase I scope only.

Flow:
  1. Parse & enrich event (from Žagar CSV row via lims_adapter)
  2. Run SHAP on the batch row → structured anomaly summary
  3. Retrieve FDA/ICH passages via RAG
  4. LLM: generate Phase I narrative (multi-cause RCA)
  5. LLM: generate escalation recommendation
  6. Assemble Word report (.docx) + audit trail (.json)
"""
from __future__ import annotations
import json
import logging
from pathlib import Path

import anthropic
import yaml

from src.pipeline.event_parser import parse_event, enrich_event
from src.rag.retriever import Retriever
from src.rag.prompts import SYSTEM_PROMPT, build_phase1_prompt, build_escalation_prompt
from src.report.builder import ReportBuilder
from src.utils.audit import AuditLogger
from src.utils.shap_formatter import format_shap_summary

logger = logging.getLogger(__name__)


def load_config(path: str = "configs/settings.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class InvestigationPipeline:
    """Phase I investigation pipeline."""

    def __init__(self, config_path: str = "configs/settings.yaml"):
        self.config    = load_config(config_path)
        self.client    = anthropic.Anthropic()
        self.retriever = Retriever(self.config)
        self.audit     = AuditLogger(self.config)
        self._detector = None   # lazy-loaded

    @property
    def detector(self):
        """Lazy-load the trained XGBoost anomaly detector."""
        if self._detector is None:
            from src.ml.model import AnomalyDetector
            self._detector = AnomalyDetector(self.config)
            model_path = self.config["ml"]["model_path"]
            if Path(model_path).exists():
                self._detector.load(model_path)
                logger.info("Anomaly detector loaded from disk.")
            else:
                logger.warning(
                    f"No trained model at {model_path}. "
                    "Run scripts/train_model.py first. "
                    "SHAP features will be unavailable."
                )
        return self._detector

    def run(self, raw_event: dict, feature_row=None, output_dir: str | None = None) -> Path:
        """
        Run full Phase I pipeline for one quality event.

        Parameters
        ----------
        raw_event    : dict       Raw event fields (from lims_adapter.row_to_event)
        feature_row  : pd.Series  Engineered feature row for SHAP (optional)
        output_dir   : str        Override default output directory

        Returns
        -------
        Path to generated .docx report
        """
        # ── 1. Parse & enrich ────────────────────────────────────────────────
        event = enrich_event(parse_event(raw_event))
        logger.info(f"Processing {event['event_id']} ({event['event_type']})")

        # ── 2. SHAP anomaly summary ──────────────────────────────────────────
        shap_result = {}
        shap_png_path = None
        if feature_row is not None and self.detector.clf is not None:
            shap_result = self.detector.predict_single(feature_row)
            # Export SHAP force plot PNG for report embedding
            if self.config["report"].get("include_shap_plot"):
                out = Path(output_dir or self.config["report"]["output_dir"])
                out.mkdir(parents=True, exist_ok=True)
                shap_png_path = str(out / f"{event['event_id']}_shap.png")
                self.detector.shap_force_plot_png(feature_row, shap_png_path)
            # Inject SHAP results back into event dict
            event.update({
                "shap_top_features":    shap_result.get("shap_top_features", []),
                "predicted_event_type": shap_result.get("predicted_event_type"),
                "class_probabilities":  shap_result.get("class_probabilities", {}),
            })

        shap_summary = format_shap_summary(shap_result)

        # ── 3. RAG retrieval ─────────────────────────────────────────────────
        queries = [
            f"Phase I laboratory OOS investigation {event.get('parameter')}",
            f"out of specification analyst error instrument calibration",
            f"21 CFR 211 OOS investigation laboratory assignable cause",
            f"FDA Phase I Phase II escalation OOS guidance",
        ]
        passages = []
        seen = set()
        for q in queries:
            for p in self.retriever.query(q, top_k=3):
                if p.text not in seen:
                    seen.add(p.text)
                    passages.append(p)
        rag_context = self.retriever.format_context(passages[:8])

        # ── 4. LLM: Phase I narrative ────────────────────────────────────────
        phase1_text = self._llm(build_phase1_prompt(event, shap_summary, rag_context))

        # ── 5. LLM: escalation recommendation ───────────────────────────────
        escalation_text = self._llm(build_escalation_prompt(event, phase1_text, rag_context))

        sections = {
            "phase1":     phase1_text,
            "escalation": escalation_text,
        }

        # ── 6. Build report ──────────────────────────────────────────────────
        builder = ReportBuilder(self.config)
        out_dir = Path(output_dir or self.config["report"]["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        doc_path = builder.build(event, sections, out_dir, shap_png_path=shap_png_path)

        # ── 7. Audit trail ───────────────────────────────────────────────────
        self.audit.write(event, sections, passages, doc_path)

        logger.info(f"Report: {doc_path}")
        return doc_path

    def _llm(self, user_prompt: str) -> str:
        msg = self.client.messages.create(
            model=self.config["llm"]["model"],
            max_tokens=self.config["llm"]["max_tokens"],
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text
