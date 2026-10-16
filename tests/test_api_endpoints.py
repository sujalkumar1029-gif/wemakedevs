"""
Integration tests for all Section 11 FastAPI contracts:
- GET /health
- GET /incidents
- GET /incidents/{id}
- POST /incidents/{id}/investigate
- GET /incidents/{id}/evidence
- POST /actions/propose
- POST /actions/{id}/approve
- GET /audit
- MCP tool endpoints
"""

import pytest
from fastapi.testclient import TestClient
from oracle.api import app
from oracle.seed_data import seed_database

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    seed_database()


def test_endpoint_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["falkordb_connected"] is True
    assert data["is_synthetic"] is True


def test_endpoint_incidents_list():
    res = client.get("/incidents")
    assert res.status_code == 200
    data = res.json()
    assert "incidents" in data
    assert any(inc["id"] == "INC-4091" for inc in data["incidents"])


def test_endpoint_incident_detail():
    res = client.get("/incidents/INC-4091")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == "INC-4091"
    assert len(data["alerts"]) >= 3
    assert len(data["observed_services"]) >= 3


def test_endpoint_incident_detail_404():
    res = client.get("/incidents/INC-NONEXISTENT")
    assert res.status_code == 404


def test_endpoint_investigate():
    res = client.post("/incidents/INC-4091/investigate")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == "INC-4091"
    assert data["investigation_status"] == "COMPLETED"

    # Verify explicit finding categories: OBSERVED, INFERRED, UNKNOWN
    categories = {f["category"] for f in data["findings"]}
    assert "OBSERVED" in categories
    assert "INFERRED" in categories
    assert "UNKNOWN" in categories

    # Verify hypotheses comparison
    hypo_names = [h["name"] for h in data["hypotheses_evaluated"]]
    assert any("Canary" in name for name in hypo_names)
    assert any("CVE" in name or "Vulnerability" in name for name in hypo_names)

    # Verify blast radius & ownership
    assert len(data["blast_radius"]) >= 3
    assert data["service_ownership"]["team_name"] == "Checkout & Payments Platform"


def test_endpoint_incident_evidence():
    res = client.get("/incidents/INC-4091/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == "INC-4091"
    assert data["evidence_count"] >= 3
    evidence_ids = [e["evidence_id"] for e in data["evidence"]]
    assert "EVI-901" in evidence_ids
    assert "EVI-902" in evidence_ids
    assert "EVI-903" in evidence_ids


def test_endpoint_action_proposal_and_approval_lifecycle():
    # 1. Propose action
    prop_payload = {
        "action_type": "simulate_canary_rollback",
        "incident_id": "INC-4091",
        "target_id": "dep-pay-v2.4.1",
        "evidence_ids": ["EVI-901", "EVI-903"],
        "proposed_by": "ORACLE Agent",
        "rationale": "Rollback connection pool leak container"
    }
    prop_res = client.post("/actions/propose", json=prop_payload)
    assert prop_res.status_code == 200
    prop_data = prop_res.json()
    action_id = prop_data["action_id"]
    assert prop_data["state"] == "PENDING_APPROVAL"

    # 2. Self-approval by agent must be rejected with 403
    self_approve_res = client.post(f"/actions/{action_id}/approve", json={"approver": "ORACLE Agent"})
    assert self_approve_res.status_code == 403
    assert "cannot approve its own" in self_approve_res.json()["detail"]

    # 3. Explicit human approval executes the simulation
    human_approve_res = client.post(f"/actions/{action_id}/approve", json={
        "approver": "Sarah Connor (Staff SRE)",
        "notes": "Verified connection pool drop in Prometheus. Rollback approved."
    })
    assert human_approve_res.status_code == 200
    human_data = human_approve_res.json()
    assert human_data["state"] == "EXECUTED_SIMULATED"
    assert human_data["approver"] == "Sarah Connor (Staff SRE)"
    assert "outcome" in human_data

    # 4. Duplicate approval on consumed proposal must be rejected with 400
    dup_res = client.post(f"/actions/{action_id}/approve", json={"approver": "Alex Murphy"})
    assert dup_res.status_code == 400
    assert "already been processed" in dup_res.json()["detail"]


def test_endpoint_audit_trail():
    res = client.get("/audit")
    assert res.status_code == 200
    data = res.json()
    assert "audit_log" in data
    assert len(data["audit_log"]) >= 1
    recent = data["audit_log"][-1]
    assert recent["status"] == "EXECUTED_SIMULATED"
    assert recent["actor"] == "Sarah Connor (Staff SRE)"


def test_endpoint_mcp_tools():
    # 1. get_vulnerable_services
    res_vuln = client.get("/api/tools/vulnerable_services?vulnerability_id=CVE-2026-4412")
    assert res_vuln.status_code == 200
    assert res_vuln.json()["count"] >= 2

    # 2. get_service_owner
    res_owner = client.get("/api/tools/service_owner?service_id=svc-payment")
    assert res_owner.status_code == 200
    assert res_owner.json()["data"]["team_name"] == "Checkout & Payments Platform"

    # 3. get_deployment_history
    res_dep = client.get("/api/tools/deployment_history?service_id=svc-payment")
    assert res_dep.status_code == 200
    assert len(res_dep.json()["data"]) >= 2
