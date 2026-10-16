"""
Cypher query definitions and graph execution functions for ORACLE.
All queries are parameterized, bounded, and adhere to the FalkorDB schema.
"""

from typing import Any, Dict, List, Optional
from oracle.db import run_query


def query_incident_context(incident_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the root incident, associated alerts, observed services, and evidence IDs.
    """
    query = """
    MATCH (inc:Incident {id: $incident_id})
    OPTIONAL MATCH (inc)-[:HAS_ALERT]->(alt:Alert)-[:OBSERVED_ON]->(svc:Service)
    OPTIONAL MATCH (evi:Evidence)-[:SUPPORTS]->(inc)
    OPTIONAL MATCH (team:Team)-[:OWNS]->(svc)
    RETURN inc.id AS incident_id,
           inc.title AS title,
           inc.severity AS severity,
           inc.status AS status,
           inc.created_at AS created_at,
           collect(DISTINCT {
               alert_id: alt.id,
               signal: alt.signal,
               timestamp: alt.timestamp,
               source: alt.source,
               service_id: svc.id,
               service_name: svc.name,
               service_health: svc.health,
               service_criticality: svc.criticality,
               owner_team: team.name
           }) AS alerts,
           collect(DISTINCT {
               service_id: svc.id,
               name: svc.name,
               criticality: svc.criticality,
               health: svc.health,
               owner_team: team.name
           }) AS observed_services,
           collect(DISTINCT evi.id) AS evidence_ids
    """
    results = run_query(query, {"incident_id": incident_id})
    if not results or not results[0].get("incident_id"):
        return None
    return results[0]


def query_blast_radius(service_id: str, max_depth: int = 4) -> List[Dict[str, Any]]:
    """
    Calculates downstream blast radius for a failing service.
    Direction convention: (consumer:Service)-[:DEPENDS_ON]->(provider:Service)
    Traversing upstream in reverse from target gives consumers impacted by target's failure.
    """
    # Depth must be bounded
    depth = max(1, min(int(max_depth), 6))
    query = f"""
    MATCH path = (consumer:Service)-[:DEPENDS_ON*1..{depth}]->(target:Service)
    WHERE target.id = $service_id
    OPTIONAL MATCH (t:Team)-[:OWNS]->(consumer)
    RETURN consumer.id AS affected_service_id,
           consumer.name AS affected_service,
           consumer.criticality AS criticality,
           consumer.health AS current_health,
           coalesce(t.name, 'Unassigned') AS owner_team,
           length(path) AS hop_distance
    ORDER BY hop_distance ASC, consumer.criticality DESC
    LIMIT 50
    """
    return run_query(query, {"service_id": service_id})


def query_candidate_causes(incident_id: str, max_depth: int = 3) -> List[Dict[str, Any]]:
    """
    Finds candidate causes (failed deployments, vulnerable packages, failing dependencies)
    connected to the services observed in the incident.
    """
    query = """
    MATCH (inc:Incident {id: $incident_id})-[:HAS_ALERT]->(alt:Alert)-[:OBSERVED_ON]->(svc:Service)
    OPTIONAL MATCH (svc)-[:DEPLOYED_IN]->(dep:Deployment)
    OPTIONAL MATCH (svc)-[:USES]->(pkg:Package)-[:HAS_VULNERABILITY]->(vuln:Vulnerability)
    OPTIONAL MATCH (svc)-[:DEPENDS_ON]->(downstream:Service {health: 'FAILING'})
    RETURN svc.id AS service_id,
           svc.name AS service_name,
           collect(DISTINCT {
               type: 'DEPLOYMENT',
               id: dep.id,
               version: dep.version,
               status: dep.status,
               timestamp: dep.timestamp,
               author: dep.author
           }) AS deployments,
           collect(DISTINCT {
               type: 'VULNERABILITY',
               package_name: pkg.name,
               package_version: pkg.version,
               vulnerability_id: vuln.id,
               severity: vuln.severity,
               title: vuln.title
           }) AS vulnerabilities,
           collect(DISTINCT {
               type: 'FAILING_DEPENDENCY',
               service_id: downstream.id,
               service_name: downstream.name,
               health: downstream.health
           }) AS failing_dependencies
    """
    return run_query(query, {"incident_id": incident_id})


def query_deployment_history(service_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches recent deployment history for a service ordered by timestamp descending.
    """
    lim = max(1, min(int(limit), 20))
    query = """
    MATCH (s:Service)-[:DEPLOYED_IN]->(d:Deployment)
    WHERE s.id = $service_id OR s.name = $service_id
    RETURN d.id AS deployment_id,
           d.version AS version,
           d.timestamp AS timestamp,
           d.status AS status,
           d.commit_sha AS commit_sha,
           d.author AS author
    ORDER BY d.timestamp DESC
    LIMIT $limit
    """
    return run_query(query, {"service_id": service_id, "limit": lim})


def query_evidence_chain(evidence_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetches detailed evidence records and their graph references.
    """
    if not evidence_ids:
        return []

    query = """
    MATCH (evi:Evidence)
    WHERE evi.id IN $evidence_ids
    OPTIONAL MATCH (evi)-[:OBSERVED]->(s:Service)
    OPTIONAL MATCH (evi)-[:REFERS_TO]->(d:Deployment)
    RETURN evi.id AS evidence_id,
           evi.kind AS kind,
           evi.source_ref AS source_ref,
           evi.observed_at AS observed_at,
           evi.summary AS summary,
           s.id AS observed_service_id,
           s.name AS observed_service_name,
           d.id AS refers_to_deployment_id,
           d.version AS refers_to_version
    ORDER BY evi.observed_at ASC
    """
    return run_query(query, {"evidence_ids": evidence_ids})


def query_service_details(service_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns full metadata for a service including incoming/outgoing dependencies and owner team.
    """
    query = """
    MATCH (s:Service)
    WHERE s.id = $service_id OR s.name = $service_id
    OPTIONAL MATCH (team:Team)-[:OWNS]->(s)
    OPTIONAL MATCH (s)-[:DEPENDS_ON]->(provider:Service)
    OPTIONAL MATCH (consumer:Service)-[:DEPENDS_ON]->(s)
    RETURN s.id AS service_id,
           s.name AS name,
           s.criticality AS criticality,
           s.health AS health,
           team.name AS owner_team,
           team.on_call AS on_call,
           collect(DISTINCT provider.name) AS dependencies,
           collect(DISTINCT consumer.name) AS dependents
    """
    results = run_query(query, {"service_id": service_id})
    return results[0] if results else None
