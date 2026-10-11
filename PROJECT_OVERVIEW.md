# ASSIGNMENT 4: ADAPTIVE NETWORK DESIGN AND OPTIMIZATION FRAMEWORK
## Complete Project Explanation: Scenario, Architecture, Conditions, Constraints & Algorithmic Working

---

## 1. The Real-World Scenario (From Assignment 4 PDF)

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

Every request entering our framework passes through the **6-Stage DAA Decision Pipeline** mandated by the handout:

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

### End-to-End Data Flow Between Modules
```text
+---------------------------------------------------------------------------------------------------+
|                                   CORE LAYER (core/)                                              |
|  Entities: Node (Data Center, Hub, IoT Gateway), NetworkEdge (Cost, Latency, Bandwidth), Graph    |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
         +----------------------------------------+----------------------------------------+
         |                                                                                 |
         v                                                                                 v
+----------------------------------------+                               +----------------------------------------+
| MODULE 1: MINIMUM-COST BACKBONE (MST)  |                               | MODULE 2: ALL-PAIRS ROUTING            |
| Condition: Graph Density D = 2E/V(V-1) |                               | Condition: Full Pairwise Matrix Needed |
| - If D < 0.35  --> Kruskal's (DSU)     |                               | - Runs Floyd-Warshall DP in Θ(V³)      |
| - If D >= 0.35 --> Prim's Algorithm    |                               | - Detects negative routing cycles      |
+----------------------------------------+                               +-----------------+----------------------+
                                                                                           |
                                                                 Feeds Pairwise Distances  |
                                                                 C[i][j] to TSP Dispatch   |
                                                                                           v
+----------------------------------------+     Feeds Damaged Sites       +----------------------------------------+
| MODULE 4: EVENT PRIORITIZATION         | ----------------------------> | MODULE 6 & 7: MAINTENANCE TOUR (TSP)   |
| Condition: Escalation Ratio R_esc      |                               | Condition: Cluster Size N (Sites)      |
| - If R_esc < 0.20  --> Binomial Heap   |                               | - Small N <= 14 --> Exact Backtracking |
| - If R_esc >= 0.20 --> Fibonacci Heap  |                               |   vs. Exact Branch-and-Bound (Reduced  |
+----------------------------------------+                               |   Cost Matrix Lower Bound)             |
                                                                         | - Large N > 14  --> Bounded Heuristic  |
+----------------------------------------+                               +----------------------------------------+
| MODULE 3: NETWORK-STATE INDEXING       |
| Condition: Storage Tier Workload       |                               +----------------------------------------+
| - Volatile RAM   --> Red-Black Tree    |                               | MODULE 5: UPGRADE BUDGETING            |
| - Disk Block I/O --> Order-t B-Tree    |                               | Condition: Asset Divisibility x_i      |
+----------------------------------------+                               | - Divisible x_i in [0,1] --> Greedy    |
                                                                         |   Fractional Knapsack                  |
                                                                         | - Discrete x_i in {0,1}  --> 0/1 DP    |
                                                                         +----------------------------------------+
```

---

## 3. Master Table: Conditions, Constraints, Objectives & Reasons

