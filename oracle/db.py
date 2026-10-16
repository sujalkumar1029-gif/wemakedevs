"""
FalkorDB Client Connection & Safe Query Runner.
"""

from typing import Any, Dict, List, Optional
from falkordb import FalkorDB, Graph
from oracle.config import settings


def get_client() -> FalkorDB:
    """Returns a connected FalkorDB client."""
    return FalkorDB(host=settings.FALKORDB_HOST, port=settings.FALKORDB_PORT)


def get_graph(graph_name: Optional[str] = None) -> Graph:
    """Returns a selected graph instance."""
    name = graph_name or settings.FALKORDB_GRAPH
    return get_client().select_graph(name)


def run_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    graph_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Executes a parameterized Cypher query and returns the results as a list of dicts.
    """
    graph = get_graph(graph_name)
    result = graph.query(query, params=params)

    if not result.header or not result.result_set:
        return []

    # FalkorDB header format: [[col_type, col_name], ...]
    col_names = [col[1] for col in result.header]
    rows = []
    for row in result.result_set:
        rows.append(dict(zip(col_names, row)))
    return rows
