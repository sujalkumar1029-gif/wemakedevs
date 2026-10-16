# ORACLE: Operational Reasoning and Causal Analysis through Linked Evidence

[![FalkorDB Track 01](https://img.shields.io/badge/FalkorDB-Track%2001-3B82F6)](https://docs.falkordb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com)

**ORACLE** is an evidence-grounded incident investigation agent built natively on **FalkorDB** for **Graph Hacks Track 01: Agents That Act on Connected Data**.

---

## 🎯 Track 01 Core Principle

> **"FalkorDB must perform the connected-data reasoning. The agent selects tools and explains evidence; it never invents graph relationships or bypasses the action policy."**

When complex microservice outages occur, root causes are obscured by cascading alerts across multiple downstream and upstream dependencies. ORACLE uses FalkorDB to:
1. **Trace Multi-Hop Causality**: Traverses 2–4 hop dependency chains from alerted consumer services to the root failing provider.
2. **Differentiate Competing Explanations**: Resolves competing hypotheses (e.g. a recent bad canary deployment vs a newly published package vulnerability) through temporal and graph-grounded evidence.
3. **Compute Downstream Blast Radius**: Evaluates consumer blast radius using reverse `DEPENDS_ON` traversal while strictly excluding disconnected negative-test services.
4. **Enforce Safe Simulated Action**: Gated by a human approval policy that simulates rollback actions and writes an auditable provenance trail directly to FalkorDB.

---

## 🏛️ Graph Schema & Topology

```
(:Incident)-[:HAS_ALERT]->(:Alert)-[:OBSERVED_ON]->(:Service)
(:Service)-[:DEPENDS_ON]->(:Service)          // (consumer)-[:DEPENDS_ON]->(provider)
(:Service)-[:USES]->(:Package)-[:HAS_VULNERABILITY]->(:Vulnerability)
(:Service)-[:DEPLOYED_IN]->(:Deployment)
(:Team)-[:OWNS]->(:Service)
(:Evidence)-[:SUPPORTS]->(:Incident)
(:Evidence)-[:OBSERVED]->(:Service)
(:Evidence)-[:REFERS_TO]->(:Deployment)
```

### Dependency Convention
- `(consumer:Service)-[:DEPENDS_ON]->(provider:Service)` means consumer depends on provider.
- **Blast Radius Query**: Traverses reverse incoming edges from the target failing service to identify all upstream consumers that will degrade or fail.

---

## 🛠️ MCP Tool Catalog

| Tool Name | Operation | Purpose | Read-Only |
| :--- | :--- | :--- | :---: |
| `get_incident_context` | Query | Fetches incident metadata, observed alerts, and evidence IDs | Yes |
| `trace_candidate_causes` | Traversal | Explores candidate causes (failed deployments, vulnerable packages) | Yes |
| `get_blast_radius` | Graph Alg | Calculates upstream consumer blast radius with bounded hops | Yes |
| `get_evidence_chain` | Query | Fetches verified logs, scan reports, and latency telemetry by ID | Yes |
| `get_deployment_history` | Query | Retrieves recent deployments, timestamps, and commit SHAs | Yes |
| `propose_response` | Validation | Validates remediation proposal against evidence; human-gated | Yes |

---

## 🚀 Quick Start Guide

### 1. Start FalkorDB
```bash
docker run -d --name falkordb --restart unless-stopped -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
```
- **Cypher Database Port**: `localhost:6379`
- **FalkorDB Browser UI**: [http://localhost:3000](http://localhost:3000)

### 2. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Seed Synthetic Graph
```bash
python -m oracle.seed_data
```

### 4. Run Acceptance Test Suite
```bash
pytest -v
```

### 5. Launch ORACLE Investigation Console
```bash
uvicorn oracle.api:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🧪 Acceptance Test Coverage

The test suite in `tests/test_oracle_acceptance.py` validates all 8 key acceptance criteria:
- [x] **Repeatable Seeding**: Idempotent reset-and-seed guarantees deterministic node/edge counts.
- [x] **Multi-Hop Traversal**: Connects alerts on `api-gateway` and `order-service` to root cause on `payment-service`.
- [x] **Negative Test Exclusion**: Proves disconnected services (`analytics-pipeline`) are excluded from blast radius.
- [x] **Hypothesis Differentiation**: Confirms `dep-pay-v2.4.1` as root cause; refutes `CVE-2026-4412` via temporal counterevidence.
- [x] **Uncertainty on Missing Data**: Missing or invalid incident IDs return explicit uncertainty messages.
- [x] **Safety Allowlist**: Arbitrary/destructive write commands are blocked.
- [x] **Human Approval Gate**: Unapproved actions are rejected (`403 Forbidden`).
- [x] **Audited Simulated Remediation**: Approved simulated actions write a permanent audit entry to FalkorDB.

---

## 🎥 3-Minute Demo Script

1. **0:00–0:30**: Introduce `INC-4091` ("Cascading Checkout Failure") with two plausible explanations (Canary rollout vs CVE-2026-4412).
2. **0:30–1:10**: Trigger ORACLE agent loop; observe MCP tool calls and the multi-hop graph path in FalkorDB Browser.
3. **1:10–1:50**: Review the Hypotheses Comparison table; highlight the counterevidence refuting CVE-2026-4412 and confirming `dep-pay-v2.4.1`.
4. **1:50–2:30**: Show the downstream blast radius (`order-service` → `api-gateway` → `web-frontend`) and the proposed `simulate_canary_rollback`.
5. **2:30–3:00**: Click **Approve Rollback** in the safety modal; inspect the audit entry and graph provenance.
