"""Unit tests for Binomial Heap, Fibonacci Heap, and the Adaptive Triage Selector."""

import random
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from prioritization.binomial_heap import BinomialHeap
from prioritization.fibonacci_heap import FibonacciHeap
from prioritization.incident import IncidentSeverity, IncidentType, NetworkIncident
from prioritization.selector import AdaptiveTriageSelector


def test_incident_model_and_escalation():
    inc = NetworkIncident(
        id="INC-001",
        node_id="hub-01",
        incident_type=IncidentType.LINK_FAILURE,
        severity=IncidentSeverity.MEDIUM,
        priority_score=3.0,
        description="Fiber link degradation",
    )
    assert inc.id == "INC-001"
    assert inc.priority_score == 3.0
    assert inc.escalation_level == 0

    # Escalate by reducing score
    inc.escalate(1.2)
    assert inc.priority_score == 1.8
    assert inc.escalation_level == 1
    assert inc.severity == IncidentSeverity.HIGH

    inc.escalate(0.5)
    assert inc.priority_score == 1.3
    assert inc.severity == IncidentSeverity.CRITICAL


def test_binomial_heap_invariants_and_operations():
    heap = BinomialHeap()
    assert heap.is_empty() is True
    assert len(heap) == 0

    # Insert 40 random keys
    rng = random.Random(42)
    keys = [round(rng.uniform(1.0, 50.0), 2) for _ in range(40)]
    node_map = {}

    for k in keys:
        node = heap.insert(k, f"val_{k}")
        node_map[k] = node

    assert len(heap) == 40
    valid, msg = heap.validate_invariants()
    assert valid is True, msg

    # Verify find_min
    min_k, min_v = heap.find_min()
    assert min_k == min(keys)

    # Test decrease_key on a known node
    max_k = max(keys)
    max_node = node_map[max_k]
    heap.decrease_key(max_node, 0.5)
    valid, msg = heap.validate_invariants()
    assert valid is True, msg
    assert heap.find_min()[0] == 0.5

    # Extract all elements and verify monotonic order
    extracted = []
    while not heap.is_empty():
        extracted.append(heap.extract_min()[0])
        valid, msg = heap.validate_invariants()
        assert valid is True, msg

    assert len(extracted) == 40
    assert extracted == sorted(extracted)


def test_binomial_heap_union():
    h1 = BinomialHeap()
    h2 = BinomialHeap()

    for k in [10, 20, 30, 40]:
        h1.insert(k, k)
    for k in [5, 15, 25, 35]:
        h2.insert(k, k)

    h1.union(h2)
    assert len(h1) == 8
    assert len(h2) == 0
    valid, msg = h1.validate_invariants()
    assert valid is True, msg
    assert h1.find_min()[0] == 5


def test_fibonacci_heap_invariants_and_cascading_cuts():
    heap = FibonacciHeap()
    assert heap.is_empty() is True
    assert len(heap) == 0

    # Insert 50 random keys
    rng = random.Random(101)
    keys = [round(rng.uniform(2.0, 100.0), 2) for _ in range(50)]
    node_map = {}

    for k in keys:
        node = heap.insert(k, f"fib_{k}")
        node_map[k] = node

    assert len(heap) == 50
    valid, msg = heap.validate_invariants()
    assert valid is True, msg
    assert heap.find_min()[0] == min(keys)

    # Trigger consolidation by extracting min
    extracted_min = heap.extract_min()
    assert extracted_min[0] == min(keys)
    assert len(heap) == 49
    valid, msg = heap.validate_invariants()
    assert valid is True, msg

    # Test decrease_key triggering cut / cascading cut
    some_key = keys[15]
    some_node = node_map[some_key]
    heap.decrease_key(some_node, 1.0)
    valid, msg = heap.validate_invariants()
    assert valid is True, msg
    assert heap.find_min()[0] == 1.0

    # Extract all remaining elements and verify monotonic order
    extracted = []
    while not heap.is_empty():
        extracted.append(heap.extract_min()[0])
        valid, msg = heap.validate_invariants()
        assert valid is True, msg

    assert len(extracted) == 49
    assert extracted[0] == 1.0
    assert extracted == sorted(extracted)


def test_fibonacci_heap_union():
    h1 = FibonacciHeap()
    h2 = FibonacciHeap()

    for k in [12, 24, 36]:
        h1.insert(k, k)
    for k in [6, 18, 30]:
        h2.insert(k, k)

    h1.union(h2)
    assert len(h1) == 6
    assert len(h2) == 0
    valid, msg = h1.validate_invariants()
    assert valid is True, msg
    assert h1.find_min()[0] == 6


def test_adaptive_triage_selector_routing_and_escalation():
    # Start with default Binomial Heap
    selector = AdaptiveTriageSelector(escalation_threshold=0.25, initial_queue_type="binomial")
    assert "Binomial Heap" in selector.current_algorithm

    incidents = []
    for i in range(15):
        inc = NetworkIncident(
            id=f"INC-{i:03d}",
            node_id=f"node_{i}",
            incident_type=IncidentType.CONGESTION,
            priority_score=round(10.0 + i, 1),
        )
        selector.ingest_incident(inc)
        incidents.append(inc)

    assert len(selector.queue) == 15

    # Low escalations: remains Binomial Heap
    selector.escalate_incident("INC-005", 1.0)
    assert "Binomial Heap" in selector.current_algorithm

    # Multiple escalations surpassing 25% threshold -> triggers dynamic migration to Fibonacci Heap
    for i in range(6):
        selector.escalate_incident(f"INC-{i:03d}", 2.0)

    # Should have adapted to Fibonacci Heap
    assert "Fibonacci Heap" in selector.current_algorithm

    # Verify highest priority dispatch
    dispatched = selector.dispatch_highest_priority()
    assert dispatched is not None
    assert dispatched.priority_score <= selector.peek_highest_priority().priority_score


def test_adaptive_triage_selector_regional_merge():
    reg1 = AdaptiveTriageSelector(initial_queue_type="binomial")
    reg2 = AdaptiveTriageSelector(initial_queue_type="binomial")

    reg1.ingest_incident(NetworkIncident(id="R1-1", node_id="A", incident_type=IncidentType.POWER_OUTAGE, priority_score=4.0))
    reg1.ingest_incident(NetworkIncident(id="R1-2", node_id="B", incident_type=IncidentType.LINK_FAILURE, priority_score=2.0))

    reg2.ingest_incident(NetworkIncident(id="R2-1", node_id="C", incident_type=IncidentType.HARDWARE_FAULT, priority_score=1.5))
    reg2.ingest_incident(NetworkIncident(id="R2-2", node_id="D", incident_type=IncidentType.CONGESTION, priority_score=3.5))

    reg1.merge_regional_queue(reg2)
    assert len(reg1.queue) == 4
    assert len(reg2.queue) == 0

    first = reg1.dispatch_highest_priority()
    assert first.id == "R2-1"
    assert first.priority_score == 1.5


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
