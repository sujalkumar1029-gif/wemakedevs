# ImpactGraph: Operational Reasoning & Causal Analysis through Linked Evidence

> **Trace the cause. Map the impact. Act with evidence.**

[![FalkorDB Track 01](https://img.shields.io/badge/FalkorDB-Track%2001-3B82F6)](https://docs.falkordb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6.svg)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF.svg)](https://vitejs.dev)

**ImpactGraph** (ORACLE) is a graph-native AI incident investigation agent that uses **FalkorDB** and **MCP tools** to trace dependencies, compare evidence-backed hypotheses, assess blast radius, and propose auditable responses for **Graph Hacks Track 01: Agents That Act on Connected Data**.

---

## 🎯 Track 01 Core Principle

> **"The graph is the source of connected operational context, MCP provides controlled tools to investigate it, and the agent uses retrieved evidence to explain its conclusions. FalkorDB performs connected-data reasoning. The agent selects tools and explains evidence; it never invents graph relationships or bypasses the action policy."**

When complex microservice outages occur, root causes are obscured by cascading alerts across multiple downstream and upstream dependencies. ORACLE uses FalkorDB to:
1. **Trace Multi-Hop Causality**: Traverses 2–4 hop dependency chains from alerted consumer services to the root failing provider.
2. **Differentiate Competing Explanations**: Resolves competing hypotheses (e.g. a recent bad canary deployment vs a newly published package vulnerability) through temporal and graph-grounded evidence.
3. **Explicit Finding Categorization**: Segregates every insight into `OBSERVED` (directly supported by graph records), `INFERRED` (hypotheses supported by evidence), and `UNKNOWN` (telemetry gaps honestly reported).
4. **Compute Downstream Blast Radius**: Evaluates consumer blast radius using reverse `DEPENDS_ON` traversal while strictly excluding disconnected negative-test services.
5. **Enforce Safe Simulated Action**: Gated by a strict human approval policy that simulates rollback actions, prevents agent self-approval, blocks duplicate executions, and writes an auditable provenance trail directly to FalkorDB.

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

### Key Graph Entities & Properties (Labeled `is_synthetic: true`)
- **`Incident`**: `id`, `title`, `description`, `severity`, `status`, `created_at`
- **`Alert`**: `id`, `signal`, `alert_type`, `observed_value`, `threshold`, `timestamp`, `source`
- **`Service`**: `id`, `name`, `criticality`, `health`, `status`
- **`Package`**: `id`, `name`, `version`, `risk_status`
- **`Vulnerability`**: `id`, `title`, `severity`, `affected_version`, `published_at`
- **`Deployment`**: `id`, `version`, `timestamp`, `status`, `commit_sha`, `author`
- **`Evidence`**: `id`, `kind`, `source_type`, `source_ref`, `observed_at`, `observation`, `summary`
- **`Team`**: `id`, `name`, `on_call`

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
| `get_vulnerable_services` | Query | Discovers services consuming packages affected by a CVE | Yes |
| `get_service_owner` | Query | Retrieves team ownership and on-call contact for a given service | Yes |
| `propose_response` | Validation | Validates remediation proposal against evidence; human-gated | Yes |

---

## 🔒 Safety Policy & Simulation Lifecycle

1. **Proposal**: Agent creates proposal via `POST /actions/propose` (status: `PENDING_APPROVAL`).
2. **Approval Gate**: Human engineer explicitly approves via `POST /actions/{id}/approve`.
   - **Anti-Self-Approval**: Agent cannot approve its own proposals (returns `403 Forbidden`).
   - **Allowlist Enforced**: Only allowlisted safe simulated actions can execute (`simulate_canary_rollback`, `simulate_service_isolation`, `simulate_team_escalation`, `acknowledge_incident`).
   - **Anti-Duplicate**: Already-consumed proposals reject duplicate execution (returns `400 Bad Request`).
   - **Zero Destructive Commands**: Never touches real production infrastructure or runs shell commands.
3. **Audit Ledger**: Complete state transition, approver handle, timestamps, and simulated outcome are recorded in FalkorDB and the audit trail.

---

## 🚀 Quick Start Guide

### ⚡ One-Click Runners (Automated Setup & Launch)

#### Windows:
Double-click `run.bat` in File Explorer or run in Command Prompt:
```cmd
run.bat
```
*Other options:* `run.bat test` (run test suite), `run.bat seed` (re-seed graph), `run.bat dev` (FastAPI + Vite dev server).

#### Linux / macOS / WSL:
```bash
./run.sh
```
*Other options:* `./run.sh test` (run test suite), `./run.sh seed` (re-seed graph), `./run.sh dev` (FastAPI + Vite dev server).

---

### Manual Step-by-Step Setup

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

### 4. Run Acceptance Test Suite (18/18 Passing)
```bash
pytest -v
```

### 5. Launch ORACLE Cockpit
```bash
# Start FastAPI backend (serves API & React UI)
uvicorn oracle.api:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

*(Optional)* Run React dev server with Hot-Module-Replacement:
```bash
cd frontend
npm run dev
# Vite runs at http://localhost:5173
```

---

## 📡 REST API Contracts

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | FalkorDB connectivity and engine status |
| `POST` | `/seed` | Idempotent reset-and-seed of synthetic graph |
| `GET` | `/incidents` | List all synthetic incidents |
| `GET` | `/incidents/{id}` | Retrieve incident details and observed alerts |
| `POST` | `/incidents/{id}/investigate` | Run ORACLE reasoning engine over MCP tools |
| `GET` | `/incidents/{id}/evidence` | Retrieve grounded evidence records for incident |
| `POST` | `/actions/propose` | Create action proposal in `PENDING_APPROVAL` state |
| `POST` | `/actions/{id}/approve` | Human approval and safe simulation execution |
| `GET` | `/audit` | Query immutable audit ledger |
| `GET` | `/api/graph/topology` | Full graph nodes and edges for Cytoscape |

---

## 🧪 Acceptance Test Coverage

The test suite in `tests/` validates all Master Engineering Prompt criteria:
- [x] **Repeatable Seeding**: Idempotent reset-and-seed guarantees deterministic node/edge counts.
- [x] **Multi-Hop Traversal**: Connects alerts on `api-gateway` and `order-service` to root cause on `payment-service`.
- [x] **Negative Test Exclusion**: Proves disconnected services (`analytics-pipeline`) are excluded from blast radius.
- [x] **Hypothesis Differentiation**: Confirms `dep-pay-v2.4.1` as root cause; refutes `CVE-2026-4412` via temporal counterevidence.
- [x] **Finding Categorization**: Formats findings into `OBSERVED`, `INFERRED`, and `UNKNOWN`.
- [x] **Uncertainty on Missing Data**: Missing or invalid incident IDs return explicit uncertainty messages.
- [x] **Safety Allowlist**: Arbitrary/destructive write commands are blocked.
- [x] **Anti-Self-Approval**: Agent cannot approve its own proposals (`403 Forbidden`).
- [x] **Anti-Duplicate Approval**: Consumed proposals reject duplicate execution (`400 Bad Request`).
- [x] **Audited Simulated Remediation**: Approved simulated actions write a permanent audit entry to FalkorDB.
- [x] **Frontend Production Build**: Vite React-TS production build compiles with zero errors.

---

## 🎥 3-Minute Demo Script

1. **0:00–0:30**: Introduce synthetic incident `INC-4091` ("Cascading Checkout Failure") with two plausible explanations:
   - Canary rollout `dep-pay-v2.4.1` vs Package Vulnerability `CVE-2026-4412`.
2. **0:30–1:10**: Click **⚡ Run Investigation**; observe the 7-step MCP tool loop executed across FalkorDB and the visual multi-hop graph rendered in Cytoscape.
3. **1:10–1:50**: Review the **Grounded Findings Breakdown** (`OBSERVED`, `INFERRED`, `UNKNOWN`) and the **Hypotheses Comparison**; explain how counterevidence refutes CVE-2026-4412 (scan 4 days old, zero exploit traffic) and confirms `dep-pay-v2.4.1` (connection pool starved 45s post-rollout).
4. **1:50–2:30**: Inspect the **Downstream Blast Radius** (`order-service` → `api-gateway` → `web-frontend`), proving `analytics-pipeline` is untouched.
5. **2:30–3:00**: Click **Approve Simulated Action**; note the human approval gate blocking agent self-approval; enter engineer handle; execute the simulation; and inspect the resulting entry in the audit ledger and FalkorDB graph.
