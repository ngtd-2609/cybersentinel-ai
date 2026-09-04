# CyberSentinel AI

> End-to-end AI-assisted Network Intrusion Detection, Risk Scoring, Threat Intelligence Enrichment, and SOC Copilot platform.

CyberSentinel AI is a defensive cybersecurity project that combines traditional machine learning, anomaly detection, rule-based security logic, threat-intelligence enrichment, Retrieval-Augmented Generation (RAG), REST APIs, experiment tracking, data/model versioning, containerization, monitoring, and CI into one reproducible system.

The main experimental dataset is CIC-IDS2017. The project is designed not only to train a high-performing intrusion-detection model, but also to demonstrate how an ML model can be integrated into a practical SOC-oriented architecture.

The complete pipeline covers:

- Network security dataset ingestion and validation
- Leakage-aware preprocessing and dataset splitting
- Binary intrusion detection
- Multiclass attack classification
- Unsupervised anomaly detection
- Rule-based network security signals
- Weighted cyber-risk scoring
- MITRE ATT&CK contextual mapping
- NVD CVE enrichment
- Local Retrieval-Augmented Generation
- Ollama-powered SOC Copilot
- FastAPI REST services
- SQLite event persistence
- MLflow experiment tracking
- DVC dataset and model versioning
- Prometheus monitoring
- Grafana dashboards
- Docker deployment
- Automated testing
- GitHub Actions CI

CyberSentinel AI is intended for defensive cybersecurity research, portfolio demonstration, learning, and experimentation.

It is not intended to replace a production IDS, IPS, SIEM, SOAR, EDR, or professional SOC workflow without additional security engineering, infrastructure hardening, model validation, authentication, authorization, and operational monitoring.

---

# Table of Contents

1. Project Overview
2. Project Objectives
3. System Architecture
4. End-to-End Data Flow
5. Technology Stack
6. Repository Structure
7. Dataset
8. Data Validation
9. Feature Engineering
10. Dataset Splitting Strategy
11. Binary Intrusion Detection
12. Multiclass Attack Classification
13. Anomaly Detection
14. Risk Scoring Engine
15. Rule-Based Security Signals
16. MITRE ATT&CK Mapping
17. NVD CVE Enrichment
18. SOC RAG Knowledge Base
19. Ollama SOC Copilot
20. FastAPI Service
21. Database Layer
22. Monitoring and Observability
23. MLflow Experiment Tracking
24. DVC Data and Model Versioning
25. Docker Deployment
26. Development Setup
27. Running the Application
28. API Usage Examples
29. Testing
30. Code Quality
31. Continuous Integration
32. Reproducibility
33. Model Evaluation Summary
34. Known Limitations
35. Security Considerations
36. Future Improvements
37. Project Status
38. Author Notes

---

# 1. Project Overview

Modern intrusion-detection projects often stop after training a classifier and reporting accuracy.

CyberSentinel AI intentionally goes further.

The project demonstrates an end-to-end cybersecurity AI workflow in which machine-learning outputs are treated as only one component of a larger defensive decision system.

Instead of returning only:

```text
ATTACK
```

the architecture is designed to eventually provide richer SOC context such as:

```text
Predicted attack
Classifier confidence
Anomaly signal
Rule-based indicators
Risk score
Severity
MITRE ATT&CK context
Optional vulnerability context
Recommended analyst actions
Human-review recommendation
```

The project therefore combines three major areas:

### Machine Learning

- Data ingestion
- Data validation
- Feature engineering
- Binary classification
- Multiclass classification
- Anomaly detection
- Threshold selection
- Evaluation

### Cybersecurity Intelligence

- Rule-based network indicators
- Risk scoring
- MITRE ATT&CK mapping
- NVD CVE context
- SOC playbooks

### MLOps and Software Engineering

- MLflow
- DVC
- FastAPI
- SQLAlchemy
- SQLite
- Docker
- Prometheus
- Grafana
- Ruff
- Pytest
- pre-commit
- GitHub Actions

---

# 2. Project Objectives

CyberSentinel AI has the following objectives.

## 2.1 Build a reproducible intrusion-detection pipeline

The pipeline must support:

- raw dataset ingestion
- validation
- preprocessing
- training
- validation
- locked test evaluation
- artifact persistence
- experiment tracking

## 2.2 Reduce common machine-learning evaluation mistakes

Particular attention is given to:

- train/test contamination
- leakage
- class imbalance
- rare attack categories
- inappropriate threshold tuning
- validation/test separation
- temporal distribution shift

## 2.3 Combine multiple security signals

A production security alert should not depend exclusively on one classifier probability.

CyberSentinel AI therefore combines:

- supervised classifier confidence
- anomaly signal
- rule-based signals
- asset criticality
- vulnerability context

into a unified risk score.

## 2.4 Add threat-intelligence context

Predictions can be enriched with:

- MITRE ATT&CK techniques
- tactic context
- NVD CVE information
- CVSS information

