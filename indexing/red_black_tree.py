"""Red-Black Tree balanced search tree implementation for in-memory indexing.

Guarantees O(log n) worst-case time complexity for dictionary operations through
strict structural invariants, recoloring passes, and tree rotations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Tuple

from indexing.base import BaseIndex


class Color(str, Enum):
    RED = "RED"
    BLACK = "BLACK"


class RBNode:
    """Node in a Red-Black Tree.
    
    Attributes:
        key: Search key (comparable).
        value: Stored data payload.
        color: Color.RED or Color.BLACK.
        left: Left child reference.
        right: Right child reference.
        parent: Parent node reference.
    """

    def __init__(
        self,
        key: Any,
        value: Any,
        color: Color = Color.RED,
        left: Optional[RBNode] = None,
        right: Optional[RBNode] = None,
        parent: Optional[RBNode] = None,
    ) -> None:
        self.key = key
        self.value = value
        self.color = color
        self.left = left
        self.right = right
        self.parent = parent


class RedBlackTree(BaseIndex):
    """Balanced Red-Black Tree maintaining O(log n) search and insertion bounds."""

    def __init__(self) -> None:
        # Sentinel NIL leaf node
        self.NIL = RBNode(key=None, value=None, color=Color.BLACK)
        self.NIL.left = self.NIL
        self.NIL.right = self.NIL
        self.NIL.parent = self.NIL

        self.root = self.NIL
        self._size = 0

        # Telemetry counters
        self.rotations = 0
        self.recolorings = 0
        self.comparisons = 0

    def __len__(self) -> int:
        return self._size

    def search(self, key: Any) -> Optional[Any]:
        """Search for a value by key in O(log n) time.
        
        Args:
            key: Comparable search key.
            
        Returns:
            Associated value if present, else None.
        """
        curr = self.root
        while curr != self.NIL:
            self.comparisons += 1
            if key == curr.key:
                return curr.value
            elif key < curr.key:
                curr = curr.left
            else:
                curr = curr.right
        return None

    def insert(self, key: Any, value: Any) -> None:
        """Insert or update a key-value pair and restore Red-Black invariants.
        
        Args:
            key: Comparable search key.
            value: Associated payload.
        """
        # If key already exists, update in-place without altering tree structure
        curr = self.root
        while curr != self.NIL:
            self.comparisons += 1
            if key == curr.key:
                curr.value = value
                return
            elif key < curr.key:
                curr = curr.left
            else:
                curr = curr.right

        # Create new red node with sentinel children
        new_node = RBNode(
            key=key,
            value=value,
            color=Color.RED,
            left=self.NIL,
            right=self.NIL,
            parent=self.NIL,
        )

        parent = self.NIL
        x = self.root
        while x != self.NIL:
            parent = x
            self.comparisons += 1
            if new_node.key < x.key:
                x = x.left
            else:
                x = x.right

        new_node.parent = parent
        if parent == self.NIL:
            self.root = new_node
        elif new_node.key < parent.key:
            parent.left = new_node
        else:
            parent.right = new_node

        self._size += 1
        self._insert_fixup(new_node)

    def _insert_fixup(self, z: RBNode) -> None:
        """Restore Red-Black invariants following insertion via rotations and recoloring."""
        while z.parent.color == Color.RED:
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right  # Uncle
                if y.color == Color.RED:
                    # Case 1: Uncle is red -> Recolor parent, uncle, and grandparent
                    z.parent.color = Color.BLACK
                    y.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    self.recolorings += 3
                    z = z.parent.parent
                else:
                    # Case 2: Uncle is black and z is right child -> Left rotate to form line
                    if z == z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    # Case 3: Uncle is black and z is left child -> Right rotate grandparent
                    z.parent.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    self.recolorings += 2
                    self._right_rotate(z.parent.parent)
            else:
                # Symmetric case: z.parent is right child of grandparent
                y = z.parent.parent.left  # Uncle
                if y.color == Color.RED:
                    z.parent.color = Color.BLACK
                    y.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    self.recolorings += 3
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    self.recolorings += 2
                    self._left_rotate(z.parent.parent)

        if self.root.color != Color.BLACK:
            self.root.color = Color.BLACK
            self.recolorings += 1

    def _left_rotate(self, x: RBNode) -> None:
        """Perform Left Rotation around node x."""
        self.rotations += 1
        y = x.right
        x.right = y.left
        if y.left != self.NIL:
            y.left.parent = x

        y.parent = x.parent
        if x.parent == self.NIL:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        y.left = x
        x.parent = y

    def _right_rotate(self, y: RBNode) -> None:
        """Perform Right Rotation around node y."""
        self.rotations += 1
        x = y.left
        y.left = x.right
        if x.right != self.NIL:
            x.right.parent = y

        x.parent = y.parent
        if y.parent == self.NIL:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x

        x.right = y
        y.parent = x

    def validate_invariants(self) -> Tuple[bool, str]:
        """Validate all formal Red-Black Tree invariants.
        
        Returns:
            Tuple of (is_valid: bool, error_message: str).
        """
        if self.root == self.NIL:
            return True, "Empty tree is valid."

        # Invariant 2: Root must be black
        if self.root.color != Color.BLACK:
            return False, f"Root is not BLACK (got {self.root.color})."

        # Invariant 4 & 5 verification via recursive traversal
        def verify_node(node: RBNode) -> Tuple[bool, int, str]:
            if node == self.NIL:
                return True, 1, ""  # Sentinel leaves contribute 1 to black-height

            # Invariant 4: Red node cannot have red children
            if node.color == Color.RED:
                if node.left.color == Color.RED or node.right.color == Color.RED:
                    return False, 0, f"Red violation at node {node.key}: child is also RED."

            # BST Ordering Check
            if node.left != self.NIL and node.left.key >= node.key:
                return False, 0, f"BST violation: left child {node.left.key} >= parent {node.key}."
            if node.right != self.NIL and node.right.key <= node.key:
                return False, 0, f"BST violation: right child {node.right.key} <= parent {node.key}."

            left_valid, left_bh, left_err = verify_node(node.left)
            if not left_valid:
                return False, 0, left_err

            right_valid, right_bh, right_err = verify_node(node.right)
            if not right_valid:
                return False, 0, right_err

            # Invariant 5: Equal black-height along all descendant paths
            if left_bh != right_bh:
                return False, 0, (
                    f"Black-height violation at node {node.key}: "
                    f"left_bh={left_bh} != right_bh={right_bh}."
                )

            current_bh = left_bh + (1 if node.color == Color.BLACK else 0)
            return True, current_bh, ""

        valid, _, msg = verify_node(self.root)
        return valid, msg if not valid else "All Red-Black invariants hold."
