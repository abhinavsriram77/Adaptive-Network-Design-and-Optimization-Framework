# DESIGN & ANALYSIS OF ALGORITHMS — PROJECT REPORT SUBMISSION FORM (EVIDENCE SHEET)

| Field | Details |
| :--- | :--- |
| **Assignment (1–6)** | **Assignment 4** — Adaptive Network Design and Optimization Framework |
| **Course / Section** | Design and Analysis of Algorithms (DAA) / **AI ML Leopards** |
| **Faculty** | **Professor Geeta Tripathi**, Professor of Practice, School of Technology |
| **Project / Framework Title** | **Adaptive Network Design and Optimization Framework** |
| **Code / Repository URL** | [https://github.com/abhinavsriram77/Adaptive-Network-Design-and-Optimization-Framework/tree/main](https://github.com/abhinavsriram77/Adaptive-Network-Design-and-Optimization-Framework/tree/main) |
| **Report / Demo Link** | [https://github.com/abhinavsriram77/Adaptive-Network-Design-and-Optimization-Framework/blob/main/main.py](https://github.com/abhinavsriram77/Adaptive-Network-Design-and-Optimization-Framework/blob/main/main.py) |

### Team Members & Roll Numbers
1. **M. Harshavardhan Reddy** (`25WU0102152`)
2. **M. Sai Manoj** (`25WU0102139`)
3. **Y. Abhinav Sri Ram** (`25WU0101158`)
4. **M. Manoj Sri Sathya Charan** (`25WU0102169`)
5. **K. Pranay** (`25WU0102328`)

---

## 1. PROBLEM ABSTRACTION & MODELLING (`LO1 · model real world scenarios`)

* **Scenario / Decision to Solve:**
  A city or enterprise network operator must interconnect **Data Centers**, **Regional Network Hubs**, and **IoT Gateways** while minimizing infrastructure cost, computing all-pairs communication latencies, indexing high-speed telemetry vs. archival state records, prioritizing dynamic fault alarms, allocating constrained upgrade budgets across divisible/indivisible assets, and routing field engineers through damaged sites. Because network density, storage tiers, fault rates, and site counts change dynamically, the framework automatically adapts its algorithm and data-structure selection at runtime.

* **Entities / Inputs & Size Parameter(s):**
  * **Graph Topology (`core/`):** Vertices $V$ (Hubs, Data Centers, IoT Gateways; size $|V|$) and weighted undirected/directed links $E$ (cost $w_e \ge 0$, latency $l_e \ge 0$, bandwidth $b_e$; size $|E|$, density $D = \frac{2|E|}{|V|(|V|-1)}$).
  * **State & Fault Records (`indexing/`, `prioritization/`):** Telemetry records $N_{\text{rec}}$, B-Tree block degree $t$, active fault alarms $N_{\text{inc}}$, and dynamic severity escalations $K_{\text{esc}}$.
  * **Upgrade & Dispatch Inputs (`budgeting/`, `dispatch/`):** Upgrade proposals $n$ with costs $w_i$, utilities $v_i$, budget capacity $W$; target maintenance sites $N_{\text{tsp}}$ with pairwise latency matrix $C[i][j]$.

* **Multi-Tier Objectives & Mathematical Constraints:**
  1. **Backbone MST:** $\min \sum_{e \in T} w(e)$ subject to $|T| = |V| - 1$ and acyclic full connectivity.
  2. **All-Pairs Routing:** $\min \text{Latency}(i \to j)\; \forall (i, j) \in V \times V$ subject to no negative-weight cycles ($D[i][i] \ge 0$).
  3. **Storage & Triage:** Maintain $\mathcal{O}(\log N)$ ordered key search ($t - 1 \le \text{keys} \le 2t - 1$ per disk block) and min-heap priority order ($\text{key}(\text{parent}) \le \text{key}(\text{child})$).
  4. **Upgrade Budgeting:** $\max \sum_{i=1}^n v_i x_i$ subject to $\sum_{i=1}^n w_i x_i \le W$, where $x_i \in [0, 1]$ (divisible bandwidth) or $x_i \in \{0, 1\}$ (indivisible router hardware).
  5. **Maintenance Tour (TSP):** $\min \sum_{i=0}^{N-2} C[\pi(i), \pi(i+1)] + C[\pi(N-1), \pi(0)]$ subject to visiting each damaged site exactly once and returning to depot $v_0$.

* **Representation:** `[x] graph` &nbsp; `[x] optimization` &nbsp; `[x] state/search` &nbsp; `[x] DP` &nbsp; `[x] data structure`

---

## 2. ALGORITHM CHOICE & FRAMEWORK DESIGN (`LO2 · choose & compare`)

* **Implemented DAA Syllabus Techniques & Alternatives Compared:**
  1. **Minimum Spanning Tree:** **Kruskal's Algorithm** (with Disjoint-Set Path Compression & Union by Rank) vs. **Prim's Algorithm** (Min-Heap & Dense Matrix).
  2. **All-Pairs Shortest Path:** **Floyd-Warshall Algorithm** (Dynamic Programming) compared against repeated single-source alternatives.
  3. **Searchable State Indexing:** **Red-Black Tree** (in-memory balanced BST) vs. **Order-$t$ B-Tree** (multi-way disk block tree).
  4. **Mergeable Event Prioritization:** **Binomial Heap** vs. **Fibonacci Heap** (lazy consolidation & cascading cuts).
  5. **Constrained Resource Allocation:** **Fractional Knapsack** (Greedy density sort) vs. **0/1 Knapsack** (Dynamic Programming).
  6. **Combinatorial Route Search (TSP):** **Exact DFS Backtracking** vs. **Exact Branch-and-Bound** (Reduced Cost Matrix lower bound).

* **Selection Reason / Runtime Decision Rules:**
  * **Rule 1 (Graph Density $D$):** Crossover observed empirically at $D \approx 0.31$ (configured threshold $D = 0.35$). If $D < 0.35$, select **Kruskal's** ($\mathcal{O}(E \log E)$ sorting on sparse edge sets); if $D \ge 0.35$, switch to **Prim's** ($\mathcal{O}(V^2)$ dense scan) to avoid sorting $\mathcal{O}(V^2)$ edges.
  * **Rule 2 (Memory vs. Disk Tier):** Volatile real-time telemetry routes to **Red-Black Tree** ($\le 2$ rotations/insert, zero disk I/O); historical archive logs route to **Order-$t$ B-Tree** ($t=16$, compressing height to $\mathcal{O}(\log_t N)$ to minimize disk block seeks).
  * **Rule 3 (Escalation Ratio $R_{\text{esc}} = \frac{K}{N+K}$):** If $R_{\text{esc}} < 0.20$, retain **Binomial Heap** ($\mathcal{O}(\log N)$ worst-case); if $R_{\text{esc}} \ge 0.20$, dynamically migrate live queue to **Fibonacci Heap** for $\mathcal{O}(1)$ amortized `decrease_key` and `union`.
  * **Rule 4 (Asset Divisibility):** Continuous bandwidth ($x_i \in [0, 1]$) selects **Greedy Fractional Knapsack**; discrete hardware ($x_i \in \{0, 1\}$) selects **0/1 Knapsack DP**.
  * **Rule 5 (TSP Cluster Scale $N$):** For $N \le 14$, executes **Exact Branch-and-Bound** (pruning $\ge 85\%$ of states over Backtracking); for $N > 14$, triggers NP-Hard scalability safeguard.

* **Workflow Architecture (`scenario → model → choose → execute → measure → explain`):**
  ```text
  [SCENARIO INPUT] --> [PROBLEM MODEL] --> [DAA SELECTOR ENGINE] --> [EXECUTION] --> [TELEMETRY & ANALYSIS] --> [ADAPTATION]
   Topology / Logs      Entities &          Checks D, Tier, R_esc,    Kruskal/Prim    Runtime (ms), Ops,         Switches live when
   Alarms / Budget      Constraints         Divisibility & Scale N    FW, RBT/BTree   Rotations, Block I/O,      input crosses
   Target Sites         Objectives          against thresholds        Heaps, DP, B&B  Pruned States              threshold
  ```

---

## 3. COMPLEXITY & CORRECTNESS (`LO3 · reason formally`)

| Major Technique / Operation | Expected Time $T(n)$ | Space $S(n)$ | Assumption / Formal Correctness Argument |
| :--- | :--- | :--- | :--- |
| **Kruskal's MST** (DSU Rank + Path Comp.) | $\mathcal{O}(\|E\| \log \|E\|)$ | $\mathcal{O}(\|V\| + \|E\|)$ | **Cut Property:** Greedily adding the lightest safe edge crossing any cut between disjoint components yields an exact MST. |
| **Prim's MST** (Min-Heap / Dense Matrix) | $\mathcal{O}(\|E\| \log \|V\|)$ / $\mathcal{O}(\|V\|^2)$ | $\mathcal{O}(\|V\| + \|E\|)$ | **Cut Property:** Growing a single tree from root $v_0$ via minimum-weight crossing edges is optimal for any non-negative connected graph. |
| **Floyd-Warshall All-Pairs Routing** | $\Theta(\|V\|^3)$ | $\Theta(\|V\|^2)$ | **Optimal Substructure:** $D^{(k)}[i][j] = \min(D^{(k-1)}[i][j], D^{(k-1)}[i][k] + D^{(k-1)}[k][j])$; requires no negative cycles ($D[i][i] \ge 0$). |
| **Red-Black Tree** (Search / Insert) | $\mathcal{O}(\log_2 N)$ | $\mathcal{O}(N)$ | **Black-Height Invariant:** No red-red parent-child and uniform black-height guarantee height $h \le 2\log_2(N+1)$ with $\le 2$ rotations/insert. |
| **Order-$t$ B-Tree** (Search / Split Insert) | $\mathcal{O}(t \log_t N)$ CPU / $\mathcal{O}(\log_t N)$ I/O | $\mathcal{O}(N)$ | **Multi-Way Balance:** Every non-root node holds $[t-1, 2t-1]$ keys; proactive downward splitting keeps all leaves at identical depth. |
| **Binomial vs. Fibonacci Heap** (`decrease_key`) | $\mathcal{O}(\log N)$ vs. $\mathcal{O}(1)$ amort. | $\mathcal{O}(N)$ | **Potential Method:** Marking nodes and cascading cuts bound amortized `decrease_key` and `union` to $\mathcal{O}(1)$ and `extract_min` to $\mathcal{O}(\log N)$. |
| **Fractional Knapsack** (Greedy Sort) | $\mathcal{O}(n \log n)$ | $\mathcal{O}(n)$ | **Greedy Exchange Proof:** Selecting continuous slices in descending order of utility density $v_i / w_i$ leaves no улучшитьable swap. |
| **0/1 Knapsack** (Dynamic Programming) | $\mathcal{O}(n \cdot W)$ *(Pseudo-Poly)* | $\mathcal{O}(n \cdot W)$ | **Bellman Recurrence:** $DP[i][w] = \max(DP[i-1][w], v_i + DP[i-1][w-w_i])$ exhaustively evaluates optimal inclusion/exclusion states. |
| **TSP Backtracking vs. Branch-and-Bound** | $\mathcal{O}((N-1)!)$ worst-case | $\mathcal{O}(N^2)$ per state | **Admissible Lower Bound:** Row/column matrix reductions satisfy $LB(\text{node}) \le \text{OPT}(\text{subtree})$, ensuring zero optimal tours are pruned when $LB \ge UB$. |

* **Complexity Status:** `[x] polynomial` &nbsp; `[x] pseudo-polynomial` &nbsp; `[x] NP-Hard optimization` &nbsp; `[x] NP-Complete decision`

---

## 4. IMPLEMENTATION & VALIDATION (`LO4 · build & verify`)

* **Language / Tools & Implemented Modules:**
  Python 3.13, `pytest`, modular architecture across [`core/`](file:///c:/desktop/DAA%20PROJECT/core/), [`algorithms/mst/`](file:///c:/desktop/DAA%20PROJECT/algorithms/mst/), [`algorithms/routing/`](file:///c:/desktop/DAA%20PROJECT/algorithms/routing/), [`indexing/`](file:///c:/desktop/DAA%20PROJECT/indexing/), [`prioritization/`](file:///c:/desktop/DAA%20PROJECT/prioritization/), [`budgeting/`](file:///c:/desktop/DAA%20PROJECT/budgeting/), [`dispatch/`](file:///c:/desktop/DAA%20PROJECT/dispatch/), [`benchmarks/`](file:///c:/desktop/DAA%20PROJECT/benchmarks/), and unified pipeline [`main.py`](file:///c:/desktop/DAA%20PROJECT/main.py).
* **Correctness Tests:** `[x] normal` &nbsp; `[x] boundary` &nbsp; `[x] large` &nbsp; `[x] difficult`
* **Tests Passed:** **28 / 28 Core Milestone Tests Passed** (**42 / 42 Total Extended Suite Passed** in `0.38s` via `python -m pytest -v`) — covering single/disconnected graphs, negative-cycle detection (`NegativeCycleError`), sequential/random Red-Black & B-Tree invariants, cascading cuts, 0/1 greedy counterexamples, and B&B verification against brute-force permutations.

---

## 5. EXPERIMENTS & ADAPTATION (`LO5 · measure & adapt`)

| Input / Condition | Size $n$ | Selected Algorithm / Structure | Runtime / Ops / Memory | Result / Empirical Observation |
| :--- | :--- | :--- | :--- | :--- |
| **1A. Baseline (Sparse Network)** | $\|V\|=25, \|E\|=36$ ($D=0.12$) | **Kruskal's MST (DSU)** | `0.23 ms` / `258 ops` | Optimal MST cost `420.40`; sparse edge sorting is minimal. |
| **1B. Changed (Dense Mesh)** | $\|V\|=25, \|E\|=240$ ($D=0.80$) | **Prim's Dense Matrix MST** | `0.31 ms` / `1,250 ops` | Crossover observed at $D \approx 0.31$; avoids sorting $240$ edges. |
| **2A. Baseline (RAM Telemetry)** | $N = 500$ live records | **Red-Black Tree (RAM)** | `485 rotations` / `0 Disk I/O` | Sub-microsecond in-memory inserts ($\le 2$ rotations/insert). |
| **2B. Changed (Disk Archive)** | $N = 500$ block logs ($t=16$) | **Order-16 B-Tree (Disk)** | `30 splits` / `591 Block I/O` | Tree height compressed to $2$ levels, minimizing disk seeks. |
| **3A. Baseline (Steady Alarms)** | $N=50, K=2$ ($R_{\text{esc}}=0.038$) | **Binomial Heap** | `50 comparisons` | Deterministic $\mathcal{O}(\log N)$ queueing with low pointer overhead. |
| **3B. Changed (Outage Storm)** | $N=50, K=26$ ($R_{\text{esc}}=0.342$) | **Fibonacci Heap** | $\mathcal{O}(1)$ amort. `decrease_key` | Auto-migrated at $R_{\text{esc}} \ge 0.20$; instant priority escalation. |
| **4A. Baseline (Divisible BW)** | $n=3, W=\$100\text{k}$ ($x_i \in [0,1]$) | **Fractional Knapsack (Greedy)** | `0.02 ms` / `3 sort ops` | Achieved `540.0` utility ($100\%$ budget utilization). |
| **4B. Changed (Discrete HW)** | $n=4, W=\$100\text{k}$ ($x_i \in \{0,1\}$) | **0/1 Knapsack (DP)** | `0.18 ms` / `404 DP states` | Achieved `370.0` exact discrete utility without greedy waste. |
| **5A. Baseline (TSP Unpruned)** | $N = 8$ sites (from FW matrix) | **Exact DFS Backtracking** | `7.27 ms` / `6,171 states` | Optimal tour `451.30 ms`, but explores thousands of paths. |
| **5B. Changed (TSP Pruned B&B)** | $N = 8$ sites (from FW matrix) | **Exact Branch-and-Bound** | `4.52 ms` / **`45 states`** (`139 pruned`) | Identical `451.30 ms` optimal tour with **$99.2\%$ fewer states**! |

* **Decision / Behaviour Changed Because:** Crossing mathematical thresholds (Edge Density $D \ge 0.31\text{--}0.35$, Disk Block persistence, Escalation Ratio $R_{\text{esc}} \ge 0.20$, Discrete $x_i \in \{0, 1\}$ constraint, and NP-Hard cluster limit $N > 14$) shifts the dominant asymptotic bottleneck, triggering automatic algorithm switching in [`main.py`](file:///c:/desktop/DAA%20PROJECT/main.py).

---

## 6. EXPLANATION, LIMITS & DEMONSTRATION (`LO5 · interpret & communicate`)

* **Main Finding & One Scalability Concern:**
  No single algorithm dominates across all network operating regimes: Kruskal excels on sparse topologies ($D < 0.31$), Prim dominates dense meshes, Fibonacci Heaps absorb escalation storms, and Reduced-Matrix Branch-and-Bound reduces TSP state exploration by $>98\%$ over Backtracking. **Primary Limitation:** Floyd-Warshall requires rigid $\Theta(|V|^3)$ time even on sparse graphs, and 0/1 Knapsack DP memory $\mathcal{O}(n \cdot W)$ scales linearly with numeric budget magnitude $W$.
* **Theory vs. Observation & Gaps Enabling Modern Algorithms:**
  Measured operation counts match theoretical bounds (Floyd-Warshall comparisons scaled cubically: $10^3 = 1,000 \to 20^3 = 8,000 \to 30^3 = 27,000$). However, Fibonacci Heaps exhibit higher constant pointer overhead on small inputs, which inspired **Pairing Heaps**; Floyd-Warshall's sparse overhead inspired **Johnson's Algorithm** ($\mathcal{O}(V^2 \log V + VE)$); and B-Tree random write amplification on SSDs inspired **LSM-Trees**.
* **NP-Hard / NP-Complete & Pseudo-Polynomial Implications:**
  * **Optimization TSP** (*"Find the minimum-cost tour visiting all sites"*) is **NP-Hard**, whereas **Decision TSP** (*"Does a tour of cost $\le K$ exist?"*) is **NP-Complete** (verifiable in $\mathcal{O}(V)$ time and reducible from Hamiltonian Cycle). Because exact search grows as $\mathcal{O}((N-1)!)$ ($21! \approx 5.1 \times 10^{19}$ for $N=22$), exact B&B is restricted to $N \le 14\text{--}18$ before handing off to polynomial heuristics.
  * **0/1 Knapsack DP** runs in $\mathcal{O}(n \cdot W)$ **Pseudo-Polynomial** time because numeric capacity $W$ requires $b = \log_2 W$ bits to encode, making $\mathcal{O}(n \cdot 2^b)$ exponential in bit-length $b$; its decision form is **NP-Complete**, while **Fractional Knapsack** ($\mathcal{O}(n \log n)$) is strictly **Polynomial**.

---

### SUBMISSION CHECKLIST
`[x] integrated framework` &nbsp; `[x] working code` &nbsp; `[x] alternative compared` &nbsp; `[x] time/space analysis` &nbsp; `[x] 4 test families` &nbsp; `[x] adapted decision` &nbsp; `[x] report + demo`
