"""
Demo: run the Phase I pipeline on a single OOS event from the Žagar dataset.

Usage:
    python scripts/run_demo.py              # uses first OOS batch in dataset
    python scripts/run_demo.py --batch 42   # specific batch index
    python scripts/run_demo.py --static     # use built-in synthetic event (no CSV needed)
"""
import argparse, logging, sys
sys.path.insert(0, ".")

import yaml

from src.utils.logger import setup_logging
setup_logging()
logger = logging.getLogger(__name__)


STATIC_EVENT = {
    "event_id":     "OOS-DEMO-001",
    "event_type":   "OOS",
    "triggered_at": "2024-08-15T14:32:00",
    "batch_number": "BN240815",
    "product_code": "TAB-ZAGAR-001",
    "parameter":    "Active Ingredient Assay",
    "test_method":  "HPLC-UV",
    "result":       87.2,
    "unit":         "%",
    "spec_limit":   "95.0 - 105.0",
    "analyst_id":   "ANA-042",
    "instrument_id": "HPLC-03",
    "last_calibration": "2024-07-14",
    "system_suitability_result": "PASS",
    "sample_storage": "25°C / 60% RH",
    "api_lot_number": "API-2024-L07",
    "analyst_notes": "No anomalies observed during sample preparation.",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config",  default="configs/settings.yaml")
    parser.add_argument("--batch",   type=int, default=None)
    parser.add_argument("--static",  action="store_true")
    parser.add_argument("--output",  default=None)
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    from src.pipeline.orchestrator import InvestigationPipeline
    pipeline = InvestigationPipeline(config_path=args.config)

    if args.static:
        logger.info("Using static demo event (no CSV required)")
        doc_path = pipeline.run(STATIC_EVENT, feature_row=None, output_dir=args.output)
    else:
        import pandas as pd
        from src.data.loader import ZagarDataset
        from src.data.anomaly_injection import build_dataset
        from src.ml.features import engineer_features, feature_columns
        from src.pipeline.lims_adapter import row_to_event

        dataset = ZagarDataset(config)
        target_col = dataset.assay_col
        df = build_dataset(config, dataset.lab, target_col)
        df_feat = engineer_features(df, dataset.numeric_lab_cols())
        feat_cols = feature_columns(df_feat, dataset.numeric_lab_cols())

        # Pick batch: user-specified or first OOS
        if args.batch is not None:
            idx = args.batch
        else:
            oos = df_feat[df_feat["event_type"] == "OOS"]
            if oos.empty:
                logger.error("No OOS events found after injection. Increase injection rate.")
                sys.exit(1)
            idx = int(oos.index[0])

        row = df_feat.loc[idx]
        event_type = str(row.get("event_type", "OOS"))
        raw_event = row_to_event(row, f"OOS-ZAGAR-{idx:04d}", target_col, event_type)

        feat_row = row[feat_cols]
        doc_path = pipeline.run(raw_event, feature_row=feat_row, output_dir=args.output)

    print(f"
Report:      {doc_path}")
    print(f"Audit trail: {doc_path.with_suffix('.audit.json')}")


if __name__ == "__main__":
    main()