| Module | Real-World Entities & Input Parameters | Mathematical Constraints | Objective Function | Switching Condition & Threshold Used | Chosen DAA Algorithm & Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Backbone MST** | **Entities:** Hubs, Data Centers, Fiber Links<br>**Params:** Vertices `\|V\|`, Edges `\|E\|` | 1. Connected subgraph spanning all `\|V\|` nodes<br>2. Acyclic (`\|V\| - 1` edges)<br>3. Edge weights `w(e) >= 0` | `Minimize Sum(w(e))` for `e in T` | **Graph Density:**<br>`D = 2\|E\| / (\|V\|(\|V\|-1))`<br>**Threshold:** `D = 0.35` | **If `D < 0.35` (Sparse):** **Kruskal's** (`O(E log E)`), because sorting few edges + `O(α(V))` Disjoint-Set is fastest.<br>**If `D >= 0.35` (Dense):** **Prim's** (`O(V²)` / `O(E log V)`), avoiding `O(V² log V)` global edge sorting. |
| **2. All-Pairs Routing** | **Entities:** Network Zones, Transit Links<br>**Params:** Zones `\|V\|`, Latency Matrix `W[i][j]` | 1. Directed/Undirected weighted graph<br>2. No negative-weight cycles (`D[i][i] >= 0`) | `Minimize PathLatency(i -> j)` for **all** pairs `(i, j) in V × V` | **All-Pairs Requirement:**<br>Every pair `(i, j)` needed for planning & TSP | **Floyd-Warshall DP (`Θ(V³)` time, `Θ(V²)` space):** Computes all-pairs paths in a tight 3-nested matrix loop and detects negative cycles (`D[i][i] < 0`), unlike Dijkstra. |
| **3. State Data Management** | **Entities:** Telemetry Packets & Audit Logs<br>**Params:** Record count `N`, Block degree `t = 16` | 1. Keys must remain sorted for range queries<br>2. Balanced tree height `O(log N)` | Minimize lookup latency (RAM) or Disk Block I/O seeks (Disk) | **Storage Tier Profile:**<br>`VOLATILE_TELEMETRY` (RAM) vs.<br>`HISTORICAL_LOGS` (Disk) | **RAM Tier:** **Red-Black Tree** (`O(log₂ N)`), requiring `<= 2` rotations per insert.<br>**Disk Tier:** **Order-t B-Tree** (`O(log_t N)`), packing `2t-1` keys per disk block to cut disk I/O seeks. |
| **4. Event Prioritization** | **Entities:** Network Fault Alarms<br>**Params:** Active alarms `N`, Escalations `K` | 1. Min-Heap order (` Priority(parent) <= Priority(child)`)<br>2. Priority score `> 0` | Extract minimum priority score (highest urgency) & merge regional queues | **Escalation Ratio:**<br>`R = K / (N + K)`<br>**Threshold:** `R = 0.20` | **If `R < 0.20` (Steady):** **Binomial Heap** (`O(log N)` worst-case ops, low pointer overhead).<br>**If `R >= 0.20` (Storm):** **Fibonacci Heap** (`O(1)` amortized `decrease_key` and `union` via cascading cuts). |
| **5. Upgrade Budgeting** | **Entities:** Bandwidth Leases & Router Hardware<br>**Params:** Items `N`, Budget Cap `W` | 1. Total spend `Sum(w_i * x_i) <= W`<br>2. Item cost `w_i > 0`, utility `v_i >= 0` | `Maximize Sum(v_i * x_i)` | **Asset Divisibility:**<br>Continuous `x_i in [0, 1]` vs.<br>Discrete `x_i in {0, 1}` | **Divisible (`x_i in [0,1]`):** **Fractional Knapsack Greedy** (`O(N log N)` via `v_i / w_i` ratio).<br>**Indivisible (`x_i in {0,1}`):** **0/1 Knapsack DP** (`O(N * W)`), because greedy leaves unspent budget gaps on discrete hardware. |
| **6. Maintenance Tour (TSP)** | **Entities:** Regional Depot + Damaged Sites<br>**Params:** Sites `N`, Cost Matrix `C[i][j]` | 1. Start and end at Depot `v_0`<br>2. Visit every site `v_1..v_{N-1}` **exactly once** (Hamiltonian cycle) | `Minimize Sum C[π(i)][π(i+1)] + C[π(N-1)][π(0)]` | **Cluster Size `N`:**<br>Exact limit `N <= 14`<br>(or `<= 18` max) | **Small `N <= 14`:** Compares **Exact DFS Backtracking** vs. **Exact Branch-and-Bound** (Reduced Cost Matrix LB prunes `>= 85%` of states).<br>**Large `N > 14`:** Switches to **Bounded Heuristic** due to NP-Hard `O((N-1)!)` explosion. |

---

## 4. Step-by-Step Working of Each Algorithm in Our Scenario

### Module 1: Minimum-Cost Backbone (`algorithms/mst/`)
* **How Kruskal's Works (Sparse Network `D < 0.35`):**
  1. Sorts all `|E|` fiber links in non-decreasing order of construction cost `w(e)`.
  2. Initializes a **Disjoint-Set (Union-Find)** with **Path Compression** and **Union by Rank** where each hub is its own set.
  3. Iterates through sorted edges: if endpoints `(u, v)` belong to different sets (`find(u) != find(v)`), adds the link to the backbone and merges the sets (`union(u, v)`). Stops when `|V| - 1` links are selected.
* **How Prim's Works (Dense Network `D >= 0.35`):**
  1. Starts from a root Data Center node and maintains the minimum cost to connect each unvisited hub to the growing backbone tree.
  2. For dense graphs (`|V| >= 20`), uses an `O(|V|²)` adjacency scan (Prim Dense) instead of sorting `O(|V|²)` edges, adding the cheapest crossing link at each step until all `|V|` hubs are connected.

---

### Module 2: All-Pairs Cost Analysis (`algorithms/routing/floyd_warshall.py`)
* **How Floyd-Warshall Works:**
  1. Initializes an `|V| × |V|` distance matrix `D` where `D[i][i] = 0`, `D[i][j] = latency(i, j)` for direct fiber links, and `∞` otherwise, plus a `NextHop[i][j]` matrix for path reconstruction.
  2. Executes 3 nested loops over intermediate zone `k = 0..|V|-1`, source `i = 0..|V|-1`, and destination `j = 0..|V|-1`:
     `if D[i][k] + D[k][j] < D[i][j]: D[i][j] = D[i][k] + D[k][j]; NextHop[i][j] = NextHop[i][k]`
  3. Checks the diagonal `D[i][i] < 0` to detect any **negative-weight routing cycles**.

