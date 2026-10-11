"""Performance profiling and telemetry tools for algorithm benchmarks."""

from __future__ import annotations

import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator


@dataclass
class ProfileMetrics:
    """Captured runtime and memory profiling metrics."""
    elapsed_time_ms: float = 0.0
    peak_memory_kb: float = 0.0
    current_memory_kb: float = 0.0


@contextmanager
def profile_execution() -> Generator[ProfileMetrics, None, None]:
    """Context manager for measuring execution time and peak memory consumption."""
    metrics = ProfileMetrics()
    tracemalloc.start()
    t_start = time.perf_counter()

    try:
        yield metrics
    finally:
        t_end = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        metrics.elapsed_time_ms = (t_end - t_start) * 1000.0
        metrics.current_memory_kb = current / 1024.0
        metrics.peak_memory_kb = peak / 1024.0
