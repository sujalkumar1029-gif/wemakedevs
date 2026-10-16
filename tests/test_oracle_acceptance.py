"""
ORACLE Section 14 Acceptance Test Suite.
Verifies all master criteria:
1. Fresh environment starts and seed script is repeatable.
2. Known incident returns expected connected services.
3. Disconnected negative-test service is excluded.
4. Competing hypotheses (deployment vs CVE) are evaluated and differentiated with evidence.
5. Findings explicitly categorized into OBSERVED, INFERRED, UNKNOWN.
6. Missing evidence produces an uncertainty message, not a fabricated cause.
7. Invalid IDs and disallowed actions are rejected.
8. Unapproved action cannot execute and agent cannot self-approve.
9. Approved simulated action writes an audit record.
"""

import pytest
from oracle.seed_data import seed_database
from oracle.queries import query_incident_context, query_blast_radius, query_candidate_causes
from oracle.mcp_tools import (
    get_incident_context,
    get_blast_radius,
    propose_response,
    get_vulnerable_services,
    get_service_owner
)
from oracle.agent import OracleAgent
from oracle.actions import (
    ActionProposalRequest,
    create_proposal,
    approve_and_execute_action,
    get_audit_trail,
)


@pytest.fixture(scope="module", autouse=True)
def setup_seeded_graph():
    """Ensures deterministic graph state for test suite."""
    stats = seed_database()
    assert stats["status"] == "SUCCESS"
    assert stats["total_nodes"] >= 20
    assert stats["total_edges"] >= 25


def test_seed_script_is_repeatable():
    """Criteria: Fresh environment starts using documented steps; seed script is repeatable."""
    stats1 = seed_database()
    stats2 = seed_database()
    assert stats1["total_nodes"] == stats2["total_nodes"]
    assert stats1["total_edges"] == stats2["total_edges"]
    assert stats1["incident_id"] == "INC-4091"
    assert stats1["is_synthetic"] is True


def test_known_incident_connected_services():
    """Criteria: Known incident returns expected connected services."""
    ctx = query_incident_context("INC-4091")
    assert ctx is not None
    assert ctx["incident_id"] == "INC-4091"

    service_names = {s["name"] for s in ctx["observed_services"]}
    assert "api-gateway" in service_names
    assert "order-service" in service_names
    assert "payment-service" in service_names


def test_disconnected_service_is_excluded():
    """Criteria: Disconnected negative test service is excluded from blast radius."""
    blast = query_blast_radius("svc-payment", max_depth=4)
    affected_services = [b["affected_service"] for b in blast]

    # Connected upstream consumers
    assert "order-service" in affected_services
    assert "api-gateway" in affected_services
    assert "web-frontend" in affected_services

    # Disconnected negative test service must NOT appear
    assert "analytics-pipeline" not in affected_services
    assert "inventory-service" not in affected_services


def test_competing_hypotheses_and_differentiation():
    """Criteria: Recent deployment and vulnerability remain competing hypotheses until evidence differentiates them."""
    agent = OracleAgent()
    report = agent.investigate("INC-4091")

    assert report["investigation_status"] == "COMPLETED"
    hypotheses = report["hypotheses_evaluated"]
    assert len(hypotheses) >= 2

    categories = {h["category"] for h in hypotheses}
    assert "DEPLOYMENT" in categories
    assert "VULNERABILITY" in categories

    deploy_hypo = next(h for h in hypotheses if h["category"] == "DEPLOYMENT")
    vuln_hypo = next(h for h in hypotheses if h["category"] == "VULNERABILITY")

    # Deployment is confirmed as root cause because of immediate temporal match and health failure
    assert deploy_hypo["status"] == "CONFIRMED_ROOT_CAUSE"
    assert deploy_hypo["confidence_score"] > 0.8
    assert "EVI-901" in deploy_hypo["supporting_evidence_ids"]

    # Vulnerability is refuted due to counterevidence (scan 4 days prior, zero exploit traffic)
    assert vuln_hypo["status"] == "REFUTED"
    assert vuln_hypo["temporal_match"] is False
    assert vuln_hypo["counter_evidence"] is not None


def test_findings_explicit_categorization():
    """Criteria: Findings are separated into OBSERVED, INFERRED, and UNKNOWN."""
    agent = OracleAgent()
    report = agent.investigate("INC-4091")
    findings = report["findings"]

    categories = {f["category"] for f in findings}
    assert "OBSERVED" in categories
    assert "INFERRED" in categories
    assert "UNKNOWN" in categories


def test_missing_evidence_produces_uncertainty():
    """Criteria: Missing evidence produces an uncertainty message, not a fabricated root cause."""
    agent = OracleAgent()
    result = agent.investigate("INC-NONEXISTENT-999")
    assert result["status"] == "NOT_FOUND"
    assert "not found" in result["message"].lower()


def test_invalid_disallowed_actions_rejected():
    """Criteria: Invalid actions outside allowlist are rejected."""
    req = ActionProposalRequest(
        action_type="delete_production_database",
        incident_id="INC-4091",
        target_id="svc-payment",
        evidence_ids=["EVI-901"],
    )
    res = create_proposal(req)
    assert res["status"] == "REJECTED_DISALLOWED"


def test_agent_cannot_self_approve():
    """Criteria: Agent cannot approve its own proposals; human approval required."""
    req = ActionProposalRequest(
        action_type="simulate_canary_rollback",
        incident_id="INC-4091",
        target_id="dep-pay-v2.4.1",
        evidence_ids=["EVI-901"],
        proposed_by="ORACLE Agent"
    )
    proposal = create_proposal(req)
    action_id = proposal["action_id"]

    res = approve_and_execute_action(action_id, approver="ORACLE Agent")
    assert res["status"] == "REJECTED_SELF_APPROVAL"


def test_approved_simulated_action_writes_audit_record():
    """Criteria: Approved simulated action writes an audit record."""
    req = ActionProposalRequest(
        action_type="simulate_canary_rollback",
        incident_id="INC-4091",
        target_id="dep-pay-v2.4.1",
        evidence_ids=["EVI-901", "EVI-903"],
        proposed_by="ORACLE Agent"
    )
    proposal = create_proposal(req)
    action_id = proposal["action_id"]

    res = approve_and_execute_action(
        action_id=action_id,
        approver="Sarah Connor (Incident Commander)",
        notes="Rollback confirmed by Lead SRE"
    )
    assert res["status"] == "SUCCESS"
    assert res["state"] == "EXECUTED_SIMULATED"

    # Verify audit log persistence
    trail = get_audit_trail("INC-4091")
    executed_events = [t for t in trail if t["action_id"] == action_id]
    assert len(executed_events) == 1
    assert executed_events[0]["actor"] == "Sarah Connor (Incident Commander)"