## 2.5 Add analyst-oriented AI assistance

A local RAG pipeline supplies relevant defensive knowledge to an Ollama-hosted LLM.

The SOC Copilot is instructed to:

- use supplied evidence
- avoid inventing indicators
- avoid inventing CVEs
- avoid inventing hosts or users
- disclose insufficient evidence
- provide practical analyst recommendations

## 2.6 Demonstrate MLOps practices

The project integrates:

- data versioning
- model artifact versioning
- experiment tracking
- automated testing
- linting
- containerization
- observability
- continuous integration

---

# 3. System Architecture

The high-level system architecture is:

```text
                         ┌──────────────────────┐
                         │     CIC-IDS2017      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Ingestion       │
                         │     + Validation     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Feature Engineering  │
                         │ + Dataset Splitting  │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌──────────────────┐            ┌──────────────────┐
          │ Supervised Model │            │ Isolation Forest │
          │ XGBoost          │            │ Anomaly Detector │
          └────────┬─────────┘            └────────┬─────────┘
                   │                               │
                   └──────────────┬────────────────┘
                                  │
                                  ▼
                       ┌────────────────────┐
                       │ Rule-Based Signals │
                       └─────────┬──────────┘
                                 │
                                 ▼
                       ┌────────────────────┐
                       │    Risk Engine     │
                       │    Score 0-100     │
                       └─────────┬──────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
       ┌───────────────────┐          ┌────────────────────┐
       │   MITRE ATT&CK    │          │      NVD CVE       │
       │     Mapping       │          │    Enrichment      │
       └─────────┬─────────┘          └──────────┬─────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                       ┌────────────────────┐
                       │   SOC Knowledge    │
                       │      Retriever     │
                       └─────────┬──────────┘
                                 │
                                 ▼
                       ┌────────────────────┐
                       │   Ollama + RAG     │
                       │    SOC Copilot     │
                       └─────────┬──────────┘
                                 │
                                 ▼
                       ┌────────────────────┐
                       │      FastAPI       │
                       └─────────┬──────────┘
                                 │
                  ┌──────────────┴───────────────┐
                  │                              │
                  ▼                              ▼
        ┌──────────────────┐           ┌──────────────────┐
        │      SQLite      │           │    Prometheus    │
        │ Detection Events │           │     Metrics      │
        └──────────────────┘           └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │     Grafana      │
                                      │    Dashboard     │
                                      └──────────────────┘
```

Cross-cutting MLOps components include:

```text
DVC
MLflow
Pytest
Ruff
pre-commit
Docker
GitHub Actions
```

---

# 4. End-to-End Data Flow

A simplified CyberSentinel AI workflow is:

```text
Raw network flow
      │
      ▼
Schema validation
      │
      ▼
Feature preprocessing
      │
      ▼
Classifier prediction
      │
      ├───────────────┐
      ▼               ▼
Confidence       Anomaly detector
      │               │
      └───────┬───────┘
              ▼
       Security rules
              │
              ▼
         Risk engine
              │
              ▼
      Severity assignment
              │
              ▼
      Threat enrichment
              │
              ▼
     Detection event API
              │
              ├────────────► SQLite
              │
              ▼
        SOC RAG Copilot
              │
              ▼
      Analyst recommendation
```

---

# 5. Technology Stack

## Core Language

```text
Python 3.12
```

## Data and Machine Learning

```text
NumPy
Pandas
Scikit-learn
XGBoost
Joblib
PyArrow
```

## Experiment Tracking

```text
MLflow
```

## Data and Artifact Versioning

```text
DVC
```

## Backend

```text
FastAPI
Uvicorn
Pydantic
SQLAlchemy
SQLite
HTTPX
```

## Local AI

```text
Ollama
Qwen models
TF-IDF retrieval
Retrieval-Augmented Generation
```

## Threat Intelligence

```text
MITRE ATT&CK contextual mapping
NVD CVE API
CVSS enrichment
```

## Monitoring

```text
Prometheus
Grafana
```

## Infrastructure

```text
Docker
Docker Compose
```

## Quality

```text
Pytest
Ruff
pre-commit
```

## Continuous Integration

```text
GitHub Actions
```

---

# 6. Repository Structure

