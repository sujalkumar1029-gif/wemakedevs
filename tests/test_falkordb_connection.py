#!/usr/bin/env python3
"""
FalkorDB Connection Smoke Test for ORACLE.
Verifies connectivity, graph creation, Cypher query execution, and cleanup.
"""

import os
import sys
import time
from falkordb import FalkorDB


def run_smoke_test():
    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", "6379"))
    graph_name = os.getenv("FALKORDB_TEST_GRAPH", "oracle_smoke_test")

    print(f"[ORACLE Smoke Test] Connecting to FalkorDB at {host}:{port}...")
    start_time = time.perf_counter()

    try:
        db = FalkorDB(host=host, port=port)
        ping_ok = db.connection.ping()
        connect_duration = (time.perf_counter() - start_time) * 1000
        print(f"[ORACLE Smoke Test] Ping check: {'PASSED' if ping_ok else 'FAILED'} ({connect_duration:.2f}ms)")
        if not ping_ok:
            print("[ORACLE Smoke Test] Error: Ping returned False", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"[ORACLE Smoke Test] Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        g = db.select_graph(graph_name)

        # Ensure clean state for test graph
        try:
            g.delete()
        except Exception:
            pass

        print(f"[ORACLE Smoke Test] Creating test incident topology in graph '{graph_name}'...")
        # Create a sample multi-node relationship: Incident -> AFFECTS -> Service
        create_query = """
        CREATE (inc:Incident {id: 'INC-SMOKE-01', title: 'High Error Rate', severity: 'CRITICAL'})
        CREATE (svc:Service {name: 'payment-gateway', tier: 1})
        CREATE (dep:Deployment {version: 'v2.4.1', status: 'CANARY_FAILED'})
        CREATE (inc)-[:AFFECTS]->(svc)
        CREATE (svc)-[:HAS_DEPLOYMENT]->(dep)
        RETURN inc.id AS incident_id, svc.name AS service_name, dep.version AS version
        """
        create_res = g.query(create_query)
        print(f"[ORACLE Smoke Test] Nodes created: {create_res.result_set}")

        # Query the graph back with multi-hop Cypher traversal
        print("[ORACLE Smoke Test] Executing multi-hop verification query...")
        verify_query = """
        MATCH (inc:Incident)-[:AFFECTS]->(svc:Service)-[:HAS_DEPLOYMENT]->(dep:Deployment)
        WHERE inc.id = 'INC-SMOKE-01'
        RETURN inc.title, svc.name, dep.version, dep.status
        """
        verify_res = g.query(verify_query)
        print(f"[ORACLE Smoke Test] Query Result: {verify_res.result_set}")

        # Validate result
        expected = [["High Error Rate", "payment-gateway", "v2.4.1", "CANARY_FAILED"]]
        if verify_res.result_set == expected:
            print("[ORACLE Smoke Test] Graph query and multi-hop traversal: PASSED")
        else:
            print(f"[ORACLE Smoke Test] Unexpected result set: {verify_res.result_set}", file=sys.stderr)
            sys.exit(1)

        # Cleanup test graph
        print(f"[ORACLE Smoke Test] Cleaning up test graph '{graph_name}'...")
        g.delete()
        print("[ORACLE Smoke Test] Graph deletion: PASSED")

        total_duration = (time.perf_counter() - start_time) * 1000
        print(f"[ORACLE Smoke Test] ALL SMOKE CHECKS PASSED in {total_duration:.2f}ms")
        return 0

    except Exception as e:
        print(f"[ORACLE Smoke Test] Execution error: {e}", file=sys.stderr)
        # Attempt cleanup on error
        try:
            db.select_graph(graph_name).delete()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(run_smoke_test())
