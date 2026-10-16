"""
MCP (Model Context Protocol) Tool implementations for ORACLE.
Exposes narrow domain tools adhering to Section 8 of the Master Engineering Prompt.
All tools are strictly read-only, validated, and bounded.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from oracle.queries import (
    query_incident_context,
    query_blast_radius,
    query_candidate_causes,
    query_deployment_history,
    query_evidence_chain,
    query_vulnerable_services,
    query_service_owner,
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
    incident_id: Optional[str] = Field(None, description="Target incident ID to fetch all supporting evidence for")
    evidence_ids: Optional[List[str]] = Field(None, description="Explicit list of evidence IDs to retrieve")


class DeploymentHistoryInput(BaseModel):
    service_id: str = Field(..., description="Service ID to check recent deployments for")
    limit: int = Field(default=10, ge=1, le=20, description="Max deployment records to return")


class VulnerableServicesInput(BaseModel):
    vulnerability_id: str = Field(..., description="CVE ID or identifier (e.g., 'CVE-2026-4412')")


class ServiceOwnerInput(BaseModel):
    service_id: str = Field(..., description="Target service ID or name")


class ProposeResponseInput(BaseModel):
    incident_id: str = Field(..., description="Target incident ID")
    candidate_action: str = Field(..., description="Candidate remediation action (e.g., 'simulate_canary_rollback')")
    evidence_ids: List[str] = Field(..., description="Evidence IDs supporting this proposed action")


# --- Tool Handlers ---

def get_incident_context(incident_id: str) -> Dict[str, Any]:
    """Fetches incident summary, alerts, observed services, and evidence IDs."""
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
    """Traces multi-hop paths from alerted services to candidate causes (deployments, vulnerabilities)."""
    causes = query_candidate_causes(incident_id, max_depth=max_depth)
    return {
        "status": "SUCCESS",
        "tool": "trace_candidate_causes",
        "data": causes,
    }


def get_blast_radius(service_id: str, max_depth: int = 4) -> Dict[str, Any]:
    """Computes downstream services affected by a failure in service_id via DEPENDS_ON reverse traversal."""
    blast = query_blast_radius(service_id, max_depth=max_depth)
    return {
        "status": "SUCCESS",
        "tool": "get_blast_radius",
        "target_service": service_id,
        "affected_count": len(blast),
        "data": blast,
    }


def get_evidence_chain(incident_id: Optional[str] = None, evidence_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Fetches source references, timestamps, observations, and node links for evidence records."""
    evidence = query_evidence_chain(evidence_ids=evidence_ids, incident_id=incident_id)
    return {
        "status": "SUCCESS",
        "tool": "get_evidence_chain",
        "count": len(evidence),
        "data": evidence,
    }


def get_deployment_history(service_id: str, limit: int = 10) -> Dict[str, Any]:
    """Retrieves recent deployment versions, timestamps, and rollout statuses for a service."""
    deployments = query_deployment_history(service_id, limit=limit)
    return {
        "status": "SUCCESS",
        "tool": "get_deployment_history",
        "service_id": service_id,
        "data": deployments,
    }


def get_vulnerable_services(vulnerability_id: str) -> Dict[str, Any]:
    """Discovers services consuming packages affected by the specified vulnerability."""
    services = query_vulnerable_services(vulnerability_id)
    return {
        "status": "SUCCESS",
        "tool": "get_vulnerable_services",
        "vulnerability_id": vulnerability_id,
        "count": len(services),
        "data": services,
    }


def get_service_owner(service_id: str) -> Dict[str, Any]:
    """Retrieves team ownership and on-call contact for a given service."""
    owner = query_service_owner(service_id)
    if not owner:
        return {
            "status": "NOT_FOUND",
            "message": f"Service '{service_id}' ownership not found.",
            "data": None,
        }
    return {
        "status": "SUCCESS",
        "tool": "get_service_owner",
        "service_id": service_id,
        "data": owner,
    }


def propose_response(incident_id: str, candidate_action: str, evidence_ids: List[str]) -> Dict[str, Any]:
    """
    Validates a proposed response against linked evidence and generates an approval request.
    Does NOT execute real infrastructure actions. Read-only validation.
    """
    valid_actions = {
        "simulate_canary_rollback": "Simulate rollback of recent failing deployment to previous stable version.",
        "simulate_service_isolation": "Isolate failing service to prevent cascading blast radius.",
        "simulate_team_escalation": "Escalate synthetic incident to owning team on-call engineer.",
        "acknowledge_incident": "Acknowledge synthetic incident in on-call queue."
    }

    if candidate_action not in valid_actions:
        return {
            "status": "REJECTED",
            "message": f"Action '{candidate_action}' is not in policy allowlist. Allowed: {list(valid_actions.keys())}",
            "requires_approval": True,
            "executable": False
        }

    # Verify evidence existence in graph
    evidence_records = query_evidence_chain(evidence_ids=evidence_ids)
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
        "description": "Fetches verified evidence logs, scan reports, and metric anomalies by incident or evidence ID.",
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
        "name": "get_vulnerable_services",
        "description": "Discovers services consuming packages affected by the specified vulnerability.",
        "input_schema": VulnerableServicesInput.model_json_schema(),
        "handler": get_vulnerable_services,
        "read_only": True,
    },
    {
        "name": "get_service_owner",
        "description": "Retrieves team ownership and on-call contact for a given service.",
        "input_schema": ServiceOwnerInput.model_json_schema(),
        "handler": get_service_owner,
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