```text
cybersentinel-ai/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── artifacts/
│   ├── isolation_forest/
│   ├── xgboost/
│   └── xgboost_multiclass/
│
├── data/
│   ├── external/
│   ├── interim/
│   ├── processed/
│   └── raw/
│
├── docker/
│   └── Dockerfile
│
├── docs/
│
├── monitoring/
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   └── prometheus/
│
├── notebooks/
│
├── scripts/
│   ├── audit_cicids2017.py
│   ├── build_binary_dataset.py
│   ├── build_multiclass_dataset.py
│   ├── check_real_schema.py
│   ├── check_split_policy.py
│   ├── evaluate_xgboost_multiclass_test.py
│   ├── evaluate_xgboost_test.py
│   ├── train_baseline.py
│   ├── train_hist_gradient_boosting.py
│   ├── train_isolation_forest.py
│   ├── train_xgboost.py
│   └── train_xgboost_multiclass.py
│
├── src/
│   └── cybersentinel_ai/
│       │
│       ├── api/
│       │   ├── copilot_routes.py
│       │   ├── main.py
│       │   ├── metrics.py
│       │   ├── routes.py
│       │   └── schemas.py
│       │
│       ├── db/
│       │   ├── database.py
│       │   ├── models.py
│       │   └── repository.py
│       │
│       ├── features/
│       │   ├── dataset.py
│       │   ├── labels.py
│       │   ├── preprocessing.py
│       │   ├── selection.py
│       │   └── splitting.py
│       │
│       ├── ingestion/
│       │   └── cicids2017.py
│       │
│       ├── models/
│       │   ├── anomaly.py
│       │   ├── baseline.py
│       │   ├── hist_gradient_boosting.py
│       │   ├── xgboost_model.py
│       │   └── xgboost_multiclass.py
│       │
│       ├── rag/
│       │   ├── copilot.py
│       │   ├── knowledge_base.py
│       │   ├── ollama_client.py
│       │   └── retriever.py
│       │
│       ├── risk/
│       │   ├── engine.py
│       │   ├── rules.py
│       │   └── scoring.py
│       │
│       ├── threat_intel/
│       │   ├── attack_mapping.py
│       │   ├── enrichment.py
│       │   └── nvd.py
│       │
│       ├── training/
│       │   ├── metrics.py
│       │   ├── mlflow_utils.py
│       │   ├── multiclass_metrics.py
│       │   └── thresholds.py
│       │
│       └── validation/
│           ├── cicids2017.py
│           └── schema.py
│
├── tests/
│
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# 7. Dataset

CyberSentinel AI currently uses CIC-IDS2017 as its primary benchmark dataset.

The development copy contains:

```text
CSV files:          8
Total rows:         2,830,743
Original columns:   79
Labels:             15
```

CIC-IDS2017 includes benign traffic and multiple attack categories including:

```text
BENIGN
Bot
DDoS
DoS GoldenEye
DoS Hulk
DoS Slowhttptest
DoS slowloris
FTP-Patator
Heartbleed
Infiltration
PortScan
SSH-Patator
Web Attack - Brute Force
Web Attack - Sql Injection
Web Attack - XSS
```

Large raw datasets are intentionally excluded from Git.

DVC is used for version-controlled dataset references.

---

# 8. Data Validation

Before model training, the ingestion pipeline checks dataset structure and schema assumptions.

Validation responsibilities include:

- expected columns
- label presence
- invalid values
- numeric compatibility
- dataset consistency
- schema verification

Relevant modules:

```text
src/cybersentinel_ai/ingestion/
src/cybersentinel_ai/validation/
```

Relevant scripts:

```text
scripts/audit_cicids2017.py
scripts/check_real_schema.py
```

---

# 9. Feature Engineering

The original CIC-IDS2017 data contains 79 columns.

The project removes problematic or redundant features, including constant or duplicated training features.

The resulting model representation contains:

```text
67 model features
1 target label
```

Feature preprocessing is implemented under:

```text
src/cybersentinel_ai/features/
```

Major responsibilities include:

- feature selection
- label handling
- preprocessing
- dataset preparation
- splitting logic

---

# 10. Dataset Splitting Strategy

Evaluation leakage is a major problem in intrusion-detection research.

For the binary experiment, CyberSentinel AI uses a day-based split.

```text
TRAIN
Monday
Tuesday
Wednesday

VALIDATION
Thursday

LOCKED TEST
Friday
```

Dataset sizes:

```text
Train:       1,668,530 rows
Validation:    458,968 rows
Test:          703,245 rows
```

The Friday test set is treated as locked evaluation data.

Model thresholds are not selected using the test set.

This strategy intentionally exposes distribution shift between different collection days rather than hiding it behind a fully randomized split.

---

# 11. Binary Intrusion Detection

Binary classification converts the problem into:

```text
BENIGN
ATTACK
```

The primary model is XGBoost.

## Validation Results

```text
Accuracy:   0.999076
Precision:  0.921846
Recall:     0.883574
F1 Score:   0.902304
ROC-AUC:    0.996336
PR-AUC:     0.821719
```

Validation confusion matrix:

```text
True Negative:   456,586
False Positive:      166
False Negative:      258
True Positive:     1,958
```

The validation-selected decision threshold is:

```text
0.461
```

## Locked Test Results

```text
Accuracy:   0.703743
Precision:  0.998898
Recall:     0.279213
F1 Score:   0.436433
ROC-AUC:    0.777590
PR-AUC:     0.780250
```

The large validation-to-test degradation is not hidden.

It demonstrates that extremely strong validation results on intrusion datasets do not necessarily indicate strong temporal generalization.

The model was not retuned against the locked test set.

---

# 12. Multiclass Attack Classification

CyberSentinel AI also trains a classifier over all 15 CIC-IDS2017 labels.

The multiclass split contains all classes across train, validation, and test sets.

Approximate sizes:

```text
Train:       2,264,609
Validation:    277,952
Test:          288,182
```

## Validation Results

```text
Accuracy:      0.998482
Macro F1:      0.870790
Weighted F1:   0.998538
```

## Locked Test Results

```text
Accuracy:      0.998546
Macro F1:      0.872429
Weighted F1:   0.998585
```

Macro F1 is especially important because CIC-IDS2017 is highly imbalanced.

A high accuracy score alone would hide poor performance on rare attack categories.

---

# 13. Anomaly Detection

CyberSentinel AI includes an Isolation Forest detector.

The anomaly model is not treated as the primary intrusion classifier.

It acts as an auxiliary signal for the risk engine.

Validation results:

```text
Threshold:   0.08

