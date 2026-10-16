"""
FastAPI REST Application for ORACLE.
Implements Section 11: Exact endpoint contracts, Pydantic schemas,
action proposal/approval lifecycle, audit log, and graph topology.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from oracle.config import settings
from oracle.db import get_client, run_query
from oracle.seed_data import seed_database
from oracle.agent import OracleAgent
from oracle.queries import query_incident_context, query_evidence_chain
from oracle.actions import (
    ActionProposalRequest,
    ActionApprovalRequest,
    create_proposal,
    approve_and_execute_action,
    get_audit_trail,
    get_proposals,
    ALLOWLISTED_ACTIONS,
)
from oracle.mcp_tools import (
    TOOL_DEFINITIONS,
    get_incident_context,
    trace_candidate_causes,
    get_blast_radius,
    get_evidence_chain as tool_evidence_chain_func,
    get_deployment_history,
    get_vulnerable_services,
    get_service_owner,
    propose_response,
)

app = FastAPI(
    title="ImpactGraph: Incident Investigation Agent API",
    description="Trace the cause. Map the impact. Act with evidence. Powered by FalkorDB (Track 01)",
    version="1.0.0",
)

# CORS configuration supporting both local Vite frontend and general local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = OracleAgent(max_tool_calls=10)


# ===========================================================================
# 1. Health & Dependency Status (GET /health and GET /api/health)
# ===========================================================================

@app.get("/health")
@app.get("/api/health")
def health_check():
    """Accurately checks FalkorDB connectivity and server health."""
    try:
        client = get_client()
        ping = client.connection.ping()
        graphs = client.list_graphs()
        return {
            "status": "HEALTHY",
            "falkordb_connected": ping,
            "falkordb_host": settings.FALKORDB_HOST,
            "falkordb_port": settings.FALKORDB_PORT,
            "active_graphs": graphs,
            "is_synthetic": True
        }
    except Exception as e:
        return {
            "status": "DEGRADED",
            "falkordb_connected": False,
            "error": str(e),
            "is_synthetic": True
        }


# ===========================================================================
# 2. Database Seeder (POST /seed and POST /api/seed)
# ===========================================================================

@app.post("/seed")
@app.post("/api/seed")
def seed_graph():
    """Deterministically seeds or resets the synthetic incident graph."""
    try:
        stats = seed_database()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")


# ===========================================================================
# 3. Incident Endpoints (GET /incidents, GET /incidents/{id})
# ===========================================================================

@app.get("/incidents")
@app.get("/api/incidents")
def list_incidents():
    """Lists all incidents available in FalkorDB."""
    query = """
    MATCH (inc:Incident)
    OPTIONAL MATCH (inc)-[:HAS_ALERT]->(alt:Alert)
    RETURN inc.id AS id,
           inc.title AS title,
           inc.severity AS severity,
           inc.status AS status,
           inc.created_at AS created_at,
           inc.is_synthetic AS is_synthetic,
           count(DISTINCT alt) AS alert_count
    """
    rows = run_query(query)
    return {"incidents": rows, "count": len(rows), "is_synthetic": True}


@app.get("/incidents/{incident_id}")
@app.get("/api/incidents/{incident_id}")
def get_incident_detail(incident_id: str = Path(..., description="Target Incident ID")):
    """Retrieves single incident details with alerts and observed services."""
    ctx = query_incident_context(incident_id)
    if not ctx:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found in graph.")
    return ctx


# ===========================================================================
# 4. Investigation Engine (POST /incidents/{id}/investigate, GET /api/investigate/{id})
# ===========================================================================

@app.post("/incidents/{incident_id}/investigate")
@app.get("/api/investigate/{incident_id}")
def run_investigation(incident_id: str = Path(..., description="Target Incident ID")):
    """
    Coordinates FalkorDB MCP tools to investigate incident causality.
    Categorizes findings into OBSERVED, INFERRED, and UNKNOWN.
    """
    result = agent.investigate(incident_id)
    if result.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


# ===========================================================================
# 5. Incident Evidence (GET /incidents/{id}/evidence)
# ===========================================================================

@app.get("/incidents/{incident_id}/evidence")
@app.get("/api/incidents/{incident_id}/evidence")
def get_incident_evidence(incident_id: str = Path(..., description="Target Incident ID")):
    """Retrieves all grounded evidence linked to an incident in FalkorDB."""
    evidence = query_evidence_chain(incident_id=incident_id)
    return {
        "incident_id": incident_id,
        "evidence_count": len(evidence),
        "evidence": evidence,
        "is_synthetic": True
    }


# ===========================================================================
# 6. Action Lifecycle: Proposal & Human Approval (POST /actions/propose, POST /actions/{id}/approve)
# ===========================================================================

@app.post("/actions/propose")
@app.post("/api/actions/propose")
def propose_action(request: ActionProposalRequest):
    """
    Creates a simulated action proposal in PENDING_APPROVAL state.
    Does NOT execute the action.
    """
    result = create_proposal(request)
    if result.get("status") in ("REJECTED_DISALLOWED", "REJECTED_NO_EVIDENCE"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/actions/{action_id}/approve")
@app.post("/api/actions/{action_id}/approve")
def approve_action(
    action_id: str = Path(..., description="Proposal ID to approve"),
    request: ActionApprovalRequest = None
):
    """
    Applies explicit human approval and executes simulated remediation.
    Rejects self-approval, duplicate executions, and unapproved requests.
    """
    if not request or not request.approver:
        raise HTTPException(status_code=400, detail="Missing required approver identifier.")

    result = approve_and_execute_action(
        action_id=action_id,
        approver=request.approver,
        notes=request.notes
    )

    if result.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=result["message"])
    if result.get("status") == "REJECTED_ALREADY_PROCESSED":
        raise HTTPException(status_code=400, detail=result["message"])
    if result.get("status") == "REJECTED_SELF_APPROVAL":
        raise HTTPException(status_code=403, detail=result["message"])

    return result


@app.get("/actions/proposals")
@app.get("/api/actions/proposals")
def list_proposals(incident_id: Optional[str] = None):
    """Lists current action proposals and their approval states."""
    return {"proposals": get_proposals(incident_id)}


# ===========================================================================
# 7. Audit Ledger (GET /audit and GET /api/audit)
# ===========================================================================

@app.get("/audit")
@app.get("/api/audit")
def audit_trail(incident_id: Optional[str] = None):
    """Returns the immutable audit log of simulated remediation actions."""
    return {"audit_log": get_audit_trail(incident_id)}


# ===========================================================================
# 8. MCP Tool Endpoints
# ===========================================================================

@app.get("/api/tools")
def list_mcp_tools():
    """Catalog of all registered narrow domain MCP tools."""
    return {
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "read_only": t["read_only"],
                "schema": t["input_schema"]
            }
            for t in TOOL_DEFINITIONS
        ]
    }


@app.get("/api/tools/incident_context")
def tool_incident_context(incident_id: str = Query(...)):
    return get_incident_context(incident_id)


@app.get("/api/tools/candidate_causes")
def tool_candidate_causes(incident_id: str = Query(...), max_depth: int = Query(3, ge=1, le=5)):
    return trace_candidate_causes(incident_id, max_depth)


@app.get("/api/tools/blast_radius")
def tool_blast_radius(service_id: str = Query(...), max_depth: int = Query(4, ge=1, le=6)):
    return get_blast_radius(service_id, max_depth)


@app.get("/api/tools/deployment_history")
def tool_deployment_history(service_id: str = Query(...), limit: int = Query(10, ge=1, le=20)):
    return get_deployment_history(service_id, limit)


@app.get("/api/tools/evidence_chain")
def tool_evidence_chain(
    incident_id: Optional[str] = Query(None),
    evidence_ids: Optional[str] = Query(None)
):
    ids = [e.strip() for e in evidence_ids.split(",") if e.strip()] if evidence_ids else None
    return tool_evidence_chain_func(incident_id=incident_id, evidence_ids=ids)


@app.get("/api/tools/vulnerable_services")
def tool_vulnerable_services(vulnerability_id: str = Query(...)):
    return get_vulnerable_services(vulnerability_id)


@app.get("/api/tools/service_owner")
def tool_service_owner(service_id: str = Query(...)):
    return get_service_owner(service_id)


# ===========================================================================
# 9. Full Graph Topology for Cytoscape Visualizer
# ===========================================================================

@app.get("/api/graph/topology")
def get_graph_topology():
    """Exports full incident graph topology (nodes and links) for interactive visualizer."""
    query = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN labels(n) AS src_labels,
           properties(n) AS src_props,
           type(r) AS rel_type,
           labels(m) AS dst_labels,
           properties(m) AS dst_props
    """
    rows = run_query(query)

    nodes_map = {}
    edges = []

    for row in rows:
        src_props = row.get("src_props", {})
        src_labels = row.get("src_labels", ["Unknown"])
        src_id = src_props.get("id") or src_props.get("name") or "unknown_src"

        if src_id not in nodes_map:
            nodes_map[src_id] = {
                "id": src_id,
                "label": src_labels[0] if src_labels else "Node",
                "properties": src_props,
            }

        rel_type = row.get("rel_type")
        dst_props = row.get("dst_props")
        dst_labels = row.get("dst_labels")

        if rel_type and dst_props:
            dst_id = dst_props.get("id") or dst_props.get("name") or "unknown_dst"
            if dst_id not in nodes_map:
                nodes_map[dst_id] = {
                    "id": dst_id,
                    "label": dst_labels[0] if dst_labels else "Node",
                    "properties": dst_props,
                }
            edges.append({
                "source": src_id,
                "target": dst_id,
                "relationship": rel_type,
            })

    return {
        "nodes": list(nodes_map.values()),
        "edges": edges,
        "is_synthetic": True
    }


# ===========================================================================
# 10. Dashboard Route (Serves React Production Build or Builtin Dashboard)
# ===========================================================================

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if (frontend_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static_assets")

@app.get("/", response_class=HTMLResponse)
def index_page():
    """Serves the React incident console or dynamic dashboard."""
    dist_index = frontend_dist / "index.html"
    if dist_index.exists():
        return FileResponse(str(dist_index))
    from oracle.frontend import get_html_dashboard
    return get_html_dashboard()

