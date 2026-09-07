"""Canonical locked-test evidence exposed to the portfolio UI.

Keep this as the application source of truth for the released binary classifier.
The values are locked by ``evaluation/xgboost_binary_test_metrics.json``.
"""

CANONICAL_MODEL_EVIDENCE = {
    "schema_version": 1,
    "model_name": "xgboost-binary",
    "model_version": "1.0.0",
    "task": "Binary network-intrusion classification",
    "artifact_hash": "35755c3ff01fa2973db3a8673f4f9e03",
    "dataset_name": "CICIDS2017 prepared dataset",
    "dataset_hash": "136d82c2aa02afd4668d9bcc18d39a1a.dir",
    "split": "Locked temporal test split",
    "evaluation": "Phase K release-gate evaluation",
    "selected_threshold": 0.461,
    "metrics": {
        "precision": 0.998898,
        "recall": 0.279213,
        "f1": 0.436433,
        "false_positive_rate": 0.000214809,
        "roc_auc": 0.777590,
        "pr_auc": 0.780250,
    },
    "quality_gate_passed": True,
    "source": "evaluation/xgboost_binary_test_metrics.json",
}
