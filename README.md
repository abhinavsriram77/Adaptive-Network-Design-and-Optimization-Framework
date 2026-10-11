# Assignment 4: Adaptive Network Design and Optimization Framework

**Course:** Design and Analysis of Algorithms (DAA)  
**Faculty:** Prof. Geeta Tripathi  
**Test Suite Status:** 42 / 42 Automated Unit Tests Passing (100%)

---

## Quickstart & How to Run

```bash
# 1. Run the Complete 6-Module End-to-End Assignment 4 Demonstration Pipeline
python main.py

# 2. Launch the Interactive Viva Console (Test custom |V|, Density D, Budget W, or Site Count N live)
python main.py --interactive

# 3. Run All 42 Automated Unit Tests
python -m pytest -v

# 4. Run Individual Experimental Benchmarks
python benchmarks/benchmark_mst.py
python benchmarks/benchmark_indexing.py
python benchmarks/benchmark_heaps.py
python benchmarks/benchmark_budgeting.py
python benchmarks/benchmark_tsp.py
```

---

## 1. The Real-World Scenario (Assignment 4)

A smart city or enterprise telecommunications provider operates a heterogeneous network consisting of **Data Centers**, **Regional Network Hubs**, and **IoT Gateways**. Because network conditions, traffic loads, hardware failures, and budgets change throughout the day, **a single fixed algorithm cannot optimally solve every operational challenge**.

Our framework solves **6 interconnected real-world network operations** inside one unified pipeline:
1. **Minimum-Cost Backbone Construction:** Connect all hubs, data centers, and gateways at minimum fiber installation cost without redundant loops.
2. **All-Pairs Communication Cost Analysis:** Compute the shortest communication latency between every pair of major network zones.
3. **Network-State Data Management:** Store and query high-speed live telemetry in RAM and historical state records on disk blocks.
4. **Fault & Maintenance Event Prioritization:** Triage active network alarms and dynamically escalate priority when cascading failures occur.
5. **Capital Upgrade Budgeting:** Allocate a limited financial budget across divisible bandwidth leases and indivisible hardware units to maximize network utility.
6. **Field Engineer Maintenance Tour (TSP):** Route a field engineer from a central depot through all damaged network sites and back to the depot at minimum travel cost.

---

## 2. Overall Architecture: How the Framework Works

Every request entering our framework passes through the **6-Stage DAA Decision Pipeline**:

```text
[1. SCENARIO INPUT]       --> Raw network topology, telemetry workload, fault stream, budget, or site list
        |
        v
[2. PROBLEM MODEL]        --> Formulates Entities, Mathematical Constraints, Objective Function & Input Size
        |
        v
[3. DAA CHOICE ENGINE]    --> Evaluates Runtime Conditions (Density D, Storage Tier, Escalation Ratio,
        |                     Asset Divisibility, Cluster Size N) to select the optimal syllabus technique
        v
[4. EXECUTION]            --> Runs the chosen algorithm/data structure and produces the exact solution
        |
        v
[5. PERFORMANCE ANALYSIS] --> Records execution time (ms), internal operation counts, and Time/Space bounds
        |
        v
[6. ADAPTATION]           --> Automatically switches algorithms when input conditions cross a threshold
```

---

## 3. Master Specification: Entities, Constraints, Conditions & Justifications

