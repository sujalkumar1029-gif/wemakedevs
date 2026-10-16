"""
MCP (Model Context Protocol) Tool implementations for ORACLE.
Exposes narrow domain tools adhering to Section 7 of the FalkorDB Implementation Guide.
All tools are strictly read-only, validated, and bounded.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from oracle.queries import (
    query_incident_context,
    query_blast_radius,
    query_candidate_causes,
    query_deployment_history,
    query_evidence_chain,
)


# --- Input Schemas ---

class IncidentContextInput(BaseModel):
    incident_id: str = Field(..., description="Unique ID of the incident (e.g., 'INC-4091')")


class CandidateCausesInput(BaseModel):
    incident_id: str = Field(..., description="Unique ID of the incident")
    max_depth: int = Field(default=3, ge=1, le=5, description="Maximum traversal depth (1 to 5)")


class BlastRadiusInput(BaseModel):
    service_id: str = Field(..., description="ID or name of the failed service (e.g., 'svc-payment')")
    max_depth: int = Field(default=4, ge=1, le=6, description="Maximum dependency hops to traverse (1 to 6)")


class EvidenceChainInput(BaseModel):
    evidence_ids: List[str] = Field(..., min_length=1, max_length=20, description="List of evidence IDs to retrieve")


class DeploymentHistoryInput(BaseModel):
    service_id: str = Field(..., description="Service ID to check recent deployments for")
    limit: int = Field(default=10, ge=1, le=20, description="Max deployment records to return")


class ProposeResponseInput(BaseModel):
    incident_id: str = Field(..., description="Target incident ID")
    candidate_action: str = Field(..., description="Candidate remediation action (e.g., 'rollback_deployment', 'isolate_service')")
    evidence_ids: List[str] = Field(..., description="Evidence IDs supporting this proposed action")


# --- Tool Implementations ---

def get_incident_context(incident_id: str) -> Dict[str, Any]:
    """
    Fetches the incident summary, triggered alerts, affected services, and linked evidence IDs.
    Read-only.
    """
    ctx = query_incident_context(incident_id)
    if not ctx:
        return {
            "status": "NOT_FOUND",
            "message": f"Incident '{incident_id}' not found in graph.",
            "data": None,
        }
    return {
        "status": "SUCCESS",
        "tool": "get_incident_context",
        "data": ctx,
    }


def trace_candidate_causes(incident_id: str, max_depth: int = 3) -> Dict[str, Any]:
    """
    Traces multi-hop paths from alerted services to candidate causes:
    recent deployments, package vulnerabilities, and failing dependencies.
    Read-only.
    """
    causes = query_candidate_causes(incident_id, max_depth=max_depth)
    return {
        "status": "SUCCESS",
        "tool": "trace_candidate_causes",
        "data": causes,
    }


def get_blast_radius(service_id: str, max_depth: int = 4) -> Dict[str, Any]:
    """
    Computes downstream services affected by a failure in service_id via DEPENDS_ON traversal.
    Read-only.
    """
    blast = query_blast_radius(service_id, max_depth=max_depth)
    return {
        "status": "SUCCESS",
        "tool": "get_blast_radius",
        "target_service": service_id,
        "affected_count": len(blast),
        "data": blast,
    }


def get_evidence_chain(evidence_ids: List[str]) -> Dict[str, Any]:
    """
    Fetches source references, timestamps, summaries, and node links for the requested evidence IDs.
    Read-only.
    """
    evidence = query_evidence_chain(evidence_ids)
    return {
        "status": "SUCCESS",
        "tool": "get_evidence_chain",
        "count": len(evidence),
        "data": evidence,
    }


def get_deployment_history(service_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Retrieves recent deployment versions, timestamps, and rollout statuses for a service.
    Read-only.
    """
    deployments = query_deployment_history(service_id, limit=limit)
    return {
        "status": "SUCCESS",
        "tool": "get_deployment_history",
        "service_id": service_id,
        "data": deployments,
    }


def propose_response(incident_id: str, candidate_action: str, evidence_ids: List[str]) -> Dict[str, Any]:
    """
    Validates a proposed response against linked evidence and generates an approval request.
    Does NOT execute real infrastructure actions. Read-only validation.
    """
    valid_actions = {
        "simulate_canary_rollback": "Simulate rollback of recent failing deployment to previous stable version.",
        "rollback_deployment": "Roll back recent failing deployment to previous stable version.",
        "simulate_service_isolation": "Isolate failing service to prevent cascading blast radius.",
        "create_remediation_ticket": "Generate Jira/Linear ticket with graph path and evidence links.",
        "failover_traffic": "Reroute ingress traffic to healthy fallback region/cluster."
    }

    if candidate_action not in valid_actions:
        return {
            "status": "REJECTED",
            "message": f"Action '{candidate_action}' is not in policy allowlist. Allowed: {list(valid_actions.keys())}",
            "requires_approval": True,
            "executable": False
        }

    # Verify evidence existence in graph
    evidence_records = query_evidence_chain(evidence_ids)
    if not evidence_records:
        return {
            "status": "REJECTED",
            "message": "Cannot propose action without valid grounded evidence from FalkorDB.",
            "requires_approval": True,
            "executable": False
        }

    return {
        "status": "PROPOSED",
        "tool": "propose_response",
        "incident_id": incident_id,
        "proposed_action": candidate_action,
        "description": valid_actions[candidate_action],
        "grounded_evidence_ids": [e["evidence_id"] for e in evidence_records],
        "requires_human_approval": True,
        "state": "PENDING_APPROVAL"
    }


# Exported Tool Catalog
TOOL_DEFINITIONS = [
    {
        "name": "get_incident_context",
        "description": "Fetches incident summary, alerts, observed services, and evidence IDs.",
        "input_schema": IncidentContextInput.model_json_schema(),
        "handler": get_incident_context,
        "read_only": True,
    },
    {
        "name": "trace_candidate_causes",
        "description": "Traces multi-hop paths from alerted services to candidate causes (deployments, vulnerabilities).",
        "input_schema": CandidateCausesInput.model_json_schema(),
        "handler": trace_candidate_causes,
        "read_only": True,
    },
    {
        "name": "get_blast_radius",
        "description": "Computes dependent services impacted by a failure in target service.",
        "input_schema": BlastRadiusInput.model_json_schema(),
        "handler": get_blast_radius,
        "read_only": True,
    },
    {
        "name": "get_evidence_chain",
        "description": "Fetches verified evidence logs, scan reports, and metric anomalies by ID.",
        "input_schema": EvidenceChainInput.model_json_schema(),
        "handler": get_evidence_chain,
        "read_only": True,
    },
    {
        "name": "get_deployment_history",
        "description": "Retrieves recent deployment versions and statuses for a service.",
        "input_schema": DeploymentHistoryInput.model_json_schema(),
        "handler": get_deployment_history,
        "read_only": True,
    },
    {
        "name": "propose_response",
        "description": "Validates a candidate response action against evidence. Requires human approval.",
        "input_schema": ProposeResponseInput.model_json_schema(),
        "handler": propose_response,
        "read_only": True,
    },
]