Accuracy:    0.975362
Precision:   0.012336
Recall:      0.051895
F1 Score:    0.019934
ROC-AUC:     0.728262
PR-AUC:      0.009430
```

These results illustrate an important security lesson:

```text
High overall accuracy does not imply useful anomaly detection.
```

Because benign traffic dominates the dataset, precision, recall, PR-AUC, and attack-class behavior must be evaluated separately.

---

# 14. Risk Scoring Engine

CyberSentinel AI combines several independent signals into a unified risk score.

The default weighting strategy is:

```text
Classifier confidence:   45%
Anomaly signal:          20%
Rule-based score:        15%
Asset criticality:       10%
Vulnerability context:   10%
```

The result is normalized to:

```text
0 - 100
```

Severity thresholds are:

```text
0  - 39     LOW
40 - 69     MEDIUM
70 - 89     HIGH
90 - 100    CRITICAL
```

The risk engine is implemented in:

```text
src/cybersentinel_ai/risk/scoring.py
src/cybersentinel_ai/risk/engine.py
```

The engine can also flag uncertain detections for analyst review.

An example review condition is:

```text
low classifier confidence
+
high anomaly signal
```

---

# 15. Rule-Based Security Signals

Machine-learning predictions are supplemented with deterministic network rules.

Current signals include:

- suspicious destination ports
- unusually high packet rate
- high SYN count
- high RST count
- invalid or zero flow duration

Example suspicious ports include:

```text
21
22
23
25
53
80
110
135
139
443
445
1433
3306
3389
8080
```

Rule logic is located in:

```text
src/cybersentinel_ai/risk/rules.py
```

Rules should be treated as contextual indicators, not standalone proof of malicious behavior.

---

# 16. MITRE ATT&CK Mapping

CyberSentinel AI provides contextual ATT&CK mappings for detected attack labels.

Examples:

## Network Service Discovery

```text
PortScan
→ T1046
→ Network Service Discovery
→ Discovery
```

## Brute Force

```text
FTP-Patator
SSH-Patator
Web Attack - Brute Force
→ T1110
→ Brute Force
→ Credential Access
```

## Network Denial of Service

```text
DDoS
DoS variants
→ T1498
→ Network Denial of Service
→ Impact
```

## Exploit Public-Facing Application

```text
SQL Injection
XSS
Heartbleed
→ T1190
→ Exploit Public-Facing Application
→ Initial Access
```

The mapping implementation is located in:

```text
src/cybersentinel_ai/threat_intel/attack_mapping.py
```

Important:

These mappings are contextual approximations.

They do not constitute proof that a specific ATT&CK technique was observed in a real environment.

---

# 17. NVD CVE Enrichment

CyberSentinel AI contains an NVD CVE enrichment client.

The client can retrieve:

- CVE identifier
- description
- CVSS score
- CVSS severity
- references

Supported CVSS parsing includes:

```text
CVSS v4
CVSS v3.1
CVSS v3.0
CVSS v2
```

Implementation:

```text
src/cybersentinel_ai/threat_intel/nvd.py
```

Threat-context composition:

```text
src/cybersentinel_ai/threat_intel/enrichment.py
```

NVD enrichment is optional and only applies when an appropriate CVE identifier is available.

---

# 18. SOC RAG Knowledge Base

The SOC Copilot does not send an unconstrained prompt directly to an LLM.

CyberSentinel AI first retrieves defensive knowledge from a local knowledge base.

The current RAG system uses:

```text
TF-IDF
Cosine similarity
Deterministic ATT&CK injection
SOC playbook documents
```

The knowledge base includes material for areas such as:

```text
DDoS
Port scanning
Brute force
Web attacks
MITRE ATT&CK context
SOC response actions
```

Relevant modules:

```text
src/cybersentinel_ai/rag/retriever.py
src/cybersentinel_ai/rag/knowledge_base.py
```

---

# 19. Ollama SOC Copilot

CyberSentinel AI uses a local Ollama instance for LLM inference.

The Ollama client supports environment configuration.

Supported variables:

```text
CYBERSENTINEL_OLLAMA_URL
CYBERSENTINEL_OLLAMA_MODEL
```

Default native configuration:

```text
URL:
http://127.0.0.1:11434

