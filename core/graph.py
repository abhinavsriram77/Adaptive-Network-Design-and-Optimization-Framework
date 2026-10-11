"""Network graph domain model with dual topological representation.

Maintains synchronized Adjacency List and Adjacency Matrix views to support
both sparse-optimized (Kruskal) and dense-optimized (Prim / Floyd-Warshall) algorithms.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

from core.edge import NetworkEdge
from core.node import Node, NodeType


class NetworkGraph:
    """Graph representation storing heterogeneous network vertices and transmission edges.
    
    Provides dual access representations (Adjacency List and Adjacency Matrix)
    and metric derivation including graph density and topological connectivity.
    
    Attributes:
        directed: Whether the graph edges are directional.
    """

    def __init__(self, directed: bool = False) -> None:
        self._directed: bool = directed
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[Tuple[str, str], NetworkEdge] = {}
        self._adj: Dict[str, Dict[str, NetworkEdge]] = {}

    @property
    def directed(self) -> bool:
        """Whether graph is directed."""
        return self._directed

    @property
    def num_nodes(self) -> int:
        """Number of vertices |V| in the graph."""
        return len(self._nodes)

    @property
    def num_edges(self) -> int:
        """Number of unique edges |E| in the graph."""
        return len(self._edges)

    def add_node(self, node: Node) -> None:
        """Register a node vertex into the graph topology.
        
        Args:
            node: Node instance to insert.
            
        Raises:
            ValueError: If a node with the same ID already exists.
        """
        if node.id in self._nodes:
            raise ValueError(f"Node with id {node.id!r} already exists in graph.")
        self._nodes[node.id] = node
        self._adj[node.id] = {}

    def get_node(self, node_id: str) -> Optional[Node]:
        """Retrieve node by identifier."""
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Check whether a node ID exists."""
        return node_id in self._nodes

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all incident edges.
        
        Args:
            node_id: ID of node to remove.
            
        Raises:
            KeyError: If node_id does not exist.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id!r} not found in graph.")

        # Identify all incident edges to remove
        incident = list(self.incident_edges(node_id))
        for edge in incident:
            self.remove_edge(edge.u, edge.v)

        del self._nodes[node_id]
        del self._adj[node_id]

    def add_edge(self, edge: NetworkEdge) -> None:
        """Add an edge between two registered nodes.
        
        If an edge already connects u and v, the edge with the smaller weight
        is retained (parallel link reduction for MST/shortest path).
        
        Args:
            edge: NetworkEdge to insert.
            
        Raises:
            ValueError: If edge endpoints are missing from graph or directional mismatch.
        """
        if edge.directed != self._directed:
            raise ValueError(
                f"Edge directionality ({edge.directed}) does not match graph directed={self._directed}"
            )
        if edge.u not in self._nodes:
            raise ValueError(f"Endpoint u={edge.u!r} does not exist in graph.")
        if edge.v not in self._nodes:
            raise ValueError(f"Endpoint v={edge.v!r} does not exist in graph.")

        key = edge.canonical_endpoints
        if key in self._edges:
            existing = self._edges[key]
            # Parallel edge handling: retain the one with lower weight
            if edge.weight >= existing.weight:
                return

        self._edges[key] = edge
        self._adj[edge.u][edge.v] = edge
        if not self._directed:
            self._adj[edge.v][edge.u] = edge

    def get_edge(self, u: str, v: str) -> Optional[NetworkEdge]:
        """Retrieve edge connecting u and v if present."""
        if self._directed:
            return self._adj.get(u, {}).get(v)
        key = (u, v) if u <= v else (v, u)
        return self._edges.get(key)

    def has_edge(self, u: str, v: str) -> bool:
        """Check if an edge connects u and v."""
        return self.get_edge(u, v) is not None

    def remove_edge(self, u: str, v: str) -> None:
        """Remove the edge connecting u and v.
        
        Raises:
            KeyError: If no edge connects u and v.
        """
        if not self.has_edge(u, v):
            raise KeyError(f"No edge found between {u!r} and {v!r}.")

        if self._directed:
            key = (u, v)
            del self._edges[key]
            del self._adj[u][v]
        else:
            key = (u, v) if u <= v else (v, u)
            del self._edges[key]
            if v in self._adj.get(u, {}):
                del self._adj[u][v]
            if u in self._adj.get(v, {}):
                del self._adj[v][u]

    def neighbors(self, node_id: str) -> List[str]:
        """Return list of neighbor node IDs adjacent to node_id."""
        if node_id not in self._adj:
            raise KeyError(f"Node {node_id!r} not found in graph.")
        return list(self._adj[node_id].keys())

    def incident_edges(self, node_id: str) -> List[NetworkEdge]:
        """Return list of edges incident to node_id."""
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id!r} not found in graph.")

        if not self._directed:
            return list(self._adj[node_id].values())

        # For directed graphs, collect outgoing and incoming edges
        edges: Set[NetworkEdge] = set(self._adj[node_id].values())
        for u in self._nodes:
            if node_id in self._adj[u]:
                edges.add(self._adj[u][node_id])
        return list(edges)

    def get_all_nodes(self) -> List[Node]:
        """Return list of all registered nodes."""
        return list(self._nodes.values())

    def get_all_edges(self) -> List[NetworkEdge]:
        """Return list of all unique edges."""
        return list(self._edges.values())

    def density(self) -> float:
        """Calculate topological edge density D(G).
        
        For undirected graphs:
            D = (2 * |E|) / (|V| * (|V| - 1))
        For directed graphs:
            D = |E| / (|V| * (|V| - 1))
            
        Returns:
            Float density in [0.0, 1.0]. Returns 0.0 if |V| <= 1.
        """
        v = self.num_nodes
        e = self.num_edges
        if v <= 1:
            return 0.0

        max_possible_edges = v * (v - 1)
        if not self._directed:
            max_possible_edges /= 2.0

        return e / max_possible_edges

    def connected_components(self) -> List[Set[str]]:
        """Identify connected components using Breadth-First Search.
        
        Returns:
            List of sets, each containing node IDs of a connected component.
        """
        visited: Set[str] = set()
        components: List[Set[str]] = []

        for node_id in self._nodes:
            if node_id not in visited:
                comp: Set[str] = set()
                queue: deque[str] = deque([node_id])
                visited.add(node_id)

                while queue:
                    curr = queue.popleft()
                    comp.add(curr)
                    for nbr in self._adj[curr]:
                        if nbr not in visited:
                            visited.add(nbr)
                            queue.append(nbr)
                components.append(comp)

        return components

    def is_connected(self) -> bool:
        """Determine whether the graph forms a single connected component.
        
        Returns:
            True if |V| <= 1 or all nodes belong to a single component.
        """
        if self.num_nodes <= 1:
            return True
        return len(self.connected_components()) == 1

    def to_adjacency_matrix(
        self, metric: str = "weight"
    ) -> Tuple[List[str], List[List[float]]]:
        """Generate a dense cost matrix representation.
        
        Used for dense Prim MST and all-pairs shortest paths (Floyd-Warshall).
        
        Args:
            metric: Edge attribute name to populate ("weight", "latency_ms", etc.).
            
        Returns:
            Tuple of:
              - sorted list of node IDs corresponding to matrix indices.
              - 2D float matrix of dimension |V| x |V|. Diagonal is 0.0,
                non-adjacent entries are float('inf').
        """
        node_ids = sorted(self._nodes.keys())
        idx_map = {nid: i for i, nid in enumerate(node_ids)}
        n = len(node_ids)

        matrix = [[math.inf] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 0.0

        for edge in self._edges.values():
            i = idx_map[edge.u]
            j = idx_map[edge.v]
            val = getattr(edge, metric, edge.weight)

            matrix[i][j] = val
            if not self._directed:
                matrix[j][i] = val

        return node_ids, matrix

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph to dictionary structure."""
        return {
            "directed": self._directed,
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NetworkGraph:
        """Reconstruct a NetworkGraph from dictionary representation."""
        graph = cls(directed=data.get("directed", False))
        for nd in data.get("nodes", []):
            ntype = nd.get("node_type", NodeType.NETWORK_HUB.value)
            node_kwargs = {
                "id": nd["id"],
                "name": nd["name"],
                "latitude": nd.get("latitude", 0.0),
                "longitude": nd.get("longitude", 0.0),
                "processing_capacity": nd.get("processing_capacity", 100.0),
                "memory_capacity_mb": nd.get("memory_capacity_mb", 1024.0),
                "is_active": nd.get("is_active", True),
                "metadata": nd.get("metadata", {}),
            }
            if ntype == NodeType.DATA_CENTER.value:
                from core.node import DataCenter

                node = DataCenter(
                    **node_kwargs,
                    server_rack_count=nd.get("server_rack_count", 128),
                    storage_capacity_tb=nd.get("storage_capacity_tb", 1000.0),
                    tier_rating=nd.get("tier_rating", 4),
                )
            elif ntype == NodeType.IOT_GATEWAY.value:
                from core.node import IoTGateway

                node = IoTGateway(
                    **node_kwargs,
                    sensor_channel_count=nd.get("sensor_channel_count", 16),
                    battery_powered=nd.get("battery_powered", False),
                    battery_level_pct=nd.get("battery_level_pct"),
                    duty_cycle_pct=nd.get("duty_cycle_pct", 100.0),
                )
            else:
                from core.node import NetworkHub

                node = NetworkHub(
                    **node_kwargs,
                    switching_capacity_gbps=nd.get("switching_capacity_gbps", 400.0),
                    max_connected_ports=nd.get("max_connected_ports", 64),
                )
            graph.add_node(node)

        for ed in data.get("edges", []):
            edge = NetworkEdge(
                u=ed["u"],
                v=ed["v"],
                weight=ed["weight"],
                latency_ms=ed.get("latency_ms", 1.0),
                bandwidth_gbps=ed.get("bandwidth_gbps", 10.0),
                reliability_score=ed.get("reliability_score", 0.99),
                directed=ed.get("directed", False),
                metadata=ed.get("metadata", {}),
            )
            graph.add_edge(edge)

        return graph
