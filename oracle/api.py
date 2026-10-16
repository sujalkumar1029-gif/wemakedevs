"""
FastAPI REST Application for ORACLE.
Exposes incident triage, bounded MCP tools, action approval, and graph visualization.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from oracle.config import settings
from oracle.db import get_client, run_query
from oracle.seed_data import seed_database
from oracle.agent import OracleAgent
from oracle.actions import (
    ActionExecutionRequest,
    execute_simulated_action,
    get_audit_trail,
    ALLOWLISTED_ACTIONS,
)
from oracle.mcp_tools import (
    TOOL_DEFINITIONS,
    get_incident_context,
    trace_candidate_causes,
    get_blast_radius,
    get_evidence_chain,
    get_deployment_history,
    propose_response,
)

app = FastAPI(
    title="ORACLE Incident Investigation Agent API",
    description="Evidence-Grounded Incident Investigation Agent powered by FalkorDB (Track 01)",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = OracleAgent(max_tool_calls=8)


# --- 1. Health & Status ---

@app.get("/api/health")
def health_check():
    """Checks FalkorDB connectivity and server health."""
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
        }
    except Exception as e:
        return {
            "status": "DEGRADED",
            "falkordb_connected": False,
            "error": str(e),
        }


# --- 2. Seed Synthetic Graph ---

@app.post("/api/seed")
def seed_graph():
    """Deterministically seeds or resets the synthetic incident graph."""
    try:
        stats = seed_database()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")


# --- 3. Incident Listing ---

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
           count(DISTINCT alt) AS alert_count
    """
    rows = run_query(query)
    return {"incidents": rows}


# --- 4. End-to-End Investigation ---

@app.get("/api/investigate/{incident_id}")
def run_investigation(incident_id: str):
    """
    Triggers the ORACLE Agent reasoning loop for the specified incident.
    Returns hypotheses, grounded evidence, blast radius, and proposed action.
    """
    result = agent.investigate(incident_id)
    if result.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


# --- 5. Direct MCP Tool Invocations ---

@app.get("/api/tools")
def list_mcp_tools():
    """Returns catalog of all registered narrow domain MCP tools."""
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
def tool_incident_context(incident_id: str = Query(..., description="Target Incident ID")):
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
def tool_evidence_chain(evidence_ids: str = Query(..., description="Comma-separated evidence IDs")):
    ids = [e.strip() for e in evidence_ids.split(",") if e.strip()]
    return get_evidence_chain(ids)


# --- 6. Policy-Controlled Simulated Action Executor ---

@app.post("/api/actions/execute")
def execute_action(request: ActionExecutionRequest):
    """
    Simulates remediation action. Enforces approval gate and allowlist.
    """
    result = execute_simulated_action(request)
    if result.get("status") == "REJECTED_UNAPPROVED":
        raise HTTPException(
            status_code=403,
            detail=result["message"]
        )
    if result.get("status") in ("REJECTED_DISALLOWED", "REJECTED_NO_EVIDENCE"):
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )
    return result


@app.get("/api/audit")
def audit_trail(incident_id: Optional[str] = None):
    """Returns the persistent audit log of simulated remediation actions."""
    return {"audit_log": get_audit_trail(incident_id)}


# --- 7. Full Graph Topology for Visualizer ---

@app.get("/api/graph/topology")
def get_graph_topology():
    """
    Exports full incident graph topology (nodes and links) for interactive visualizer.
    """
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
    }


# --- 8. Interactive Investigation Console (HTML/JS Web App) ---

@app.get("/", response_class=HTMLResponse)
def index_page():
    """Serves the rich ORACLE Incident Investigation Console."""
    from oracle.frontend import get_html_dashboard
    return get_html_dashboard()
