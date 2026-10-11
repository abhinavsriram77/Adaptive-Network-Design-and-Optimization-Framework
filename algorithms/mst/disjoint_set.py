"""Disjoint-Set Union (Union-Find) data structure with rank and path compression.

Provides near constant time O(alpha(V)) operations with integrated telemetry
counters for tracking amortized algorithmic operations in Kruskal's algorithm.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set


class DisjointSetUnion:
    """Disjoint-Set Union (DSU) with Union-by-Rank and Path Compression heuristics.
    
    Attributes:
        parent: Mapping of element to its immediate parent representative.
        rank: Upper bound on the height of each disjoint sub-tree.
        size: Number of elements in each connected set representative.
        find_ops: Number of find operations executed.
        union_ops: Number of union operations executed.
        compressions: Count of path compressions performed during find traversals.
    """

    def __init__(self, elements: Optional[Iterable[str]] = None) -> None:
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}
        self.size: Dict[str, int] = {}
        self._sets_count: int = 0

        # Telemetry counters
        self.find_ops: int = 0
        self.union_ops: int = 0
        self.compressions: int = 0

        if elements is not None:
            for elem in elements:
                self.make_set(elem)

    @property
    def sets_count(self) -> int:
        """Total number of disjoint components currently maintained."""
        return self._sets_count

    def make_set(self, x: str) -> None:
        """Initialize a new singleton set containing element x."""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            self.size[x] = 1
            self._sets_count += 1

    def find(self, x: str) -> str:
        """Find the canonical representative of the set containing x with path compression.
        
        Complexity:
            Amortized O(alpha(V)) where alpha is the inverse Ackermann function.
            
        Raises:
            KeyError: If element x has not been registered in the DSU.
        """
        self.find_ops += 1
        if x not in self.parent:
            raise KeyError(f"Element {x!r} not registered in DisjointSetUnion.")

        # Path compression: update parent pointer directly to set representative
        root = x
        while self.parent[root] != root:
            root = self.parent[root]

        curr = x
        while curr != root:
            next_node = self.parent[curr]
            if self.parent[curr] != root:
                self.parent[curr] = root
                self.compressions += 1
            curr = next_node

        return root

    def union(self, x: str, y: str) -> bool:
        """Unite the sets containing elements x and y using union-by-rank.
        
        Args:
            x: Element from first set.
            y: Element from second set.
            
        Returns:
            True if the sets were merged (previously disjoint).
            False if x and y were already in the same set (cycle detected).
        """
        self.union_ops += 1
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False

        # Union by rank heuristic
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
            self.size[root_y] += self.size[root_x]
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
            self.size[root_x] += self.size[root_y]
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
            self.size[root_x] += self.size[root_y]

        self._sets_count -= 1
        return True

    def connected(self, x: str, y: str) -> bool:
        """Check whether elements x and y belong to the same component."""
        return self.find(x) == self.find(y)

    def get_components(self) -> Dict[str, List[str]]:
        """Return mapping of canonical representative to all member elements."""
        components: Dict[str, List[str]] = {}
        for elem in self.parent:
            root = self.find(elem)
            if root not in components:
                components[root] = []
            components[root].append(elem)
        return components

    def reset_counters(self) -> None:
        """Reset telemetry operation counters."""
        self.find_ops = 0
        self.union_ops = 0
        self.compressions = 0
