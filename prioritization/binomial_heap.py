"""Binomial Heap priority queue implementation for incident triage.

Maintains a forest of binomial trees satisfying strict order and degree invariants,
achieving O(log n) worst-case bounds for insert, merge, extract-min, and decrease-key.
"""

from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

from prioritization.base import BasePriorityQueue, QueueTelemetry


class BinomialNode:
    """Node in a Binomial Tree.
    
    Attributes:
        key: Numeric priority key (lower = higher urgency).
        value: Associated payload (e.g., NetworkIncident).
        degree: Number of children attached to this node.
        parent: Pointer to parent node.
        child: Pointer to leftmost child.
        sibling: Pointer to immediate right sibling.
    """

    def __init__(self, key: float, value: Any) -> None:
        self.key: float = key
        self.value: Any = value
        self.degree: int = 0
        self.parent: Optional[BinomialNode] = None
        self.child: Optional[BinomialNode] = None
        self.sibling: Optional[BinomialNode] = None
        # Handle to keep external reference updated if satellite data swaps
        self.handle: Optional[Any] = None


class BinomialHeap(BasePriorityQueue):
    """Binomial Heap priority queue composed of ordered binomial trees."""

    def __init__(self) -> None:
        self.head: Optional[BinomialNode] = None
        self._size: int = 0
        self.telemetry = QueueTelemetry()

    @property
    def name(self) -> str:
        return "Binomial Heap (Forest of B_k Trees)"

    def __len__(self) -> int:
        return self._size

    def _link(self, y: BinomialNode, z: BinomialNode) -> None:
        """Make node y the leftmost child of node z."""
        self.telemetry.comparisons += 1
        y.parent = z
        y.sibling = z.child
        z.child = y
        z.degree += 1

    def _merge_root_lists(
        self, h1: Optional[BinomialNode], h2: Optional[BinomialNode]
    ) -> Optional[BinomialNode]:
        """Merge two root lists sorted by increasing degree into a single sorted list."""
        if h1 is None:
            return h2
        if h2 is None:
            return h1

        dummy = BinomialNode(0.0, None)
        tail = dummy

        curr1 = h1
        curr2 = h2

        while curr1 is not None and curr2 is not None:
            if curr1.degree <= curr2.degree:
                tail.sibling = curr1
                curr1 = curr1.sibling
            else:
                tail.sibling = curr2
                curr2 = curr2.sibling
            tail = tail.sibling

        if curr1 is not None:
            tail.sibling = curr1
        else:
            tail.sibling = curr2

        return dummy.sibling

    def union(self, other: BasePriorityQueue) -> None:
        """Merge another BinomialHeap into self, resolving degree collisions with carries."""
        if not isinstance(other, BinomialHeap):
            raise TypeError(f"Cannot union BinomialHeap with {type(other).__name__}")

        self.telemetry.unions += 1
        if other.head is None:
            return

        if self.head is None:
            self.head = other.head
            self._size = other._size
            other.head = None
            other._size = 0
            return

        total_size = self._size + other._size
        new_head = self._merge_root_lists(self.head, other.head)

        # Disarm other
        other.head = None
        other._size = 0

        if new_head is None:
            self.head = None
            self._size = 0
            return

        prev_x: Optional[BinomialNode] = None
        x: Optional[BinomialNode] = new_head
        next_x: Optional[BinomialNode] = x.sibling

        while next_x is not None:
            # Case 1: degrees are not equal or 3 consecutive equal degrees (lookahead)
            if (x.degree != next_x.degree) or (
                next_x.sibling is not None and next_x.sibling.degree == x.degree
            ):
                prev_x = x
                x = next_x
            # Case 2: x.key <= next_x.key -> next_x becomes child of x
            elif x.key <= next_x.key:
                x.sibling = next_x.sibling
                self._link(next_x, x)
            # Case 3: x.key > next_x.key -> x becomes child of next_x
            else:
                if prev_x is None:
                    new_head = next_x
                else:
                    prev_x.sibling = next_x
                self._link(x, next_x)
                x = next_x

            next_x = x.sibling

        self.head = new_head
        self._size = total_size

    def insert(self, key: float, value: Any) -> BinomialNode:
        """Insert key-value pair in O(log n) worst-case time."""
        self.telemetry.inserts += 1
        node = BinomialNode(key=key, value=value)
        temp_heap = BinomialHeap()
        temp_heap.head = node
        temp_heap._size = 1
        self.union(temp_heap)
        return node

    def find_min(self) -> Optional[Tuple[float, Any]]:
        """Return minimum (key, value) in O(log n) time without removing."""
        self.telemetry.find_mins += 1
        if self.head is None:
            return None

        min_node = self.head
        curr = self.head.sibling

        while curr is not None:
            self.telemetry.comparisons += 1
            if curr.key < min_node.key:
                min_node = curr
            curr = curr.sibling

        return min_node.key, min_node.value

    def extract_min(self) -> Optional[Tuple[float, Any]]:
        """Extract and return minimum (key, value) in O(log n) time."""
        self.telemetry.extract_mins += 1
        if self.head is None:
            return None

        # 1. Find root x with minimum key and track predecessor
        prev_min: Optional[BinomialNode] = None
        min_node = self.head
        prev = self.head
        curr = self.head.sibling

        while curr is not None:
            self.telemetry.comparisons += 1
            if curr.key < min_node.key:
                min_node = curr
                prev_min = prev
            prev = curr
            curr = curr.sibling

        # 2. Remove min_node from root list
        if prev_min is None:
            self.head = min_node.sibling
        else:
            prev_min.sibling = min_node.sibling

        # 3. Reverse children of min_node to form a root list sorted by increasing degree
        child = min_node.child
        reversed_head: Optional[BinomialNode] = None

        while child is not None:
            next_child = child.sibling
            child.parent = None
            child.sibling = reversed_head
            reversed_head = child
            child = next_child

        min_tree_size = 1 << min_node.degree
        self._size -= min_tree_size

        # 4. Union remaining heap with reversed children
        if reversed_head is not None:
            temp_heap = BinomialHeap()
            temp_heap.head = reversed_head
            temp_heap._size = min_tree_size - 1
            self.union(temp_heap)

        # Net reduction in size: 1 element
        self._size = max(0, self._size)

        return min_node.key, min_node.value

    def decrease_key(self, node: BinomialNode, new_key: float) -> None:
        """Decrease the key of a specific node in O(log n) time.
        
        Args:
            node: BinomialNode reference returned from insert.
            new_key: New priority score strictly less than current key.
        """
        self.telemetry.decrease_keys += 1
        if new_key > node.key:
            raise ValueError(f"New key {new_key} cannot be greater than current key {node.key}")

        node.key = new_key
        curr = node
        parent = curr.parent

        # Bubble up towards the root
        while parent is not None and curr.key < parent.key:
            self.telemetry.comparisons += 1
            # Swap key and value satellite data
            curr.key, parent.key = parent.key, curr.key
            curr.value, parent.value = parent.value, curr.value

            curr = parent
            parent = curr.parent

    def validate_invariants(self) -> Tuple[bool, str]:
        """Validate all formal structural invariants of the Binomial Heap."""
        if self.head is None:
            if self._size != 0:
                return False, f"Empty heap head but _size={self._size}."
            return True, "Empty binomial heap is valid."

        # 1. Check unique, strictly increasing degrees in root list
        curr = self.head
        prev_degree = -1
        counted_nodes = 0

        while curr is not None:
            if curr.degree <= prev_degree:
                return False, f"Root list degrees not strictly increasing: {curr.degree} <= {prev_degree}."
            prev_degree = curr.degree

            # 2. Verify tree structure recursively
            valid_tree, tree_size, err = self._validate_binomial_tree(curr, curr.degree)
            if not valid_tree:
                return False, err

            expected_tree_size = 1 << curr.degree
            if tree_size != expected_tree_size:
                return False, f"B_{curr.degree} tree size mismatch: {tree_size} != {expected_tree_size}."

            counted_nodes += tree_size
            curr = curr.sibling

        # 3. Verify total node count
        if counted_nodes != self._size:
            return False, f"Total nodes counted ({counted_nodes}) != _size ({self._size})."

        return True, "All Binomial Heap invariants hold."

    def _validate_binomial_tree(
        self, node: BinomialNode, expected_degree: int
    ) -> Tuple[bool, int, str]:
        """Recursively check degree, min-heap property, and size of a binomial tree."""
        if node.degree != expected_degree:
            return False, 0, f"Node degree {node.degree} != expected {expected_degree}."

        child = node.child
        actual_children_count = 0
        total_nodes = 1
        expected_child_deg = expected_degree - 1

        while child is not None:
            # Check min-heap property
            if child.key < node.key:
                return False, 0, f"Min-heap violation: child key {child.key} < parent key {node.key}."
            if child.parent != node:
                return False, 0, "Child parent pointer mismatch."

            valid_sub, sub_size, err = self._validate_binomial_tree(child, expected_child_deg)
            if not valid_sub:
                return False, 0, err

            total_nodes += sub_size
            actual_children_count += 1
            expected_child_deg -= 1
            child = child.sibling

        if actual_children_count != expected_degree:
            return False, 0, f"Child count {actual_children_count} != degree {expected_degree}."

        return True, total_nodes, ""

