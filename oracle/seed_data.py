"""
Idempotent synthetic incident graph seeder for ORACLE.
Implements the exact schema from Section 5 of the FalkorDB Implementation Guide.
"""

from typing import Dict, Any
from oracle.config import settings
from oracle.db import get_client


def seed_database(graph_name: str = settings.FALKORDB_GRAPH) -> Dict[str, Any]:
    """
    Seeds the FalkorDB graph with the synthetic incident topology.
    Uses clean reset-and-seed to guarantee deterministic state without duplicates.
    """
    client = get_client()
    graph = client.select_graph(graph_name)

    # 1. Reset existing graph
    try:
        graph.delete()
    except Exception:
        pass
    graph = client.select_graph(graph_name)

    # 2. Cypher Seeding Query
    seed_query = """
    // --- 1. INCIDENT ---
    CREATE (inc:Incident {
        id: 'INC-4091',
        title: 'Cascading Checkout Failure and 504 Gateway Spike',
        severity: 'CRITICAL',
        status: 'ACTIVE',
        created_at: '2026-10-16T10:20:00Z'
    })

    // --- 2. TEAMS ---
    CREATE (team_checkout:Team {id: 'team-checkout', name: 'Checkout & Payments Platform', on_call: 'Sarah Connor (Staff SRE)'})
    CREATE (team_gateway:Team {id: 'team-gateway', name: 'Core Traffic & Gateways', on_call: 'Alex Murphy (Traffic Lead)'})
    CREATE (team_bi:Team {id: 'team-bi', name: 'Business Intelligence', on_call: 'Data Ops Team'})

    // --- 3. SERVICES (Connected chain + 1 Disconnected Negative Test) ---
    CREATE (s_web:Service {id: 'svc-web', name: 'web-frontend', criticality: 'HIGH', health: 'DEGRADED'})
    CREATE (s_gw:Service {id: 'svc-gateway', name: 'api-gateway', criticality: 'CRITICAL', health: 'DEGRADED'})
    CREATE (s_order:Service {id: 'svc-order', name: 'order-service', criticality: 'CRITICAL', health: 'DEGRADED'})
    CREATE (s_pay:Service {id: 'svc-payment', name: 'payment-service', criticality: 'CRITICAL', health: 'FAILING'})
    CREATE (s_inv:Service {id: 'svc-inventory', name: 'inventory-service', criticality: 'MEDIUM', health: 'HEALTHY'})
    CREATE (s_notif:Service {id: 'svc-notification', name: 'notification-service', criticality: 'LOW', health: 'HEALTHY'})
    CREATE (s_analytics:Service {id: 'svc-analytics', name: 'analytics-pipeline', criticality: 'LOW', health: 'HEALTHY'})

    // Ownership
    CREATE (team_gateway)-[:OWNS]->(s_web)
    CREATE (team_gateway)-[:OWNS]->(s_gw)
    CREATE (team_checkout)-[:OWNS]->(s_order)
    CREATE (team_checkout)-[:OWNS]->(s_pay)
    CREATE (team_checkout)-[:OWNS]->(s_inv)
    CREATE (team_gateway)-[:OWNS]->(s_notif)
    CREATE (team_bi)-[:OWNS]->(s_analytics)

    // Dependency Topology: (consumer:Service)-[:DEPENDS_ON]->(provider:Service)
    // Multi-hop path: web -> gateway -> order -> payment (4 hops)
    CREATE (s_web)-[:DEPENDS_ON]->(s_gw)
    CREATE (s_gw)-[:DEPENDS_ON]->(s_order)
    CREATE (s_order)-[:DEPENDS_ON]->(s_pay)
    CREATE (s_order)-[:DEPENDS_ON]->(s_inv)
    CREATE (s_gw)-[:DEPENDS_ON]->(s_notif)
    // Note: svc-analytics has NO DEPENDS_ON edges (Disconnected negative test)

    // --- 4. ALERTS ---
    CREATE (alt_gw:Alert {
        id: 'ALT-881',
        signal: '504 Gateway Timeout Spike (p99 > 15s)',
        timestamp: '2026-10-16T10:18:00Z',
        source: 'Datadog'
    })
    CREATE (alt_pay:Alert {
        id: 'ALT-882',
        signal: 'Connection Pool Starvation & Latency Spike',
        timestamp: '2026-10-16T10:16:00Z',
        source: 'Prometheus'
    })
    CREATE (alt_order:Alert {
        id: 'ALT-883',
        signal: 'Order Processing Throughput Dropped 85%',
        timestamp: '2026-10-16T10:19:00Z',
        source: 'PagerDuty'
    })

    CREATE (inc)-[:HAS_ALERT]->(alt_gw)
    CREATE (inc)-[:HAS_ALERT]->(alt_pay)
    CREATE (inc)-[:HAS_ALERT]->(alt_order)

    CREATE (alt_gw)-[:OBSERVED_ON]->(s_gw)
    CREATE (alt_pay)-[:OBSERVED_ON]->(s_pay)
    CREATE (alt_order)-[:OBSERVED_ON]->(s_order)

    // --- 5. COMPETING HYPOTHESIS 1: SHARED PACKAGE & VULNERABILITY ---
    CREATE (pkg_auth:Package {
        id: 'pkg-auth-tokens',
        name: 'auth-tokens-lib',
        version: 'v1.2.0',
        risk_status: 'VULNERABLE'
    })
    CREATE (vuln_cve:Vulnerability {
        id: 'CVE-2026-4412',
        title: 'Memory exhaustion via crafted JWT token header',
        severity: 'HIGH',
        affected_version: 'v1.2.0'
    })
    CREATE (pkg_auth)-[:HAS_VULNERABILITY]->(vuln_cve)
    CREATE (s_order)-[:USES]->(pkg_auth)
    CREATE (s_pay)-[:USES]->(pkg_auth)

    // --- 6. COMPETING HYPOTHESIS 2: RECENT DEPLOYMENTS ---
    CREATE (dep_pay_bad:Deployment {
        id: 'dep-pay-v2.4.1',
        version: 'v2.4.1',
        timestamp: '2026-10-16T10:14:00Z',
        status: 'FAILED_HEALTHCHECKS',
        commit_sha: 'c7f91a2',
        author: 'deploy-bot@company.com'
    })
    CREATE (dep_pay_good:Deployment {
        id: 'dep-pay-v2.4.0',
        version: 'v2.4.0',
        timestamp: '2026-10-14T08:00:00Z',
        status: 'STABLE',
        commit_sha: 'a10b39e',
        author: 'lead-dev@company.com'
    })
    CREATE (dep_order_good:Deployment {
        id: 'dep-order-v1.8.0',
        version: 'v1.8.0',
        timestamp: '2026-10-10T12:00:00Z',
        status: 'STABLE',
        commit_sha: '99bc412',
        author: 'order-dev@company.com'
    })

    CREATE (s_pay)-[:DEPLOYED_IN]->(dep_pay_bad)
    CREATE (s_pay)-[:DEPLOYED_IN]->(dep_pay_good)
    CREATE (s_order)-[:DEPLOYED_IN]->(dep_order_good)

    // --- 7. EVIDENCE & PROVENANCE ---
    CREATE (evi_canary:Evidence {
        id: 'EVI-901',
        kind: 'LOG_TRACE',
        source_ref: 'logs://payment-service/canary-errors.log',
        observed_at: '2026-10-16T10:15:30Z',
        summary: 'Database connection pool starvation immediately following deployment v2.4.1 container rollout'
    })
    CREATE (evi_sec:Evidence {
        id: 'EVI-902',
        kind: 'SECURITY_SCAN',
        source_ref: 'trivy://scans/auth-tokens-lib-cve-2026-4412',
        observed_at: '2026-10-12T04:00:00Z',
        summary: 'CVE-2026-4412 published 4 days prior. No exploit payload patterns detected in incoming gateway traffic'
    })
    CREATE (evi_latency:Evidence {
        id: 'EVI-903',
        kind: 'METRIC_ANOMALY',
        source_ref: 'datadog://metrics/payment-service/p99-latency',
        observed_at: '2026-10-16T10:14:45Z',
        summary: 'P99 latency surged from 110ms to 17,800ms within 45 seconds of v2.4.1 deployment'
    })

    CREATE (evi_canary)-[:SUPPORTS]->(inc)
    CREATE (evi_canary)-[:OBSERVED]->(s_pay)
    CREATE (evi_canary)-[:REFERS_TO]->(dep_pay_bad)

    CREATE (evi_sec)-[:SUPPORTS]->(inc)
    CREATE (evi_sec)-[:OBSERVED]->(s_pay)

    CREATE (evi_latency)-[:SUPPORTS]->(inc)
    CREATE (evi_latency)-[:OBSERVED]->(s_pay)
    CREATE (evi_latency)-[:REFERS_TO]->(dep_pay_bad)

    RETURN inc.id AS incident_id
    """

    res = graph.query(seed_query)
    incident_id = res.result_set[0][0] if res.result_set else None

    # Count nodes and relationships
    stats_query = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->()
    RETURN count(DISTINCT n) AS total_nodes, count(r) AS total_edges
    """
    stats_res = graph.query(stats_query)
    total_nodes = stats_res.result_set[0][0]
    total_edges = stats_res.result_set[0][1]

    return {
        "status": "SUCCESS",
        "graph": graph_name,
        "incident_id": incident_id,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
    }


if __name__ == "__main__":
    print(f"Seeding FalkorDB graph '{settings.FALKORDB_GRAPH}'...")
    stats = seed_database()
    print("Seed complete successfully!")
    print(f"  Graph: {stats['graph']}")
    print(f"  Incident ID: {stats['incident_id']}")
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Relationships: {stats['total_edges']}")
