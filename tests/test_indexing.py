"""Unit tests for Red-Black Tree, B-Tree, and the Adaptive Index Selector."""

import random
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from indexing.b_tree import BTree
from indexing.base import TelemetryRecord, WorkloadType
from indexing.red_black_tree import Color, RedBlackTree
from indexing.selector import AdaptiveIndexSelector


def test_red_black_tree_invariants_sequential_and_random():
    rbt = RedBlackTree()

    # 1. Sequential insertions (worst-case for unbalanced BST, O(log n) for RBT)
    for i in range(1, 101):
        rbt.insert(i, f"payload_{i}")
        assert len(rbt) == i

    valid, msg = rbt.validate_invariants()
    assert valid is True, msg
    assert rbt.root.color == Color.BLACK
    assert rbt.rotations > 0
    assert rbt.recolorings > 0

    # 2. Random insertions
    rng = random.Random(42)
    random_keys = list(range(200, 600))
    rng.shuffle(random_keys)

    for k in random_keys:
        rbt.insert(k, f"random_payload_{k}")

    valid, msg = rbt.validate_invariants()
    assert valid is True, msg
    assert len(rbt) == 100 + len(random_keys)

    # 3. Search verification
    for i in range(1, 101):
        assert rbt.search(i) == f"payload_{i}"
    assert rbt.search(99999) is None

    # 4. In-place update
    rbt.insert(50, "updated_50")
    assert rbt.search(50) == "updated_50"
    valid, msg = rbt.validate_invariants()
    assert valid is True, msg


def test_b_tree_structural_invariants_and_io_tracking():
    # Test for both t=2 (2-3-4 tree) and t=3
    for degree in [2, 3]:
        btree = BTree(t=degree)

        keys = list(range(1, 121))
        random.Random(123).shuffle(keys)

        for k in keys:
            btree.insert(k, f"block_data_{k}")

        assert len(btree) == 120
        valid, msg = btree.validate_invariants()
        assert valid is True, f"Degree {degree} invariant failure: {msg}"

        # Verify disk I/O metrics were recorded
        assert btree.disk_writes > 0
        assert btree.splits > 0

        # Query verification
        reads_before = btree.disk_reads
        for k in keys[:20]:
            val = btree.search(k)
            assert val == f"block_data_{k}"
        assert btree.disk_reads > reads_before
        assert btree.search(99999) is None


def test_adaptive_indexing_selector_workload_routing():
    selector = AdaptiveIndexSelector(btree_order=3)

    # 1. Volatile In-Memory Ingestion
    rec_volatile = TelemetryRecord(
        node_id="gateway_01",
        metric_name="duty_cycle",
        value=98.5,
        timestamp_ns=1000000,
    )
    res_vol = selector.store_telemetry(rec_volatile, workload=WorkloadType.VOLATILE_TELEMETRY)
    assert "Red-Black Tree" in res_vol["target_tier"]

    # 2. Historical Archival Ingestion
    rec_historical = TelemetryRecord(
        node_id="hub_01",
        metric_name="ingress_bandwidth",
        value=450.2,
        timestamp_ns=2000000,
    )
    res_hist = selector.store_telemetry(rec_historical, workload=WorkloadType.HISTORICAL_LOGS)
    assert "B-Tree" in res_hist["target_tier"]
    assert "simulated_disk_writes" in res_hist

    # 3. Hierarchical Tier Lookups
    # Hit L1 RAM
    val_l1, tier_l1, _ = selector.query_telemetry(rec_volatile.composite_key)
    assert val_l1 is not None
    assert "L1" in tier_l1

    # Miss L1, Hit L2 Disk
    val_l2, tier_l2, metrics_l2 = selector.query_telemetry(rec_historical.composite_key)
    assert val_l2 is not None
    assert "L2 Block" in tier_l2
    assert "simulated_disk_reads" in metrics_l2

    # 4. Archival Migration from RAM to Disk
    migrated = selector.archive_volatile_to_persistent(rec_volatile.composite_key)
    assert migrated is True
    # Verify now present in L2
    val_migrated = selector.btree.search(rec_volatile.composite_key)
    assert val_migrated is not None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
