"""
Integration tests for ORACLE FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from oracle.api import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["falkordb_connected"] is True


def test_api_seed():
    response = client.post("/api/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["incident_id"] == "INC-4091"


def test_api_list_incidents():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert any(inc["id"] == "INC-4091" for inc in data["incidents"])


def test_api_investigate_incident():
    response = client.get("/api/investigate/INC-4091")
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == "INC-4091"
    assert data["investigation_status"] == "COMPLETED"
    assert data["root_cause"] is not None
    assert len(data["blast_radius"]) >= 3


def test_api_tools_catalog():
    response = client.get("/api/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_incident_context" in tool_names
    assert "get_blast_radius" in tool_names
    assert "propose_response" in tool_names


def test_api_action_approval_gate():
    # Unapproved action must be rejected with 403
    unapproved_payload = {
        "action_type": "simulate_canary_rollback",
        "incident_id": "INC-4091",
        "target_id": "dep-pay-v2.4.1",
        "evidence_ids": ["EVI-901"],
        "approved": False,
        "approver": None
    }
    res_unapproved = client.post("/api/actions/execute", json=unapproved_payload)
    assert res_unapproved.status_code == 403

    # Approved action must execute
    approved_payload = {
        "action_type": "simulate_canary_rollback",
        "incident_id": "INC-4091",
        "target_id": "dep-pay-v2.4.1",
        "evidence_ids": ["EVI-901", "EVI-903"],
        "approved": True,
        "approver": "Alex Murphy (Staff SRE)"
    }
    res_approved = client.post("/api/actions/execute", json=approved_payload)
    assert res_approved.status_code == 200
    data = res_approved.json()
    assert data["status"] == "EXECUTED_SIMULATED"
    assert data["approved"] is True


def test_api_audit_trail():
    response = client.get("/api/audit")
    assert response.status_code == 200
    data = response.json()
    assert "audit_log" in data
    assert len(data["audit_log"]) > 0


def test_api_graph_topology():
    response = client.get("/api/graph/topology")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 20
    assert len(data["edges"]) >= 25


def test_api_frontend_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "ORACLE Incident Agent" in response.text
