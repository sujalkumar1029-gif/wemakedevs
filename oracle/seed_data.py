"""
Deterministic synthetic incident graph seeder for ORACLE.
Implements the exact schema from Section 6 of the Master Engineering Prompt.
All records are explicitly marked with `is_synthetic: true`.
Supports multiple realistic incident scenarios:
- INC-4091: Cascading Checkout Failure (Canary Rollout vs Package CVE)
- INC-3022: Redis Cache Stampede & Auth Token Eviction Surge (Config Rollout vs DDoS)
- INC-5102: Logistics Carrier Webhook & Delivery Gateway Timeout (External Outage vs DNS)
"""

from typing import Dict, Any
from oracle.config import settings
from oracle.db import get_client, run_query


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
    // --- 1. INCIDENTS (Synthetic) ---
    CREATE (inc:Incident {
        id: 'INC-4091',
        title: 'Cascading Checkout Failure and 504 Gateway Spike',
        description: 'Critical downstream latency spike causing p99 timeout cascade across order processing pipeline',
        severity: 'CRITICAL',
        status: 'ACTIVE',
        created_at: '2026-10-16T10:20:00Z',
        is_synthetic: true
    })

    CREATE (inc2:Incident {
        id: 'INC-3022',
        title: 'Redis Cache Stampede & Auth Token Eviction Surge',
        description: 'Session cache TTL misconfiguration triggering downstream database authentication stampede',
        severity: 'HIGH',
        status: 'ACTIVE',
        created_at: '2026-10-17T08:15:00Z',
        is_synthetic: true
    })

    CREATE (inc3:Incident {
        id: 'INC-5102',
        title: 'Logistics Carrier Webhook & Delivery Gateway Timeout',
        description: 'Third-party delivery carrier endpoint outage causing message queue backlog and circuit breaker trip',
        severity: 'MEDIUM',
        status: 'ACTIVE',
        created_at: '2026-10-17T14:10:00Z',
        is_synthetic: true
    })

    // --- 2. TEAMS (Synthetic) ---
    CREATE (team_checkout:Team {id: 'team-checkout', name: 'Checkout & Payments Platform', on_call: 'Sarah Connor (Staff SRE)', is_synthetic: true})
    CREATE (team_gateway:Team {id: 'team-gateway', name: 'Core Traffic & Gateways', on_call: 'Alex Murphy (Traffic Lead)', is_synthetic: true})
    CREATE (team_bi:Team {id: 'team-bi', name: 'Business Intelligence & Analytics', on_call: 'Data Ops Team', is_synthetic: true})
    CREATE (team_logistics:Team {id: 'team-logistics', name: 'Fulfillment & Logistics', on_call: 'Elena Vance (Logistics SRE)', is_synthetic: true})

    // --- 3. SERVICES (Connected Chain + 1 Disconnected Negative Test) ---
    CREATE (s_web:Service {id: 'svc-web', name: 'web-frontend', criticality: 'HIGH', health: 'DEGRADED', status: 'DEGRADED', is_synthetic: true})
    CREATE (s_gw:Service {id: 'svc-gateway', name: 'api-gateway', criticality: 'CRITICAL', health: 'DEGRADED', status: 'DEGRADED', is_synthetic: true})
    CREATE (s_order:Service {id: 'svc-order', name: 'order-service', criticality: 'CRITICAL', health: 'DEGRADED', status: 'DEGRADED', is_synthetic: true})
    CREATE (s_pay:Service {id: 'svc-payment', name: 'payment-service', criticality: 'CRITICAL', health: 'FAILING', status: 'OUTAGE', is_synthetic: true})
    CREATE (s_inv:Service {id: 'svc-inventory', name: 'inventory-service', criticality: 'MEDIUM', health: 'HEALTHY', status: 'HEALTHY', is_synthetic: true})
    CREATE (s_notif:Service {id: 'svc-notification', name: 'notification-service', criticality: 'LOW', health: 'HEALTHY', status: 'HEALTHY', is_synthetic: true})
    CREATE (s_auth:Service {id: 'svc-auth', name: 'auth-service', criticality: 'CRITICAL', health: 'DEGRADED', status: 'DEGRADED', is_synthetic: true})
    CREATE (s_logistics:Service {id: 'svc-logistics', name: 'logistics-service', criticality: 'MEDIUM', health: 'DEGRADED', status: 'DEGRADED', is_synthetic: true})
    CREATE (s_analytics:Service {id: 'svc-analytics', name: 'analytics-pipeline', criticality: 'LOW', health: 'HEALTHY', status: 'HEALTHY', is_synthetic: true})

    // Ownership: (Team)-[:OWNS]->(Service)
    CREATE (team_gateway)-[:OWNS]->(s_web)
    CREATE (team_gateway)-[:OWNS]->(s_gw)
    CREATE (team_checkout)-[:OWNS]->(s_order)
    CREATE (team_checkout)-[:OWNS]->(s_pay)
    CREATE (team_checkout)-[:OWNS]->(s_inv)
    CREATE (team_gateway)-[:OWNS]->(s_notif)
    CREATE (team_gateway)-[:OWNS]->(s_auth)
    CREATE (team_logistics)-[:OWNS]->(s_logistics)
    CREATE (team_bi)-[:OWNS]->(s_analytics)

    // Dependency Topology: (consumer:Service)-[:DEPENDS_ON]->(provider:Service)
    CREATE (s_web)-[:DEPENDS_ON]->(s_gw)
    CREATE (s_gw)-[:DEPENDS_ON]->(s_order)
    CREATE (s_order)-[:DEPENDS_ON]->(s_pay)
    CREATE (s_order)-[:DEPENDS_ON]->(s_inv)
    CREATE (s_gw)-[:DEPENDS_ON]->(s_notif)
    CREATE (s_gw)-[:DEPENDS_ON]->(s_auth)
    CREATE (s_order)-[:DEPENDS_ON]->(s_logistics)
    // svc-analytics has NO DEPENDS_ON edges (Negative test: disconnected from blast radius)

    // --- 4. ALERTS: INC-4091 (Synthetic) ---
    CREATE (alt_gw:Alert {
        id: 'ALT-881',
        signal: '504 Gateway Timeout Spike (p99 > 15s)',
        alert_type: 'HTTP_504_TIMEOUT',
        observed_value: '18400ms',
        threshold: '500ms',
        timestamp: '2026-10-16T10:18:00Z',
        source: 'Datadog Ingress Monitor',
        is_synthetic: true
    })
    CREATE (alt_pay:Alert {
        id: 'ALT-882',
        signal: 'Connection Pool Starvation & Latency Spike',
        alert_type: 'DB_CONNECTION_EXHAUSTION',
        observed_value: '100% saturation (0 free slots)',
        threshold: '85% saturation',
        timestamp: '2026-10-16T10:16:00Z',
        source: 'Prometheus HikariCP Exporter',
        is_synthetic: true
    })
    CREATE (alt_order:Alert {
        id: 'ALT-883',
        signal: 'Order Processing Throughput Dropped 85%',
        alert_type: 'THROUGHPUT_DROP',
        observed_value: '15 orders/min',
        threshold: '100 orders/min',
        timestamp: '2026-10-16T10:19:00Z',
        source: 'PagerDuty Business Service Alert',
        is_synthetic: true
    })

    CREATE (inc)-[:HAS_ALERT]->(alt_gw)
    CREATE (inc)-[:HAS_ALERT]->(alt_pay)
    CREATE (inc)-[:HAS_ALERT]->(alt_order)

    CREATE (alt_gw)-[:OBSERVED_ON]->(s_gw)
    CREATE (alt_pay)-[:OBSERVED_ON]->(s_pay)
    CREATE (alt_order)-[:OBSERVED_ON]->(s_order)

    // --- 5. ALERTS: INC-3022 (Synthetic) ---
    CREATE (alt_auth_1:Alert {
        id: 'ALT-301',
        signal: 'Session Cache Eviction Rate Surge > 950 keys/sec',
        alert_type: 'CACHE_EVICTION_SURGE',
        observed_value: '950 evictions/sec',
        threshold: '50 evictions/sec',
        timestamp: '2026-10-17T08:12:00Z',
        source: 'Redis Prometheus Exporter',
        is_synthetic: true
    })
    CREATE (alt_auth_2:Alert {
        id: 'ALT-302',
        signal: 'P95 Auth Token Verify Latency Elevated',
        alert_type: 'AUTH_LATENCY_SPIKE',
        observed_value: '1420ms',
        threshold: '100ms',
        timestamp: '2026-10-17T08:14:00Z',
        source: 'Datadog APM Auth Monitor',
        is_synthetic: true
    })
    CREATE (inc2)-[:HAS_ALERT]->(alt_auth_1)
    CREATE (inc2)-[:HAS_ALERT]->(alt_auth_2)
    CREATE (alt_auth_1)-[:OBSERVED_ON]->(s_auth)
    CREATE (alt_auth_2)-[:OBSERVED_ON]->(s_auth)

    // --- 6. ALERTS: INC-5102 (Synthetic) ---
    CREATE (alt_logistics_1:Alert {
        id: 'ALT-501',
        signal: 'External Carrier Dispatch Webhook Timeout > 30s',
        alert_type: 'WEBHOOK_504_TIMEOUT',
        observed_value: '31200ms',
        threshold: '2000ms',
        timestamp: '2026-10-17T14:08:00Z',
        source: 'CircuitBreaker Sentinel',
        is_synthetic: true
    })
    CREATE (alt_logistics_2:Alert {
        id: 'ALT-502',
        signal: 'Delivery Queue Dead-Letter Threshold Surpassed',
        alert_type: 'QUEUE_OVERFLOW',
        observed_value: '5240 messages in DLQ',
        threshold: '500 messages',
        timestamp: '2026-10-17T14:09:30Z',
        source: 'RabbitMQ Metrics Collector',
        is_synthetic: true
    })
    CREATE (inc3)-[:HAS_ALERT]->(alt_logistics_1)
    CREATE (inc3)-[:HAS_ALERT]->(alt_logistics_2)
    CREATE (alt_logistics_1)-[:OBSERVED_ON]->(s_logistics)
    CREATE (alt_logistics_2)-[:OBSERVED_ON]->(s_logistics)

    // --- 7. PACKAGES & VULNERABILITIES ---
    CREATE (pkg_auth:Package {
        id: 'pkg-auth-tokens',
        name: 'auth-tokens-lib',
        version: 'v1.2.0',
        risk_status: 'VULNERABLE',
        is_synthetic: true
    })
    CREATE (vuln_cve:Vulnerability {
        id: 'CVE-2026-4412',
        title: 'Memory exhaustion via crafted JWT token header',
        severity: 'HIGH',
        affected_version: 'v1.2.0',
        published_at: '2026-10-12T04:00:00Z',
        is_synthetic: true
    })
    CREATE (pkg_auth)-[:HAS_VULNERABILITY]->(vuln_cve)
    CREATE (s_order)-[:USES]->(pkg_auth)
    CREATE (s_pay)-[:USES]->(pkg_auth)
    CREATE (s_auth)-[:USES]->(pkg_auth)

    // --- 8. RECENT DEPLOYMENTS ---
    CREATE (dep_pay_bad:Deployment {
        id: 'dep-pay-v2.4.1',
        version: 'v2.4.1',
        timestamp: '2026-10-16T10:14:00Z',
        status: 'FAILED_HEALTHCHECKS',
        commit_sha: 'c7f91a2',
        author: 'deploy-bot@company.com',
        is_synthetic: true
    })
    CREATE (dep_pay_good:Deployment {
        id: 'dep-pay-v2.4.0',
        version: 'v2.4.0',
        timestamp: '2026-10-14T08:00:00Z',
        status: 'STABLE',
        commit_sha: 'a10b39e',
        author: 'lead-dev@company.com',
        is_synthetic: true
    })
    CREATE (dep_order_good:Deployment {
        id: 'dep-order-v1.8.0',
        version: 'v1.8.0',
        timestamp: '2026-10-10T12:00:00Z',
        status: 'STABLE',
        commit_sha: '99bc412',
        author: 'order-dev@company.com',
        is_synthetic: true
    })
    CREATE (dep_auth_bad:Deployment {
        id: 'dep-auth-v1.4.2',
        version: 'v1.4.2',
        timestamp: '2026-10-17T08:10:00Z',
        status: 'FAILED_HEALTHCHECKS',
        commit_sha: 'b8e120f',
        author: 'auth-bot@company.com',
        is_synthetic: true
    })
    CREATE (dep_logistics_good:Deployment {
        id: 'dep-logistics-v1.1.0',
        version: 'v1.1.0',
        timestamp: '2026-10-15T09:00:00Z',
        status: 'STABLE',
        commit_sha: '4d10f8a',
        author: 'logistics-dev@company.com',
        is_synthetic: true
    })

    CREATE (s_pay)-[:DEPLOYED_IN]->(dep_pay_bad)
    CREATE (s_pay)-[:DEPLOYED_IN]->(dep_pay_good)
    CREATE (s_order)-[:DEPLOYED_IN]->(dep_order_good)
    CREATE (s_auth)-[:DEPLOYED_IN]->(dep_auth_bad)
    CREATE (s_logistics)-[:DEPLOYED_IN]->(dep_logistics_good)

    // --- 9. EVIDENCE & PROVENANCE (INC-4091) ---
    CREATE (evi_canary:Evidence {
        id: 'EVI-901',
        kind: 'LOG_TRACE',
        source_type: 'LOG_AGGREGATOR',
        source_ref: 'logs://payment-service/canary-errors.log',
        observed_at: '2026-10-16T10:15:30Z',
        observation: 'Database connection pool starvation immediately following deployment v2.4.1 container rollout',
        summary: 'Database connection pool starvation immediately following deployment v2.4.1 container rollout',
        is_synthetic: true
    })
    CREATE (evi_sec:Evidence {
        id: 'EVI-902',
        kind: 'SECURITY_SCAN',
        source_type: 'VULNERABILITY_SCANNER',
        source_ref: 'trivy://scans/auth-tokens-lib-cve-2026-4412',
        observed_at: '2026-10-12T04:00:00Z',
        observation: 'CVE-2026-4412 published 4 days prior. Ingress traffic telemetry shows 0 exploit payload signatures',
        summary: 'CVE-2026-4412 published 4 days prior. Ingress traffic telemetry shows 0 exploit payload signatures',
        is_synthetic: true
    })
    CREATE (evi_latency:Evidence {
        id: 'EVI-903',
        kind: 'METRIC_ANOMALY',
        source_type: 'METRIC_TIMESERIES',
        source_ref: 'datadog://metrics/payment-service/p99-latency',
        observed_at: '2026-10-16T10:14:45Z',
        observation: 'P99 latency surged from 110ms to 17,800ms within 45 seconds of v2.4.1 deployment rollout',
        summary: 'P99 latency surged from 110ms to 17,800ms within 45 seconds of v2.4.1 deployment rollout',
        is_synthetic: true
    })

    CREATE (evi_canary)-[:SUPPORTS]->(inc)
    CREATE (evi_canary)-[:OBSERVED]->(s_pay)
    CREATE (evi_canary)-[:REFERS_TO]->(dep_pay_bad)

    CREATE (evi_sec)-[:SUPPORTS]->(inc)
    CREATE (evi_sec)-[:OBSERVED]->(s_pay)

    CREATE (evi_latency)-[:SUPPORTS]->(inc)
    CREATE (evi_latency)-[:OBSERVED]->(s_pay)
    CREATE (evi_latency)-[:REFERS_TO]->(dep_pay_bad)

    // --- 10. EVIDENCE & PROVENANCE (INC-3022) ---
    CREATE (evi_redis_config:Evidence {
        id: 'EVI-301',
        kind: 'LOG_TRACE',
        source_type: 'CONFIG_AUDIT',
        source_ref: 'redis://auth-cache/config.log',
        observed_at: '2026-10-17T08:11:00Z',
        observation: 'Redis maxmemory-policy misconfigured to volatile-ttl with 30s expiry instead of 24h in dep-auth-v1.4.2',
        summary: 'Redis maxmemory-policy misconfigured to volatile-ttl with 30s expiry instead of 24h in dep-auth-v1.4.2',
        is_synthetic: true
    })
    CREATE (evi_waf_ddos:Evidence {
        id: 'EVI-302',
        kind: 'METRIC_ANOMALY',
        source_type: 'WAF_METRICS',
        source_ref: 'waf://auth-service/ingress-rate',
        observed_at: '2026-10-17T08:13:00Z',
        observation: 'WAF ingress traffic reports normal login volume 118 req/s (0 DDoS anomaly score)',
        summary: 'WAF ingress traffic reports normal login volume 118 req/s (0 DDoS anomaly score)',
        is_synthetic: true
    })
    CREATE (evi_redis_config)-[:SUPPORTS]->(inc2)
    CREATE (evi_redis_config)-[:OBSERVED]->(s_auth)
    CREATE (evi_redis_config)-[:REFERS_TO]->(dep_auth_bad)
    CREATE (evi_waf_ddos)-[:SUPPORTS]->(inc2)
    CREATE (evi_waf_ddos)-[:OBSERVED]->(s_auth)

    // --- 11. EVIDENCE & PROVENANCE (INC-5102) ---
    CREATE (evi_carrier_outage:Evidence {
        id: 'EVI-501',
        kind: 'LOG_TRACE',
        source_type: 'STATUS_PAGE_INGEST',
        source_ref: 'carrier-api://status/dispatch-endpoint',
        observed_at: '2026-10-17T14:07:30Z',
        observation: 'Third-party delivery carrier API reports regional gateway outage on /v1/dispatch endpoint',
        summary: 'Third-party delivery carrier API reports regional gateway outage on /v1/dispatch endpoint',
        is_synthetic: true
    })
    CREATE (evi_internal_dns:Evidence {
        id: 'EVI-502',
        kind: 'METRIC_ANOMALY',
        source_type: 'NETWORK_TELEMETRY',
        source_ref: 'network://coredns/resolution-latency',
        observed_at: '2026-10-17T14:08:45Z',
        observation: 'Internal CoreDNS latency normal at 1.8ms; outbound NAT reports 0% packet loss to other external targets',
        summary: 'Internal CoreDNS latency normal at 1.8ms; outbound NAT reports 0% packet loss to other external targets',
        is_synthetic: true
    })
    CREATE (evi_carrier_outage)-[:SUPPORTS]->(inc3)
    CREATE (evi_carrier_outage)-[:OBSERVED]->(s_logistics)
    CREATE (evi_internal_dns)-[:SUPPORTS]->(inc3)
    CREATE (evi_internal_dns)-[:OBSERVED]->(s_logistics)

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
        "is_synthetic": True
    }


if __name__ == "__main__":
    print(f"Seeding FalkorDB graph '{settings.FALKORDB_GRAPH}'...")
    stats = seed_database()
    print("Seed complete successfully!")
    print(f"  Graph: {stats['graph']}")
    print(f"  Incident ID: {stats['incident_id']}")
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Relationships: {stats['total_edges']}")
