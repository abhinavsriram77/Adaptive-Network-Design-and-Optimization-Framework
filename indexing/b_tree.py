"""Order-t B-Tree multi-way search tree simulating disk-backed block indexing.

Minimizes simulated secondary storage I/O transfers with O(log_t n) disk accesses
and dynamic block node splitting mechanics.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from indexing.base import BaseIndex


class BTreeNode:
    """A disk block node in an order-t B-Tree.
    
    Attributes:
        keys: Ordered list of search keys.
        values: Corresponding payload records.
        children: Child BTreeNode pointers.
        is_leaf: True if the node is a leaf (has no children).
    """

    def __init__(self, is_leaf: bool = True) -> None:
        self.keys: List[Any] = []
        self.values: List[Any] = []
        self.children: List[BTreeNode] = []
        self.is_leaf = is_leaf

    @property
    def key_count(self) -> int:
        return len(self.keys)


class BTree(BaseIndex):
    """Disk-backed multi-way B-Tree with order t (minimum degree).
    
    Attributes:
        t: Minimum degree (each non-root node contains between t-1 and 2t-1 keys).
        disk_reads: Simulated secondary storage block read operations.
        disk_writes: Simulated secondary storage block write operations.
        splits: Count of node split operations executed.
        comparisons: In-node key comparisons executed during searches/inserts.
    """

    def __init__(self, t: int = 3) -> None:
        if t < 2:
            raise ValueError(f"Minimum degree t must be >= 2, got {t}")
        self.t = t
        self.root = BTreeNode(is_leaf=True)
        self._size = 0

        # Secondary storage simulation telemetry
        self.disk_reads = 0
        self.disk_writes = 1  # Initial root write
        self.splits = 0
        self.comparisons = 0

    def __len__(self) -> int:
        return self._size

    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the B-Tree with O(log_t n) simulated block accesses."""
        return self._search_node(self.root, key)

    def _search_node(self, node: BTreeNode, key: Any) -> Optional[Any]:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            self.comparisons += 1
            i += 1

        if i < len(node.keys):
            self.comparisons += 1
            if key == node.keys[i]:
                return node.values[i]

        if node.is_leaf:
            return None

        # Simulate paging in the child block from disk
        self.disk_reads += 1
        return self._search_node(node.children[i], key)

    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value record, splitting full nodes along the descent path."""
        root = self.root

        # If key already exists in root or descendant, update in-place
        existing = self.search(key)
        if existing is not None:
            self._update_existing(self.root, key, value)
            return

        # If root is full (contains 2t - 1 keys), allocate new root and split
        if len(root.keys) == (2 * self.t - 1):
            new_root = BTreeNode(is_leaf=False)
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)

        self._size += 1

    def _update_existing(self, node: BTreeNode, key: Any, value: Any) -> bool:
        """Helper to find and overwrite an existing key in place."""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            node.values[i] = value
            self.disk_writes += 1
            return True
        if node.is_leaf:
            return False
        return self._update_existing(node.children[i], key, value)

    def _insert_non_full(self, node: BTreeNode, key: Any, value: Any) -> None:
        """Insert into a node that is guaranteed to not be full."""
        i = len(node.keys) - 1

        if node.is_leaf:
            # Shift elements to place (key, value) in sorted sequence
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                self.comparisons += 1
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = value
            self.disk_writes += 1
        else:
            # Find child pointer for descent
            while i >= 0 and key < node.keys[i]:
                self.comparisons += 1
                i -= 1
            i += 1

            # Proactively split full child during descent
            self.disk_reads += 1
            if len(node.children[i].keys) == (2 * self.t - 1):
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1

            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: BTreeNode, i: int) -> None:
        """Split parent's full child at index i into two half-full nodes."""
        self.splits += 1
        t = self.t
        full_child = parent.children[i]
        new_child = BTreeNode(is_leaf=full_child.is_leaf)

        # Median index to be promoted
        median_idx = t - 1
        median_key = full_child.keys[median_idx]
        median_val = full_child.values[median_idx]

        # Transfer upper t - 1 keys and values to new_child
        new_child.keys = full_child.keys[t : 2 * t - 1]
        new_child.values = full_child.values[t : 2 * t - 1]

        # Transfer upper t children if internal node
        if not full_child.is_leaf:
            new_child.children = full_child.children[t : 2 * t]
            full_child.children = full_child.children[:t]

        # Truncate full_child to retain lower t - 1 keys
        full_child.keys = full_child.keys[:t - 1]
        full_child.values = full_child.values[:t - 1]

        # Insert new_child into parent's children array
        parent.children.insert(i + 1, new_child)

        # Promote median key and value to parent
        parent.keys.insert(i, median_key)
        parent.values.insert(i, median_val)

        # Account for writing parent, full_child, and new_child back to simulated disk
        self.disk_writes += 3

    def validate_invariants(self) -> Tuple[bool, str]:
        """Validate all formal structural invariants of an order-t B-Tree."""
        if self._size == 0:
            return True, "Empty tree is valid."

        def check_node(node: BTreeNode, is_root: bool, depth: int) -> Tuple[bool, Optional[int], str]:
            # 1. Key count limits
            n_keys = len(node.keys)
            if not is_root:
                if not (self.t - 1 <= n_keys <= 2 * self.t - 1):
                    return False, None, f"Node violates key count: {n_keys} not in [{self.t-1}, {2*self.t-1}]."
            else:
                if not (1 <= n_keys <= 2 * self.t - 1):
                    return False, None, f"Root violates key count: {n_keys} not in [1, {2*self.t-1}]."

            # 2. Keys strictly sorted
            for i in range(len(node.keys) - 1):
                if node.keys[i] >= node.keys[i + 1]:
                    return False, None, f"Keys out of order: {node.keys[i]} >= {node.keys[i+1]}."

            # 3. Children count for internal nodes
            if not node.is_leaf:
                if len(node.children) != n_keys + 1:
                    return False, None, f"Internal node has {len(node.children)} children for {n_keys} keys."

                # Verify key partitioning across children
                for i, child in enumerate(node.children):
                    for k in child.keys:
                        if i > 0 and k <= node.keys[i - 1]:
                            return False, None, f"Child key {k} <= parent partition key {node.keys[i-1]}."
                        if i < n_keys and k >= node.keys[i]:
                            return False, None, f"Child key {k} >= parent partition key {node.keys[i]}."

                # Recurse down children and check leaf depth equality
                child_depths = []
                for child in node.children:
                    valid, d, err = check_node(child, False, depth + 1)
                    if not valid:
                        return False, None, err
                    child_depths.append(d)

                # All leaves must reside at identical depth
                if len(set(child_depths)) != 1:
                    return False, None, f"Leaves reside at unequal depths: {child_depths}."

                return True, child_depths[0], ""
            else:
                return True, depth, ""

        valid, _, msg = check_node(self.root, True, 0)
        return valid, msg if not valid else "All B-Tree invariants hold."
