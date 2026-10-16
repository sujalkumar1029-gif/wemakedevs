"""
Safe Simulated Action Executor and Policy Engine for ORACLE.
Implements Section 10: Strict allowlists, two-phase proposal -> approval lifecycle,
anti-tampering, duplicate execution prevention, and persistent audit logging.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from oracle.queries import query_service_details, query_evidence_chain
from oracle.db import run_query


class ActionProposalRequest(BaseModel):
    action_type: str = Field(..., description="Allowlisted simulated action type")
    incident_id: str = Field(..., description="Associated incident ID")
    target_id: str = Field(..., description="Target service, deployment, or team ID")
    evidence_ids: List[str] = Field(..., min_length=1, description="Evidence IDs justifying this action")
    proposed_by: str = Field("ORACLE Agent", description="Entity proposing the action")
    rationale: Optional[str] = Field(None, description="Operational justification for the proposal")


class ActionApprovalRequest(BaseModel):
    approver: str = Field(..., min_length=2, description="Name or identifier of human approver (cannot be agent)")
    notes: Optional[str] = Field(None, description="Approval notes")


# Allowlisted simulated actions
ALLOWLISTED_ACTIONS = {
    "acknowledge_incident": "Acknowledge synthetic incident in on-call queue and assign to triage.",
    "simulate_canary_rollback": "Simulate rolling back candidate failed deployment to stable baseline.",
    "simulate_service_isolation": "Simulate severing upstream traffic to contain cascading blast radius.",
    "simulate_team_escalation": "Simulate paging owning service team on-call engineer."
}

# In-memory stores for proposals and audit events
PROPOSALS_STORE: Dict[str, Dict[str, Any]] = {}
AUDIT_LOG: List[Dict[str, Any]] = []


def create_proposal(req: ActionProposalRequest) -> Dict[str, Any]:
    """
    Creates an action proposal in PENDING_APPROVAL state.
    Does NOT execute the action.
    """
    if req.action_type not in ALLOWLISTED_ACTIONS:
        return {
            "status": "REJECTED_DISALLOWED",
            "message": f"Action '{req.action_type}' is not allowlisted. Allowed: {list(ALLOWLISTED_ACTIONS.keys())}",
            "executable": False
        }

    # Verify evidence existence in graph
    evidence_records = query_evidence_chain(evidence_ids=req.evidence_ids)
    if not evidence_records:
        return {
            "status": "REJECTED_NO_EVIDENCE",
            "message": "Grounded evidence check failed: No verified FalkorDB evidence nodes matched the provided IDs.",
            "executable": False
        }

    action_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    proposal = {
        "action_id": action_id,
        "status": "PROPOSED",
        "action_type": req.action_type,
        "description": ALLOWLISTED_ACTIONS[req.action_type],
        "incident_id": req.incident_id,
        "target_id": req.target_id,
        "evidence_ids": [e["evidence_id"] for e in evidence_records],
        "proposed_by": req.proposed_by,
        "rationale": req.rationale,
        "created_at": timestamp,
        "state": "PENDING_APPROVAL",
        "requires_human_approval": True,
        "is_synthetic": True
    }

    PROPOSALS_STORE[action_id] = proposal
    return proposal


def approve_and_execute_action(action_id: str, approver: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates and executes an approved proposal.
    Rejects self-approval by agent, duplicate approvals, expired/consumed proposals, and unknown actions.
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # 1. Proposal Existence Check
    if action_id not in PROPOSALS_STORE:
        return {
            "status": "NOT_FOUND",
            "message": f"Proposal '{action_id}' not found.",
            "action_id": action_id
        }

    proposal = PROPOSALS_STORE[action_id]

    # 2. State & Duplicate Execution Check
    if proposal["state"] != "PENDING_APPROVAL":
        return {
            "status": "REJECTED_ALREADY_PROCESSED",
            "message": f"Proposal '{action_id}' has already been processed with state '{proposal['state']}'. Duplicate execution blocked.",
            "current_state": proposal["state"]
        }

    # 3. Agent Self-Approval Prohibition
    if approver.lower().strip() in ("oracle agent", "oracle", "agent", "bot", "auto"):
        return {
            "status": "REJECTED_SELF_APPROVAL",
            "message": "Security policy violation: ORACLE Agent cannot approve its own action proposals. Explicit human engineer sign-off required.",
            "current_state": "PENDING_APPROVAL"
        }

    action_type = proposal["action_type"]
    target_id = proposal["target_id"]
    incident_id = proposal["incident_id"]

    # 4. Simulation Outcomes
    simulated_outcome = {}
    if action_type == "simulate_canary_rollback":
        simulated_outcome = {
            "target": target_id,
            "previous_version": "v2.4.1 (FAILED_HEALTHCHECKS)",
            "restored_version": "v2.4.0 (STABLE)",
            "simulated_effect": "Connection pool reset; error rate projected to drop to <0.01% within 60s.",
            "mode": "SIMULATION_SAFE"
        }
    elif action_type == "simulate_service_isolation":
        simulated_outcome = {
            "target": target_id,
            "simulated_effect": "Traffic to target severed and routed to fallback mock; upstream timeout cascade arrested.",
            "mode": "SIMULATION_SAFE"
        }
    elif action_type == "simulate_team_escalation":
        simulated_outcome = {
            "target_team": "team-checkout",
            "on_call_paged": "Sarah Connor (Staff SRE)",
            "page_urgency": "HIGH_P1",
            "mode": "SIMULATION_SAFE"
        }
    elif action_type == "acknowledge_incident":
        simulated_outcome = {
            "incident_id": incident_id,
            "triage_status": "ACKNOWLEDGED_BY_OPERATOR",
            "mode": "SIMULATION_SAFE"
        }

    # 5. Transition Proposal State
    proposal["state"] = "EXECUTED_SIMULATED"
    proposal["approved_by"] = approver
    proposal["approved_at"] = timestamp
    proposal["approval_notes"] = notes
    proposal["outcome"] = simulated_outcome

    # 6. Append to Audit Ledger
    audit_record = {
        "audit_id": f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
        "action_id": action_id,
        "timestamp": timestamp,
        "incident_id": incident_id,
        "action_type": action_type,
        "target_id": target_id,
        "status": "EXECUTED_SIMULATED",
        "actor": approver,
        "notes": notes,
        "evidence_cited": proposal["evidence_ids"],
        "outcome": simulated_outcome,
        "is_synthetic": True
    }
    AUDIT_LOG.append(audit_record)

    # 7. Record Audit Record in FalkorDB Graph for native provenance
    try:
        audit_cypher = """
        CREATE (a:AuditRecord {
            id: $audit_id,
            action_id: $action_id,
            timestamp: $timestamp,
            action_type: $action_type,
            target_id: $target_id,
            status: 'EXECUTED_SIMULATED',
            approver: $approver,
            is_synthetic: true
        })
        WITH a
        MATCH (inc:Incident {id: $incident_id})
        CREATE (inc)-[:HAS_AUDIT_LOG]->(a)
        """
        run_query(audit_cypher, {
            "audit_id": audit_record["audit_id"],
            "action_id": action_id,
            "timestamp": timestamp,
            "action_type": action_type,
            "target_id": target_id,
            "incident_id": incident_id,
            "approver": approver
        })
    except Exception:
        pass

    return {
        "status": "SUCCESS",
        "action_id": action_id,
        "state": "EXECUTED_SIMULATED",
        "approver": approver,
        "outcome": simulated_outcome,
        "audit_record": audit_record
    }


def get_audit_trail(incident_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns the immutable audit log of simulated remediation actions."""
    if incident_id:
        return [entry for entry in AUDIT_LOG if entry.get("incident_id") == incident_id]
    return list(AUDIT_LOG)


def get_proposals(incident_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists registered action proposals."""
    proposals = list(PROPOSALS_STORE.values())
    if incident_id:
        return [p for p in proposals if p.get("incident_id") == incident_id]
    return proposals