Model:
qwen2.5:3b
```

Docker Compose currently connects the API container to a host Ollama instance through:

```text
http://host.docker.internal:11434
```

The current Docker model configuration is:

```text
qwen3:4b
```

The connection path has been tested successfully:

```text
Docker API
→ host.docker.internal
→ Ollama
→ qwen3:4b
→ generated response
```

The SOC Copilot was also tested end-to-end through:

```text
POST /copilot/ask
```

with an HTTP 200 response.

---

# 20. SOC Copilot Safety Design

The Copilot system prompt directs the LLM to:

- use supplied context
- state when evidence is insufficient
- avoid inventing network indicators
- avoid inventing CVEs
- avoid inventing MITRE mappings
- avoid inventing usernames
- avoid inventing hosts
- avoid inventing security evidence
- provide practical defensive recommendations

The goal is to reduce unsupported SOC conclusions.

LLM output must still be reviewed by a human analyst.

---

# 21. FastAPI Service

CyberSentinel AI exposes its application layer through FastAPI.

Application entry point:

```text
src/cybersentinel_ai/api/main.py
```

Start locally:

```bash
uv run uvicorn cybersentinel_ai.api.main:app --host 0.0.0.0 --port 8000
```

Main local address:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

---

# 22. Main API Endpoints

## Health

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "cybersentinel-ai"
}
```

## Prometheus Metrics

```text
GET /metrics
```

## Detection Events

```text
POST /events
GET /events
GET /events/{id}
```

## SOC Copilot

```text
POST /copilot/ask
```

Example body:

```json
{
  "question": "What should a SOC analyst do for a PortScan alert?",
  "alert_context": "Detected label: PortScan. Risk score: 78. Severity: HIGH.",
  "top_k": 4
}
```

The response contains:

```text
answer
model
sources
```

---

# 23. Database Layer

CyberSentinel AI currently uses SQLAlchemy with SQLite.

Default local database:

```text
sqlite:///./cybersentinel.db
```

The database URL can be controlled through:

```text
CYBERSENTINEL_DATABASE_URL
```

Detection events can store information including:

```text
source IP
destination IP
destination port
predicted label
classifier confidence
anomaly score
rule score
risk score
severity
requires review
creation timestamp
```

Relevant modules:

```text
src/cybersentinel_ai/db/database.py
src/cybersentinel_ai/db/models.py
src/cybersentinel_ai/db/repository.py
```

SQLite is suitable for development and demonstration.

A production deployment would typically migrate to a dedicated database service.

---

# 24. Monitoring and Observability

CyberSentinel AI exports Prometheus-compatible HTTP metrics.

Current metrics include:

```text
cybersentinel_http_requests_total
cybersentinel_http_request_duration_seconds
```

Prometheus configuration:

```text
monitoring/prometheus/prometheus.yml
```

Prometheus scrapes:

```text
api:8000/metrics
```

The target has been verified as:

```text
cybersentinel-api up
```

---

# 25. Grafana Dashboard

Grafana is automatically provisioned through repository configuration.

Dashboard:

```text
CyberSentinel AI Overview
```

Dashboard UID:

```text
cybersentinel-overview
```

Current panels include:

- HTTP Request Rate
- Requests by Status
- Average API Latency
- Requests by Endpoint

Relevant files:

```text
monitoring/grafana/dashboards/cybersentinel-overview.json

monitoring/grafana/provisioning/dashboards/default.yml

monitoring/grafana/provisioning/datasources/prometheus.yml
```

---

# 26. MLflow Experiment Tracking

CyberSentinel AI uses MLflow for experiment tracking.

Local tracking backend:

```text
sqlite:///mlflow.db
```

Experiments have been created for:

```text
Binary XGBoost
Multiclass XGBoost
Isolation Forest
```

Training scripts log:

- parameters
- validation metrics
- model information
- selected artifacts

Relevant module:

```text
src/cybersentinel_ai/training/mlflow_utils.py
```

MLflow runtime files are intentionally ignored by Git.

Start the UI when required:

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

---

# 27. DVC Data and Model Versioning

CyberSentinel AI uses DVC for large data and model artifacts.

DVC prevents large datasets and trained binaries from being committed directly to Git.

Production model artifacts currently include:

```text
artifacts/xgboost/model.joblib.dvc

artifacts/xgboost_multiclass/model.joblib.dvc

artifacts/isolation_forest/model.joblib.dvc
```

Check DVC state:

```bash
uv run dvc status
```

Restore data or model objects:

```bash
uv run dvc pull
```

Push DVC objects:

