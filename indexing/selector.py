"""Adaptive Dual-Tier Indexing Selector.

Intelligently routes node telemetry lookups and ingestion between the in-memory
Red-Black Tree (volatile, ultra-low latency) and the disk-backed B-Tree (persistent blocks).
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

from indexing.b_tree import BTree
from indexing.base import TelemetryRecord, WorkloadType
from indexing.red_black_tree import RedBlackTree


class AdaptiveIndexSelector:
    """Multi-tier indexing orchestrator dispatching operations based on workload profile.
    
    Attributes:
        rbt: In-memory Red-Black Tree for volatile real-time records.
        btree: Disk-backed B-Tree for durable block persistence.
    """

    def __init__(self, btree_order: int = 3) -> None:
        self.rbt = RedBlackTree()
        self.btree = BTree(t=btree_order)

        self.rbt_queries = 0
        self.btree_queries = 0
        self.cache_hits_rbt = 0
        self.cache_hits_btree = 0

    def store_telemetry(
        self,
        record: TelemetryRecord,
        workload: WorkloadType = WorkloadType.VOLATILE_TELEMETRY,
    ) -> Dict[str, Any]:
        """Store a telemetry observation into the appropriate storage tier.
        
        Args:
            record: TelemetryRecord instance.
            workload: WorkloadType determining memory vs. disk placement.
            
        Returns:
            Dict containing telemetry profiling metrics of the operation.
        """
        t0 = time.perf_counter()
        key = record.composite_key
        payload = record.to_dict()

        if workload == WorkloadType.VOLATILE_TELEMETRY:
            rotations_before = self.rbt.rotations
            self.rbt.insert(key, payload)
            elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

            return {
                "target_tier": "Red-Black Tree (In-Memory)",
                "workload": workload.value,
                "elapsed_microseconds": elapsed_us,
                "rotations_triggered": self.rbt.rotations - rotations_before,
            }
        else:
            writes_before = self.btree.disk_writes
            splits_before = self.btree.splits
            self.btree.insert(key, payload)
            elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

            return {
                "target_tier": "B-Tree (Disk-Backed Block Storage)",
                "workload": workload.value,
                "elapsed_microseconds": elapsed_us,
                "simulated_disk_writes": self.btree.disk_writes - writes_before,
                "node_splits": self.btree.splits - splits_before,
            }

    def query_telemetry(
        self,
        key: str,
        workload: Optional[WorkloadType] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str, Dict[str, Any]]:
        """Query a telemetry record across tiers.
        
        If workload is unspecified, queries the in-memory L1 tier first before
        falling back to the persistent L2 block tier.
        
        Args:
            key: Composite search key.
            workload: Optional explicit tier override.
            
        Returns:
            Tuple of (Result Payload or None, Dispatched Tier Name, Metrics Dict).
        """
        t0 = time.perf_counter()

        # Explicit volatile request
        if workload == WorkloadType.VOLATILE_TELEMETRY:
            self.rbt_queries += 1
            val = self.rbt.search(key)
            if val is not None:
                self.cache_hits_rbt += 1
            elapsed_us = (time.perf_counter() - t0) * 1_000_000.0
            return val, "Red-Black Tree (L1)", {"elapsed_microseconds": elapsed_us}

        # Explicit historical request
        if workload == WorkloadType.HISTORICAL_LOGS:
            self.btree_queries += 1
            reads_before = self.btree.disk_reads
            val = self.btree.search(key)
            if val is not None:
                self.cache_hits_btree += 1
            elapsed_us = (time.perf_counter() - t0) * 1_000_000.0
            return (
                val,
                "B-Tree (L2 Block)",
                {
                    "elapsed_microseconds": elapsed_us,
                    "simulated_disk_reads": self.btree.disk_reads - reads_before,
                },
            )

        # Tiered hierarchical lookup: L1 RAM -> L2 Block Disk
        self.rbt_queries += 1
        val = self.rbt.search(key)
        if val is not None:
            self.cache_hits_rbt += 1
            elapsed_us = (time.perf_counter() - t0) * 1_000_000.0
            return val, "Red-Black Tree (L1 Cache Hit)", {"elapsed_microseconds": elapsed_us}

        # L1 Miss -> Query L2 B-Tree
        self.btree_queries += 1
        reads_before = self.btree.disk_reads
        val = self.btree.search(key)
        if val is not None:
            self.cache_hits_btree += 1
        elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

        return (
            val,
            "B-Tree (L2 Block Access)",
            {
                "elapsed_microseconds": elapsed_us,
                "simulated_disk_reads": self.btree.disk_reads - reads_before,
            },
        )

    def archive_volatile_to_persistent(self, key: str) -> bool:
        """Migrate a volatile telemetry entry from RAM to persistent B-Tree storage."""
        record = self.rbt.search(key)
        if record is None:
            return False
        self.btree.insert(key, record)
        return True

    def get_tier_statistics(self) -> Dict[str, Any]:
        """Aggregate operational telemetry across both indexing tiers."""
        return {
            "rbt_in_memory_records": len(self.rbt),
            "btree_persistent_records": len(self.btree),
            "rbt_rotations_total": self.rbt.rotations,
            "rbt_recolorings_total": self.rbt.recolorings,
            "btree_disk_reads_total": self.btree.disk_reads,
            "btree_disk_writes_total": self.btree.disk_writes,
            "btree_splits_total": self.btree.splits,
            "rbt_queries": self.rbt_queries,
            "btree_queries": self.btree_queries,
            "cache_hits_rbt": self.cache_hits_rbt,
            "cache_hits_btree": self.cache_hits_btree,
        }
