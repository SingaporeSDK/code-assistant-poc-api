"""
Graph Loader Module

Fetches graph structure from the analytics API and provides traversal functions
for GraphRAG.
"""
import os
import json
from typing import Dict, List, Set, Optional
from collections import defaultdict
import httpx

GRAPH_API_URL = os.getenv("GRAPH_API_URL", "http://localhost:5001/graph/nodes")
GRAPH_CACHE_TTL = int(os.getenv("GRAPH_CACHE_TTL", "300"))  # 5 minutes

_graph_data = None
_graph_cache_time = None


class GraphLoader:
    """Loads and provides access to the codebase graph structure."""

    def __init__(self, graph_url: str = GRAPH_API_URL):
        self.graph_url = graph_url
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        self.node_edges: Dict[str, List[Dict]] = defaultdict(list)  # node_id -> edges
        self._loaded = False

    def load(self) -> bool:
        """Fetch graph data from the analytics API."""
        try:
            response = httpx.get(self.graph_url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            self.nodes = {node["id"]: node for node in data.get("nodes", [])}
            self.edges = data.get("edges", [])

            # Build edge index for fast traversal
            for edge in self.edges:
                from_id = edge.get("from")
                to_id = edge.get("to")
                if from_id:
                    self.node_edges[from_id].append(edge)
                if to_id:
                    # Also index reverse for bidirectional traversal
                    self.node_edges[to_id].append(edge)

            self._loaded = True
            print(f"✅ Graph loaded: {len(self.nodes)} nodes, {len(self.edges)} edges")
            return True
        except Exception as e:
            print(f"⚠️ Failed to load graph from {self.graph_url}: {e}")
            self._loaded = False
            return False

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(
        self, node_id: str, relation_filter: Optional[str] = None
    ) -> List[Dict]:
        """Get all neighbors of a node, optionally filtered by relation type."""
        if not self._loaded or node_id not in self.node_edges:
            return []

        neighbors = []
        for edge in self.node_edges[node_id]:
            if relation_filter and edge.get("relation") != relation_filter:
                continue

            other_id = edge.get("to") if edge.get("from") == node_id else edge.get("from")
            if other_id and other_id in self.nodes:
                neighbors.append(self.nodes[other_id])

        return neighbors

    def traverse(
        self,
        start_node_ids: List[str],
        depth: int = 2,
        relation_filters: Optional[List[str]] = None,
    ) -> Set[str]:
        """
        Traverse graph from starting nodes up to specified depth.

        Args:
            start_node_ids: List of node IDs to start from
            depth: Maximum traversal depth
            relation_filters: Optional list of relation types to follow

        Returns:
            Set of node IDs reached during traversal
        """
        if not self._loaded:
            return set()

        visited = set()
        current_level = set(start_node_ids)

        for _ in range(depth):
            next_level = set()
            for node_id in current_level:
                if node_id in visited:
                    continue
                visited.add(node_id)

                for edge in self.node_edges.get(node_id, []):
                    if relation_filters and edge.get("relation") not in relation_filters:
                        continue

                    other_id = edge.get("to") if edge.get("from") == node_id else edge.get("from")
                    if other_id and other_id not in visited:
                        next_level.add(other_id)

            current_level = next_level
            if not current_level:
                break

        return visited

    def find_nodes_by_source(self, source_path: str) -> List[Dict]:
        """Find all nodes that reference a specific source file path."""
        if not self._loaded or not source_path:
            return []

        # Normalize paths for matching (handle both relative and absolute paths)
        # Extract just the filename and relevant path components
        import os
        source_normalized = os.path.normpath(source_path).lower()
        source_basename = os.path.basename(source_normalized)
        
        matches = []
        for node in self.nodes.values():
            node_source = node.get("source", "")
            if not node_source:
                continue
            
            # Normalize node source path
            node_normalized = os.path.normpath(node_source).lower()
            node_basename = os.path.basename(node_normalized)
            
            # Match if:
            # 1. Source path is contained in node source (both normalized)
            # 2. Node source ends with source path
            # 3. Basenames match (same filename)
            # 4. Path components match (e.g., both in mycarhub/src/)
            if (source_normalized in node_normalized or 
                node_normalized.endswith(source_normalized) or
                source_basename == node_basename or
                source_normalized.replace(source_basename, "") in node_normalized):
                matches.append(node)

        return matches

    def get_nodes_by_type(self, node_type: str) -> List[Dict]:
        """Get all nodes of a specific type."""
        if not self._loaded:
            return []

        return [node for node in self.nodes.values() if node.get("type") == node_type]

    def is_loaded(self) -> bool:
        """Check if graph is loaded."""
        return self._loaded


# Global graph loader instance
_graph_loader = None


def get_graph_loader() -> GraphLoader:
    """Get or create the global graph loader instance."""
    global _graph_loader
    if _graph_loader is None:
        _graph_loader = GraphLoader()
        _graph_loader.load()
    return _graph_loader


def reload_graph() -> bool:
    """Force reload the graph from the API."""
    global _graph_loader
    _graph_loader = GraphLoader()
    return _graph_loader.load()

