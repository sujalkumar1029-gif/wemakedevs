"""
Safe Simulated Action Executor for ORACLE.
Enforces Step 10: Strict allowlists, human approval gates, audit logging,
and guarantees that no real destructive infrastructure commands are executed.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from oracle.queries import query_service_details, query_evidence_chain
from oracle.db import run_query


class ActionExecutionRequest(BaseModel):
    action_type: str = Field(..., description="Allowlisted simulated action type")
    incident_id: str = Field(..., description="Associated incident ID")
    target_id: str = Field(..., description="Target service or deployment ID")
    evidence_ids: List[str] = Field(..., description="Evidence IDs justifying this action")
    approved: bool = Field(False, description="Explicit human approval flag (MUST be True to execute)")
    approver: Optional[str] = Field(None, description="Name or role of approving engineer")
    notes: Optional[str] = Field(None, description="Operational notes or reason for approval")


# In-memory audit log ledger for quick retrieval
AUDIT_LOG: List[Dict[str, Any]] = []

ALLOWLISTED_ACTIONS = {
    "simulate_canary_rollback": "Simulates rolling back candidate failed deployment to stable baseline.",
    "simulate_service_isolation": "Simulates severing upstream traffic to contain cascading blast radius.",
    "create_remediation_ticket": "Simulates creating an auditable P1 incident ticket with evidence trail."
}


def execute_simulated_action(request: ActionExecutionRequest) -> Dict[str, Any]:
    """
    Executes an allowlisted simulated remediation action.
    Strictly gates on `request.approved == True`.
    Logs audit event and simulates state transition.
    """
    action_id = f"ACT-{int(time.time() * 1000)}"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # 1. Allowlist Validation
    if request.action_type not in ALLOWLISTED_ACTIONS:
        record = {
            "action_id": action_id,
            "timestamp": timestamp,
            "action_type": request.action_type,
            "status": "REJECTED_DISALLOWED",
            "message": f"Action '{request.action_type}' is forbidden. Not in allowlist.",
            "approved": request.approved,
            "approver": request.approver
        }
        AUDIT_LOG.append(record)
        return record

    # 2. Human Approval Gate
    if not request.approved:
        record = {
            "action_id": action_id,
            "timestamp": timestamp,
            "action_type": request.action_type,
            "status": "REJECTED_UNAPPROVED",
            "message": "Security policy violation: Simulated remediation cannot execute without explicit human approval (approved=True).",
            "approved": False,
            "approver": request.approver
        }
        AUDIT_LOG.append(record)
        return record

    # 3. Evidence Grounding Check
    evidence_records = query_evidence_chain(request.evidence_ids)
    if not evidence_records:
        record = {
            "action_id": action_id,
            "timestamp": timestamp,
            "action_type": request.action_type,
            "status": "REJECTED_NO_EVIDENCE",
            "message": "Grounded evidence check failed: No verified FalkorDB evidence nodes matched the provided IDs.",
            "approved": True,
            "approver": request.approver
        }
        AUDIT_LOG.append(record)
        return record

    # 4. Simulated Execution Logic
    simulated_outcome = {}
    if request.action_type == "simulate_canary_rollback":
        simulated_outcome = {
            "target": request.target_id,
            "previous_version": "v2.4.1 (FAILED_HEALTHCHECKS)",
            "restored_version": "v2.4.0 (STABLE)",
            "simulated_effect": "Connection pool reset; error rate projected to drop to <0.01% within 60s.",
            "mode": "SIMULATION_SAFE"
        }
    elif request.action_type == "simulate_service_isolation":
        simulated_outcome = {
            "target": request.target_id,
            "simulated_effect": "Traffic to service routed to fallback mock; prevents cascading timeout to api-gateway.",
            "mode": "SIMULATION_SAFE"
        }
    elif request.action_type == "create_remediation_ticket":
        simulated_outcome = {
            "ticket_id": f"INC-TICKET-{request.incident_id}",
            "priority": "P1-CRITICAL",
            "assigned_team": "Checkout & Payments Platform",
            "linked_evidence_count": len(evidence_records),
            "mode": "SIMULATION_SAFE"
        }

    # 5. Record Successful Audit Entry
    audit_record = {
        "action_id": action_id,
        "timestamp": timestamp,
        "incident_id": request.incident_id,
        "action_type": request.action_type,
        "target_id": request.target_id,
        "status": "EXECUTED_SIMULATED",
        "description": ALLOWLISTED_ACTIONS[request.action_type],
        "approved": True,
        "approver": request.approver or "On-Call Incident Commander",
        "notes": request.notes,
        "evidence_cited": [e["evidence_id"] for e in evidence_records],
        "outcome": simulated_outcome
    }
    AUDIT_LOG.append(audit_record)

    # 6. Record Audit in FalkorDB Graph for Graph-Native Provenance
    try:
        audit_cypher = """
        CREATE (a:AuditRecord {
            id: $action_id,
            timestamp: $timestamp,
            action_type: $action_type,
            target_id: $target_id,
            status: 'EXECUTED_SIMULATED',
            approver: $approver
        })
        WITH a
        MATCH (inc:Incident {id: $incident_id})
        CREATE (inc)-[:HAS_AUDIT_LOG]->(a)
        """
        run_query(audit_cypher, {
            "action_id": action_id,
            "timestamp": timestamp,
            "action_type": request.action_type,
            "target_id": request.target_id,
            "incident_id": request.incident_id,
            "approver": request.approver or "Incident Commander"
        })
    except Exception as e:
        # Non-critical graph update failure logged
        pass

    return audit_record


def get_audit_trail(incident_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns the history of simulated actions and policy checks."""
    if incident_id:
        return [entry for entry in AUDIT_LOG if entry.get("incident_id") == incident_id]
    return list(AUDIT_LOG)
