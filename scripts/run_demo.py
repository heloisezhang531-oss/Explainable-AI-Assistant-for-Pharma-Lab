"""
Demo: run the full pipeline on a synthetic OOS event.

Usage:
    python scripts/run_demo.py
    python scripts/run_demo.py --event data/raw/sample_event.json
"""
import argparse
import json
import logging
import sys
sys.path.insert(0, ".")

from src.pipeline.orchestrator import InvestigationPipeline
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


# Synthetic demo event (mirrors a real LIMS JSON export)
DEMO_EVENT = {
    "event_id": "OOS-2024-00815",
    "event_type": "OOS",
    "triggered_at": "2024-08-15T14:32:00",
    "batch_number": "BN240815",
    "product_code": "TAB-500MG-IR",
    "parameter": "Active Ingredient Assay",
    "test_method": "HPLC-UV",
    "result": 87.2,
    "unit": "%",
    "spec_limit": "95.0 - 105.0",
    "analyst_id": "ANA-042",
    "instrument_id": "HPLC-03",
    "last_calibration": "2024-07-14",
    "system_suitability_result": "PASS",
    "sample_storage": "25°C / 60% RH",
    "api_lot_number": "API-2024-L07",
    "analyst_notes": "No anomalies observed during sample preparation.",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", default=None,
                        help="Path to LIMS event JSON file")
    parser.add_argument("--config", default="configs/settings.yaml")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()

    if args.event:
        with open(args.event) as f:
            event = json.load(f)
        logger.info(f"Loaded event from {args.event}")
    else:
        event = DEMO_EVENT
        logger.info("Using built-in demo event (OOS-2024-00815)")

    pipeline = InvestigationPipeline(config_path=args.config)
    doc_path = pipeline.run(event, output_dir=args.output_dir)
    print(f"\nReport generated: {doc_path}")
    print(f"Audit trail:      {doc_path.with_suffix('.audit.json')}")


if __name__ == "__main__":
    main()