| Module | Real-World Entities & Input Parameters | Mathematical Constraints | Objective Function | Switching Condition & Threshold Used | Chosen DAA Algorithm & Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Backbone MST** | **Entities:** Hubs, Data Centers, Fiber Links<br>**Params:** Vertices `\|V\|`, Edges `\|E\|` | 1. Connected subgraph spanning all `\|V\|` nodes<br>2. Acyclic (`\|V\| - 1` edges)<br>3. Edge weights `w(e) >= 0` | `Minimize Sum(w(e))` for `e in T` | **Graph Density:**<br>`D = 2\|E\| / (\|V\|(\|V\|-1))`<br>**Threshold:** `D = 0.35` | **If `D < 0.35` (Sparse):** **Kruskal's** (`O(E log E)`), because sorting few edges + `O(α(V))` Disjoint-Set is fastest.<br>**If `D >= 0.35` (Dense):** **Prim's** (`O(V²)` / `O(E log V)`), avoiding `O(V² log V)` global edge sorting. |
| **2. All-Pairs Routing** | **Entities:** Network Zones, Transit Links<br>**Params:** Zones `\|V\|`, Latency Matrix `W[i][j]` | 1. Directed/Undirected weighted graph<br>2. No negative-weight cycles (`D[i][i] >= 0`) | `Minimize PathLatency(i -> j)` for **all** pairs `(i, j) in V × V` | **All-Pairs Requirement:**<br>Every pair `(i, j)` needed for planning & TSP | **Floyd-Warshall DP (`Θ(V³)` time, `Θ(V²)` space):** Computes all-pairs paths in a tight 3-nested matrix loop and detects negative cycles (`D[i][i] < 0`), unlike Dijkstra. |
| **3. State Data Management** | **Entities:** Telemetry Packets & Audit Logs<br>**Params:** Record count `N`, Block degree `t = 16` | 1. Keys must remain sorted for range queries<br>2. Balanced tree height `O(log N)` | Minimize lookup latency (RAM) or Disk Block I/O seeks (Disk) | **Storage Tier Profile:**<br>`VOLATILE_TELEMETRY` (RAM) vs.<br>`HISTORICAL_LOGS` (Disk) | **RAM Tier:** **Red-Black Tree** (`O(log₂ N)`), requiring `<= 2` rotations per insert.<br>**Disk Tier:** **Order-t B-Tree** (`O(log_t N)`), packing `2t-1` keys per disk block to cut disk I/O seeks. |
| **4. Event Prioritization** | **Entities:** Network Fault Alarms<br>**Params:** Active alarms `N`, Escalations `K` | 1. Min-Heap order (`Priority(parent) <= Priority(child)`)<br>2. Priority score `> 0` | Extract minimum priority score (highest urgency) & merge regional queues | **Escalation Ratio:**<br>`R = K / (N + K)`<br>**Threshold:** `R = 0.20` | **If `R < 0.20` (Steady):** **Binomial Heap** (`O(log N)` worst-case ops, low pointer overhead).<br>**If `R >= 0.20` (Storm):** **Fibonacci Heap** (`O(1)` amortized `decrease_key` and `union` via cascading cuts). |
| **5. Upgrade Budgeting** | **Entities:** Bandwidth Leases & Router Hardware<br>**Params:** Items `N`, Budget Cap `W` | 1. Total spend `Sum(w_i * x_i) <= W`<br>2. Item cost `w_i > 0`, utility `v_i >= 0` | `Maximize Sum(v_i * x_i)` | **Asset Divisibility:**<br>Continuous `x_i in [0, 1]` vs.<br>Discrete `x_i in {0, 1}` | **Divisible (`x_i in [0,1]`):** **Fractional Knapsack Greedy** (`O(N log N)` via `v_i / w_i` ratio).<br>**Indivisible (`x_i in {0,1}`):** **0/1 Knapsack DP** (`O(N * W)`), because greedy leaves unspent budget gaps on discrete hardware. |
| **6. Maintenance Tour (TSP)** | **Entities:** Regional Depot + Damaged Sites<br>**Params:** Sites `N`, Cost Matrix `C[i][j]` | 1. Start and end at Depot `v_0`<br>2. Visit every site `v_1..v_{N-1}` **exactly once** (Hamiltonian cycle) | `Minimize Sum C[π(i)][π(i+1)] + C[π(N-1)][π(0)]` | **Cluster Size `N`:**<br>Exact limit `N <= 14` | **Small `N <= 14`:** Compares **Exact DFS Backtracking** vs. **Exact Branch-and-Bound** (Reduced Cost Matrix LB prunes `>= 85%` of states).<br>**Large `N > 14`:** Switches to **Bounded Heuristic** due to NP-Hard `O((N-1)!)` explosion. |

---

## 4. Mandatory Complexity Classifications

1. **Optimization TSP vs. Decision TSP:**
   * **Optimization TSP** (*"Find the closed tour visiting all sites with minimum total cost"*) is **NP-Hard**.
   * **Decision TSP** (*"Does there exist a closed tour of total cost <= K?"*) is **NP-Complete** (verifiable in `O(V)` time and reducible from Hamiltonian Cycle).
2. **Why 0/1 Knapsack DP is Pseudo-Polynomial:**
   * The 0/1 Knapsack DP algorithm runs in `O(N * W)` time. Because the numeric budget value `W` requires `b = log₂(W)` bits to encode in binary, substituting `W = 2^b` yields `O(N * 2^b)`, which is **exponential in the input bit-length `b`** — hence **Pseudo-Polynomial**. Its decision version is **NP-Complete**, whereas Fractional Knapsack (`O(N log N)`) is strictly **Polynomial**.

---

## 5. Gaps in Classic DAA Algorithms That Enabled Modern Algorithms

| Classic Syllabus Algorithm | Identified Limitation / Gap | Modern Algorithm Developed to Solve It |
| :--- | :--- | :--- |
| **Prim's & Kruskal's MST** | Sequential single-thread bottleneck on billion-edge web graphs. | **Filter-Kruskal** & **Parallel Distributed Boruvka (MapReduce/Pregel)** |
| **Floyd-Warshall (`Θ(V³)`)** | Wastes cubic work when graphs are sparse (`E << V²`). | **Johnson's Algorithm (`O(V² log V + V*E)`)** & **Contraction Hierarchies** |
| **Order-t B-Tree** | Random block writes cause high SSD write amplification on heavy ingest. | **LSM-Trees (Log-Structured Merge Trees)** used in RocksDB & Apache Cassandra |
| **Fibonacci Heap** | 4 pointers per node cause poor CPU cache locality and high constant overhead. | **Pairing Heaps** & **Strict Brodal/Rank-Pairing Heaps** |
| **0/1 Knapsack DP (`O(N*W)`)** | Memory explodes when budget `W` is in billions of dollars with cent precision. | **FPTAS (Fully Polynomial-Time Approximation Scheme)** via value scaling |
| **Exact TSP B&B / Backtracking** | Exponential state explosion for `N > 25` cities. | **Christofides' 1.5-Approximation Algorithm** & **Lin-Kernighan-Helsgaun (LKH)** |