```bash
uv run dvc push
```

The development machine currently uses a local DVC remote outside the Git repository.

Because that remote is machine-local, GitHub Actions does not automatically attempt a DVC pull.

---

# 28. Docker Deployment

CyberSentinel AI includes a complete Docker Compose observability stack.

Services:

```text
cybersentinel-api
cybersentinel-prometheus
cybersentinel-grafana
```

Build and start:

```bash
docker compose up -d --build
```

Public registration is disabled by default. Bootstrap the first administrator
once, using the hidden password prompt so the password is not stored in shell
history or Docker Compose environment configuration:

```bash
docker compose exec api /app/.venv/bin/python -m cybersentinel_ai.auth.bootstrap \
  --email admin@example.com \
  --username admin \
  --full-name "SOC Administrator"
```

The command refuses to run after any administrator exists. For non-interactive
automation, pass `--password-stdin` and supply the password through standard input
from an appropriate secret manager. Public registration can be deliberately enabled
with `CYBERSENTINEL_PUBLIC_REGISTRATION_ENABLED=true`; do not enable it on an
internet-facing deployment without email verification and abuse controls.

Login protection defaults to five failed attempts followed by a 15-minute
database-backed account lock. Configure it with
`CYBERSENTINEL_ACCOUNT_LOCKOUT_ATTEMPTS` and
`CYBERSENTINEL_ACCOUNT_LOCKOUT_MINUTES`.

Check:

```bash
docker compose ps
```

Current host mappings:

```text
CyberSentinel API
Host port: 8001
Container port: 8000

Prometheus
Host port: 9091
Container port: 9090

Grafana
Host port: 3001
Container port: 3000
```

Therefore:

```text
API
http://127.0.0.1:8001

Swagger
http://127.0.0.1:8001/docs

Prometheus
http://127.0.0.1:9091

Grafana
http://127.0.0.1:3001
```

Stop:

```bash
docker compose down
```

---

# 29. Docker API Runtime

The image is based on:

```text
python:3.12-slim
```

Dependencies are installed using `uv`.

The application runs directly from the image virtual environment:

```text
/app/.venv/bin/uvicorn
```

This avoids unnecessary dependency synchronization during each container startup.

The image build excludes unnecessary local content through `.dockerignore`.

Examples include:

```text
.git
.github
.venv
data
artifacts
MLflow runtime
local database
environment files
credentials
notebooks
temporary directories
```

---

# 30. Development Setup

## Requirements

Recommended local tools:

```text
Python 3.12
uv
Git
Git LFS
DVC
Docker
Docker Compose
Ollama
```

Clone the repository:

```bash
git clone https://github.com/ngtd-2609/cybersentinel-ai.git
cd cybersentinel-ai
```

Install dependencies:

```bash
uv sync
```

Verify environment:

```bash
uv run python --version
```

---

# 31. Running Tests

Run the entire test suite:

```bash
uv run pytest
```

At the current project state:

```text
94 tests passed
```

The suite covers:

- anomaly models
- API
- Copilot API
- event API
- Prometheus metrics
- MITRE mapping
- baseline models
- CIC-IDS2017 ingestion
- CIC-IDS2017 validation
- database
- database models
- dataset preparation
- event repository
- feature selection
- gradient boosting
- labels
- MLflow utilities
- multiclass metrics
- NVD integration
- Ollama client
- preprocessing
- RAG Copilot
- RAG knowledge base
- RAG retrieval
- risk engine
- security rules
- risk scoring
- schemas
- smoke tests
- split policy
- threat enrichment
- thresholds
- training metrics
- XGBoost
- multiclass XGBoost

---

# 32. Code Quality

Run Ruff:

```bash
uv run ruff check .
```

The repository also uses pre-commit hooks.

Before commits, quality checks execute automatically.

Typical checks include:

```text
Ruff
Pytest
```

---

# 33. Continuous Integration

GitHub Actions is configured in:

```text
.github/workflows/ci.yml
```

The workflow runs on:

```text
push to main
pull requests
```

CI jobs include:

## Quality

```text
Install Python 3.12
Install dependencies
Ruff
Pytest
```

## Docker Build

```text
Build CyberSentinel API image
```

The latest project CI runs have completed successfully.

---

# 34. Reproducibility

CyberSentinel AI separates four forms of state.

## Git

Stores:

```text
source code
tests
configuration
DVC metadata
Docker configuration
monitoring configuration
documentation
```

## DVC

Stores references for:

```text
large datasets
trained production model artifacts
```

## MLflow

Tracks:

```text
model experiments
training parameters
metrics
artifacts
```

## Docker

Defines:

```text
portable application runtime
monitoring services
observability stack
```

This structure prevents model development from depending solely on an undocumented local environment.

---

# 35. Model Evaluation Summary

## Binary XGBoost

### Validation

