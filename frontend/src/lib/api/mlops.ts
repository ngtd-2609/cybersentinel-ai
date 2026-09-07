import { apiFetch } from "@/lib/api/client";

export interface ModelEvaluationEvidence {
  schema_version: number;
  model_name: string;
  model_version: string;
  task: string;
  artifact_hash: string;
  dataset_name: string;
  dataset_hash: string;
  split: string;
  evaluation: string;
  selected_threshold: number;
  metrics: {
    precision: number;
    recall: number;
    f1: number;
    false_positive_rate: number;
    roc_auc: number;
    pr_auc: number;
  };
  quality_gate_passed: boolean;
  source: string;
}

export async function getModelEvaluationEvidence(): Promise<ModelEvaluationEvidence> {
  const response = await apiFetch("/mlops/evaluation-evidence", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Model evidence request failed with status ${response.status}`);
  }
  return response.json() as Promise<ModelEvaluationEvidence>;
}