---

### Module 3: Network-State Data Management (`indexing/`)
* **How Red-Black Tree Works (In-Memory RAM Telemetry):**
  1. Maintains 5 Red-Black invariants (root is black, no two consecutive red nodes, equal black-height on all root-to-leaf paths).
  2. On every new telemetry packet insertion, performs standard BST insert followed by **Recoloring** and **at most 2 Rotations (Left/Right)**, guaranteeing `O(log₂ N)` worst-case time in RAM.
* **How Order-t B-Tree Works (Disk Block Archive):**
  1. Each node represents a physical disk block storing between `t - 1` and `2t - 1` sorted keys (`t = 16` -> up to 31 keys per block).
  2. During insertion, proactively **splits full child blocks (`2t - 1` keys)** on the way down in a single pass, keeping the tree wide and shallow (`height = O(log_t N)`) to minimize disk I/O reads and writes.

---

### Module 4: Fault Event Prioritization (`prioritization/`)
* **How Binomial Heap Works (Steady-State Faults):**
  1. Maintains a forest of heap-ordered Binomial Trees `B_k` (where `B_k` has `2^k` nodes and at most one tree of each degree exists, mirroring binary addition).
  2. Supports `insert`, `union`, `extract_min`, and `decrease_key` in worst-case `O(log N)` time.
* **How Fibonacci Heap Works (Alarm Escalation Storm):**
  1. Maintains a circular doubly-linked root list of trees without eager consolidation (`insert` and `union` take **`O(1)` actual time**).
  2. When an alarm escalates (`decrease_key`), if heap order is violated, it **cuts the node** from its parent, moves it to the root list in **`O(1)` amortized time**, and performs **Cascading Cuts** on ancestors that lose a second child.
  3. Tree consolidation into distinct degrees is deferred lazily until `extract_min()` (`O(log N)` amortized).

---

### Module 5: Upgrade Budgeting (`budgeting/`)
* **How Fractional Knapsack Works (Divisible Bandwidth Leases):**
  1. Computes the utility-to-cost density `r_i = v_i / w_i` for each bandwidth proposal.
  2. Sorts proposals in descending order of `r_i` (`O(N log N)`).
  3. Greedily funds whole items while budget remains, and takes an exact fractional slice `(remaining_budget / w_i)` of the boundary item to achieve 100% budget utilization.
* **How 0/1 Knapsack DP Works (Indivisible Router Hardware):**
  1. Constructs a Dynamic Programming table `DP[i][w]` for `i = 1..N` items and integer budget steps `w = 0..W`.
  2. Evaluates Bellman's optimality equation:
     `DP[i][w] = max(DP[i-1][w], v_i + DP[i-1][w - w_i])` if `w_i <= w`, else `DP[i-1][w]`.
  3. Backtracks from `DP[N][W]` to identify the exact subset of hardware units purchased.

---

### Modules 6 & 7: Maintenance Tour TSP & Complexity (`dispatch/`)
* **How Exact DFS Backtracking Works (`dispatch/backtracking.py`):**
  1. Explores permutations of unvisited sites starting from the Depot (`v_0`) via Depth-First Search.
  2. Tracks `current_cost` along the partial path; if `current_cost + C[u][v] >= best_cost`, it prunes that branch and backtracks.
* **How Exact Branch-and-Bound Works (`dispatch/branch_and_bound.py`):**
  1. **Initial Upper Bound (`UB`):** Runs Nearest Neighbor + 2-Opt in `< 1 ms` to get a strong starting `best_cost`.
  2. **Reduced Cost Matrix Lower Bound (`LB`):** Subtracting the minimum of each row and column yields an admissible lower bound `LB` representing the minimum possible cost to complete the tour.
  3. **Best-First Search & Pruning:** Expands the search node with the smallest `LB` first using a Min-Heap. Any branch with `LB >= best_cost` is immediately pruned, eliminating **85% to 98%** of the search space compared to Backtracking!
* **How NP-Hard Complexity & Scalability Are Handled:**
  * **Optimization TSP** (*"Find the minimum-cost tour"*) is **NP-Hard**, while **Decision TSP** (*"Is there a tour with cost <= K?"*) is **NP-Complete**.
  * **0/1 Knapsack DP** (`O(N * W)`) is **Pseudo-Polynomial** (polynomial in numeric value `W`, but exponential in input bit-length `log₂ W`), while its decision form is **NP-Complete**.
  * Because exact TSP search grows factorially as `O((N-1)!)`, when `N > 14` (e.g., 22 sites where `21! = 5.1 × 10^19`), the framework automatically transitions from exact search to bounded polynomial heuristics so the system never freezes.
