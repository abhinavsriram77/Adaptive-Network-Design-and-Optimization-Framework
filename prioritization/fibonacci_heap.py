"""Fibonacci Heap priority queue implementation for high-frequency incident triage.

Maintains a flexible forest of min-heap ordered trees with circular doubly-linked lists
and cascading cuts, achieving O(1) amortized bounds for insert, union, and decrease-key.
"""

from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

from prioritization.base import BasePriorityQueue, QueueTelemetry


class FibonacciNode:
    """Node in a Fibonacci Heap.
    
    Attributes:
        key: Numeric priority key (lower = higher urgency).
        value: Associated payload (e.g., NetworkIncident).
        degree: Number of children.
        mark: True if node has lost a child since being attached to its current parent.
        parent: Pointer to parent node.
        child: Pointer to any child node in circular child list.
        left: Left sibling in circular doubly-linked list.
        right: Right sibling in circular doubly-linked list.
    """

    def __init__(self, key: float, value: Any) -> None:
        self.key: float = key
        self.value: Any = value
        self.degree: int = 0
        self.mark: bool = False
        self.parent: Optional[FibonacciNode] = None
        self.child: Optional[FibonacciNode] = None
        self.left: FibonacciNode = self
        self.right: FibonacciNode = self


class FibonacciHeap(BasePriorityQueue):
    """Fibonacci Heap priority queue optimizing dynamic alarm escalation."""

    def __init__(self) -> None:
        self.min_node: Optional[FibonacciNode] = None
        self._size: int = 0
        self.marked_count: int = 0
        self.trees_count: int = 0
        self.telemetry = QueueTelemetry()

    @property
    def name(self) -> str:
        return "Fibonacci Heap (Amortized O(1) Decrease-Key & Cascading Cuts)"

    def __len__(self) -> int:
        return self._size

    @property
    def potential(self) -> int:
        """Calculate current amortized potential: Phi(H) = t(H) + 2 * m(H)."""
        return self.trees_count + 2 * self.marked_count

    def insert(self, key: float, value: Any) -> FibonacciNode:
        """Insert a key-value record in O(1) amortized and worst-case time."""
        self.telemetry.inserts += 1
        node = FibonacciNode(key=key, value=value)

        if self.min_node is None:
            self.min_node = node
        else:
            self._splice_into_root_list(node)
            self.telemetry.comparisons += 1
            if node.key < self.min_node.key:
                self.min_node = node

        self._size += 1
        self.trees_count += 1
        return node

    def find_min(self) -> Optional[Tuple[float, Any]]:
        """Return minimum (key, value) in O(1) worst-case time."""
        self.telemetry.find_mins += 1
        if self.min_node is None:
            return None
        return self.min_node.key, self.min_node.value

    def union(self, other: BasePriorityQueue) -> None:
        """Merge another FibonacciHeap into self in O(1) time."""
        if not isinstance(other, FibonacciHeap):
            raise TypeError(f"Cannot union FibonacciHeap with {type(other).__name__}")

        self.telemetry.unions += 1
        if other.min_node is None:
            return

        if self.min_node is None:
            self.min_node = other.min_node
            self._size = other._size
            self.marked_count = other.marked_count
            self.trees_count = other.trees_count
            other.min_node = None
            other._size = 0
            other.marked_count = 0
            other.trees_count = 0
            return

        # Concatenate circular root lists
        min1 = self.min_node
        min2 = other.min_node

        min1_next = min1.right
        min2_prev = min2.left

        min1.right = min2
        min2.left = min1
        min1_next.left = min2_prev
        min2_prev.right = min1_next

        self.telemetry.comparisons += 1
        if min2.key < min1.key:
            self.min_node = min2

        self._size += other._size
        self.marked_count += other.marked_count
        self.trees_count += other.trees_count

        other.min_node = None
        other._size = 0
        other.marked_count = 0
        other.trees_count = 0

    def extract_min(self) -> Optional[Tuple[float, Any]]:
        """Extract minimum node in O(log n) amortized time."""
        self.telemetry.extract_mins += 1
        z = self.min_node
        if z is None:
            return None

        # 1. Promote all children of z to the root list
        if z.child is not None:
            children = self._iterate_circular_list(z.child)
            for child in children:
                child.parent = None
                if child.mark:
                    child.mark = False
                    self.marked_count -= 1
                self._splice_into_root_list(child)
                self.trees_count += 1
            z.child = None

        # 2. Remove z from the root list
        self._remove_from_circular_list(z)
        self.trees_count -= 1
        self._size -= 1

        if z == z.right:
            self.min_node = None
        else:
            self.min_node = z.right
            self._consolidate()

        return z.key, z.value

    def decrease_key(self, node: FibonacciNode, new_key: float) -> None:
        """Decrease key of a node in O(1) amortized time using cascading cuts."""
        self.telemetry.decrease_keys += 1
        if new_key > node.key:
            raise ValueError(f"New key {new_key} cannot be greater than current key {node.key}")

        node.key = new_key
        y = node.parent

        if y is not None and node.key < y.key:
            self.telemetry.comparisons += 1
            self._cut(node, y)
            self._cascading_cut(y)

        self.telemetry.comparisons += 1
        if self.min_node is not None and node.key < self.min_node.key:
            self.min_node = node

    def _cut(self, x: FibonacciNode, y: FibonacciNode) -> None:
        """Cut child x from parent y and place x into the root list."""
        # Remove x from child list of y
        if x.right == x:
            y.child = None
        else:
            if y.child == x:
                y.child = x.right
            self._remove_from_circular_list(x)

        y.degree -= 1
        self._splice_into_root_list(x)
        x.parent = None
        if x.mark:
            x.mark = False
            self.marked_count -= 1
        self.trees_count += 1

    def _cascading_cut(self, y: FibonacciNode) -> None:
        """Recursively cut marked ancestors losing a second child."""
        z = y.parent
        if z is not None:
            if not y.mark:
                y.mark = True
                self.marked_count += 1
            else:
                self._cut(y, z)
                self._cascading_cut(z)

    def _consolidate(self) -> None:
        """Consolidate root list by linking trees of equal degree."""
        # Upper bound on max degree: D(n) <= floor(log_phi(n)) + 2
        phi = 1.618033988749895
        max_deg = int(math.log(max(1, self._size) + 1, phi)) + 5
        a: List[Optional[FibonacciNode]] = [None] * max_deg

        root_nodes = self._iterate_circular_list(self.min_node)

        for w in root_nodes:
            x = w
            d = x.degree
            while d < len(a) and a[d] is not None:
                y = a[d]
                self.telemetry.comparisons += 1
                if x.key > y.key:
                    x, y = y, x

                self._link(y, x)
                a[d] = None
                d += 1

            if d >= len(a):
                a.extend([None] * (d - len(a) + 5))
            a[d] = x

        # Reconstruct clean circular root list from array a
        self.min_node = None
        self.trees_count = 0

        for node in a:
            if node is not None:
                node.left = node
                node.right = node
                if self.min_node is None:
                    self.min_node = node
                else:
                    self._splice_into_root_list(node)
                    self.telemetry.comparisons += 1
                    if node.key < self.min_node.key:
                        self.min_node = node
                self.trees_count += 1

    def _link(self, y: FibonacciNode, x: FibonacciNode) -> None:
        """Remove y from root list and make it a child of x."""
        self._remove_from_circular_list(y)
        self.trees_count -= 1

        y.parent = x
        if x.child is None:
            x.child = y
            y.left = y
            y.right = y
        else:
            self._splice_into_list(x.child, y)

        x.degree += 1
        if y.mark:
            y.mark = False
            self.marked_count -= 1

    def _splice_into_root_list(self, node: FibonacciNode) -> None:
        """Splice node into the root list adjacent to min_node."""
        if self.min_node is not None:
            self._splice_into_list(self.min_node, node)

    def _splice_into_list(self, anchor: FibonacciNode, node: FibonacciNode) -> None:
        """Splice a singleton node into anchor's circular doubly-linked list."""
        node.left = anchor
        node.right = anchor.right
        anchor.right.left = node
        anchor.right = node

    def _remove_from_circular_list(self, node: FibonacciNode) -> None:
        """Remove node from circular doubly-linked list."""
        node.left.right = node.right
        node.right.left = node.left

    def _iterate_circular_list(self, start: Optional[FibonacciNode]) -> List[FibonacciNode]:
        """Safely traverse and return all nodes in a circular doubly-linked list."""
        if start is None:
            return []
        nodes = []
        curr = start
        while True:
            nodes.append(curr)
            curr = curr.right
            if curr == start:
                break
        return nodes

    def validate_invariants(self) -> Tuple[bool, str]:
        """Validate all structural invariants of the Fibonacci Heap."""
        if self.min_node is None:
            if self._size != 0:
                return False, f"Empty heap min_node but _size={self._size}."
            return True, "Empty Fibonacci heap is valid."

        roots = self._iterate_circular_list(self.min_node)
        if len(roots) != self.trees_count:
            return False, f"Root count {len(roots)} != trees_count {self.trees_count}."

        actual_min = min(roots, key=lambda n: n.key)
        if self.min_node.key > actual_min.key:
            return False, f"min_node {self.min_node.key} > actual minimum {actual_min.key}."

        total_nodes = 0
        actual_marked = 0

        for root in roots:
            if root.parent is not None:
                return False, f"Root node {root.key} has non-None parent."
            valid, n_count, m_count, err = self._validate_subtree(root)
            if not valid:
                return False, err
            total_nodes += n_count
            actual_marked += m_count

        if total_nodes != self._size:
            return False, f"Counted nodes ({total_nodes}) != _size ({self._size})."
        if actual_marked != self.marked_count:
            return False, f"Counted marked ({actual_marked}) != marked_count ({self.marked_count})."

        return True, "All Fibonacci Heap invariants hold."

    def _validate_subtree(self, node: FibonacciNode) -> Tuple[bool, int, int, str]:
        """Recursively validate min-heap property and child counts."""
        sub_count = 1
        mark_count = 1 if node.mark else 0

        if node.child is not None:
            children = self._iterate_circular_list(node.child)
            if len(children) != node.degree:
                return False, 0, 0, f"Node degree {node.degree} != child count {len(children)}."

            for child in children:
                if child.key < node.key:
                    return False, 0, 0, f"Min-heap violation: child {child.key} < parent {node.key}."
                if child.parent != node:
                    return False, 0, 0, "Child parent pointer mismatch."

                valid, c_nodes, c_marked, err = self._validate_subtree(child)
                if not valid:
                    return False, 0, 0, err
                sub_count += c_nodes
                mark_count += c_marked

        return True, sub_count, mark_count, ""