| Metric | Score |
|---|---:|
| Accuracy | 0.999076 |
| Precision | 0.921846 |
| Recall | 0.883574 |
| F1 | 0.902304 |
| ROC-AUC | 0.996336 |
| PR-AUC | 0.821719 |

### Locked Test

| Metric | Score |
|---|---:|
| Accuracy | 0.703743 |
| Precision | 0.998898 |
| Recall | 0.279213 |
| F1 | 0.436433 |
| ROC-AUC | 0.777590 |
| PR-AUC | 0.780250 |

---

## Multiclass XGBoost

### Validation

| Metric | Score |
|---|---:|
| Accuracy | 0.998482 |
| Macro F1 | 0.870790 |
| Weighted F1 | 0.998538 |

### Locked Test

| Metric | Score |
|---|---:|
| Accuracy | 0.998546 |
| Macro F1 | 0.872429 |
| Weighted F1 | 0.998585 |

---

## Isolation Forest

| Metric | Score |
|---|---:|
| Threshold | 0.08 |
| Accuracy | 0.975362 |
| Precision | 0.012336 |
| Recall | 0.051895 |
| F1 | 0.019934 |
| ROC-AUC | 0.728262 |
| PR-AUC | 0.009430 |

---

# 36. Interpretation of Results

Several important conclusions can be drawn from the current experiments.

## Binary model

The binary model achieves excellent validation performance but substantially lower recall on the locked Friday test set.

This indicates temporal distribution shift.

Rather than tuning against the test set, CyberSentinel AI preserves this result as evidence of a genuine generalization problem.

## Multiclass model

Multiclass performance is very strong overall.

However, weighted metrics are influenced heavily by common classes.

Macro F1 is therefore retained as a more meaningful indicator across classes.

## Isolation Forest

Isolation Forest provides useful ranking information but performs poorly as a direct standalone attack detector.

It is therefore used only as an auxiliary signal in the risk architecture.

---

# 37. Known Limitations

CyberSentinel AI currently has several known limitations.

## Dataset age

CIC-IDS2017 is a historical benchmark.

Modern enterprise traffic, cloud-native workloads, encrypted protocols, modern malware, identity attacks, and current adversary behavior are not fully represented.

## Dataset realism

Benchmark traffic differs from production environments.

Strong benchmark results should not be interpreted directly as equivalent production IDS performance.

## Temporal generalization

Binary test results demonstrate substantial distribution shift between collection days.

This is a critical research result rather than a hidden failure.

## Rare classes

Several CIC-IDS2017 attack classes contain very few observations.

Performance estimates for these classes may therefore be unstable.

## Anomaly calibration

The anomaly component currently acts as an auxiliary score.

Further normalization and calibration are appropriate before production use.

## Multiclass split validation

Additional global duplicate/leakage auditing would strengthen the deterministic label-aware multiclass splitting strategy.

## ATT&CK mapping

Current mappings are contextual approximations.

They do not establish forensic proof of an ATT&CK technique.

## NVD context

NVD enrichment requires an appropriate CVE identifier.

The system does not automatically prove that a detected network event exploits a given CVE.

## LLM reliability

The SOC Copilot may still generate incorrect or incomplete reasoning.

Retrieved evidence and analyst review remain necessary.

## Authentication

The API implements password authentication, RBAC, short-lived access tokens,
rotating refresh sessions, explicit session revocation, one-time first-admin
bootstrap, closed-by-default public registration, and database-backed account
lockout. The remaining production hardening work includes:

```text
password reset and email verification
administrator MFA/TOTP
distributed Redis rate limiting
OAuth
API keys
```

## Transport security

The local demonstration stack does not provide production TLS termination.

## Database scalability

SQLite is appropriate for development but not intended for high-volume distributed event ingestion.

## Distributed inference

The current architecture is a single-node demonstration and does not include:

```text
Kafka
Redis
Celery
Kubernetes deployment
distributed inference workers
horizontal autoscaling
```

---

# 38. Security Considerations

CyberSentinel AI is a defensive project.

Before exposing the application to an untrusted network, additional protections should be implemented.

Recommended production controls include:

- API authentication
- authorization
- RBAC
- HTTPS/TLS
- secure secret management
- database access controls
- request rate limiting
- input size limits
- structured audit logging
- dependency vulnerability scanning
- container vulnerability scanning
- network segmentation
- firewall controls
- reverse proxy
- secure HTTP headers
- strict CORS policy
- model artifact integrity verification
- DVC remote access control
- MLflow access control
- Grafana authentication hardening
- Prometheus access restrictions

Do not expose Ollama directly to an untrusted network.

---

# 39. Future Improvements

Planned or possible future work includes:

## Machine Learning

- additional feature analysis
- better probability calibration
- anomaly-score normalization
- drift detection
- model monitoring
- explainability with SHAP
- additional datasets such as UNSW-NB15
- ToN-IoT evaluation
- cross-dataset generalization
- stronger imbalance handling
- rare-class analysis
- incremental learning

## Threat Intelligence

- richer ATT&CK mapping
- STIX/TAXII integration
- IOC enrichment
- reputation services
- improved CVE correlation
- threat-feed ingestion

## SOC Copilot

- vector database retrieval
- embedding-based retrieval
- reranking
- evidence citations
- conversation history
- alert-specific playbooks
- structured Copilot output
- analyst feedback loop
- response confidence scoring

## Backend

- PostgreSQL
- migrations
- API authentication
- RBAC
- background workers
- message queues
- event streaming
- WebSocket updates

## Monitoring

- detection-level Prometheus metrics
- attack-class counters
- severity counters
- review-required counters
- model latency
- inference errors
- model-confidence monitoring
- drift dashboards
- alerting rules

## Infrastructure

- Kubernetes
- Helm
- OpenTofu/Terraform
- external secrets
- production reverse proxy
- HTTPS
- container registry
- staged CI/CD deployment

---

# 40. Project Status

Current implementation status:

```text
[✓] Project scope and architecture
[✓] Repository structure
[✓] CIC-IDS2017 ingestion
[✓] Dataset audit
[✓] DVC dataset tracking
[✓] Feature preprocessing
[✓] Leakage-aware binary splitting
[✓] Binary baseline model
[✓] Binary XGBoost model
[✓] Validation threshold selection
[✓] Locked binary test evaluation
[✓] Multiclass dataset preparation
[✓] Multiclass XGBoost
[✓] Locked multiclass test evaluation
[✓] Isolation Forest anomaly detector
[✓] Rule-based security signals
[✓] Weighted risk engine
[✓] MLflow tracking
[✓] Production model artifact versioning with DVC
[✓] FastAPI application
[✓] SQLite persistence
[✓] Detection-event API
[✓] MITRE ATT&CK mapping
[✓] NVD CVE client
[✓] Threat-intelligence enrichment
[✓] TF-IDF RAG retriever
[✓] SOC knowledge base
[✓] Ollama client
[✓] SOC RAG Copilot
[✓] Copilot FastAPI endpoint
[✓] Prometheus instrumentation
[✓] Prometheus deployment
[✓] Grafana deployment
[✓] Grafana datasource provisioning
[✓] Grafana dashboard provisioning
[✓] Docker API deployment
[✓] Docker-to-Ollama integration
[✓] Docker hardening rules
[✓] Ruff
[✓] Pytest
[✓] pre-commit
[✓] GitHub Actions
[✓] CI Docker build
[✓] End-to-end Docker Copilot test

[ ] Final documentation validation
[ ] Final demonstration checklist
[ ] Final release snapshot
```

---

# 41. Current Verification State

At the current project checkpoint:

```text
Python tests:
94 passed

Ruff:
Passed

Docker API:
Running

API health:
HTTP 200

Prometheus:
Healthy

Prometheus API target:
cybersentinel-api up

Grafana:
HTTP 200

Grafana dashboard:
CyberSentinel AI Overview

Docker → Ollama:
Verified

SOC Copilot through Docker API:
HTTP 200

GitHub Actions:
Successful

Git working tree:
Clean before documentation update
```

---

# 42. Example Local Verification Commands

Run quality checks:

```bash
uv run ruff check .
uv run pytest
```

Check DVC:

```bash
uv run dvc status
```

Check Docker:

```bash
docker compose ps
```

Check API:

```bash
curl http://127.0.0.1:8001/health
```

Check Prometheus:

```bash
curl http://127.0.0.1:9091/-/healthy
```

Check Grafana:

```bash
curl -I http://127.0.0.1:3001/login
```

Check Prometheus target:

```bash
curl -s http://127.0.0.1:9091/api/v1/targets
```

---

# 43. Responsible Use

CyberSentinel AI must be used only for authorized defensive cybersecurity activities.

Appropriate uses include:

- learning intrusion detection
- cybersecurity research
- testing defensive machine-learning pipelines
- SOC workflow demonstrations
- authorized network-security labs
- MLOps education
- portfolio demonstrations

The user is responsible for ensuring that data collection and network-security testing comply with applicable laws, policies, and authorization requirements.

---

# 44. Final Note

CyberSentinel AI is intentionally built as more than a notebook-based classification experiment.

The project demonstrates the integration of:

```text
Data Engineering
+
Machine Learning
+
Cybersecurity
+
Threat Intelligence
+
Local Generative AI
+
Backend Engineering
+
MLOps
+
Observability
+
DevOps
+
Automated Quality Assurance
```

The main engineering principle of the project is:

```text
A model prediction is not a complete security decision.
```

CyberSentinel AI therefore combines model outputs with anomaly signals, deterministic rules, risk scoring, threat context, RAG-based knowledge retrieval, human-review indicators, persistence, observability, and reproducible infrastructure.

---

# License

A production-use license has not yet been declared for this repository.

Until a license is explicitly added, normal copyright restrictions apply.
