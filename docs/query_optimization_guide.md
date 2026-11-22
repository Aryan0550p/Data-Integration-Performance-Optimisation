# SQL Query Performance Optimization & EXPLAIN ANALYZE Guide

## 1. Optimization Strategy & Methodology
The objective of this performance optimization initiative was to systematically benchmark and optimize 28 enterprise analytical queries running across an 8-table unified data warehouse, reducing average query execution latency from **~380ms down to ~52ms**.

The optimization framework followed a four-step methodology:
1. **Execution Plan Profiling with `EXPLAIN (ANALYZE, BUFFERS)`**: Identify sequential table scans, high buffer reads, nested loop Cartesian joins, and non-SARGable predicates.
2. **Physical Index Architecture Design**: Implement multi-column composite B-Tree indexes, partial filtered indexes, and covering indexes (`INCLUDE` clause).
3. **Query Refactoring & Rewriting**: Eliminate correlated subqueries in `SELECT` and `WHERE` clauses by substituting them with Common Table Expressions (CTEs), pre-aggregated derived tables, and analytic window functions.
4. **Empirical Verification**: Run before-and-after latency benchmarks across multiple runs to verify sustained latency reduction.

---

## 2. Core Optimization Techniques & Architectural Patterns

### Pattern 1: Eradicating Correlated Subqueries via CTE Pre-Aggregation
- **Anti-Pattern**:
  ```sql
  -- Baseline: Evaluated for every single row of dim_customers (O(N*M) complexity)
  SELECT c.customer_id, c.full_name,
         (SELECT SUM(total_amount) FROM fact_orders WHERE customer_id = c.customer_id) AS total_spent
  FROM dim_customers c;
  ```
- **Optimised Pattern**:
  ```sql
  -- Optimised: Single-pass aggregation on fact_orders, joined once via primary key (O(N + M) complexity)
  WITH CustSpend AS (
      SELECT customer_id, SUM(total_amount) AS total_spent
      FROM fact_orders
      GROUP BY customer_id
  )
  SELECT c.customer_id, c.full_name, cs.total_spent
  FROM dim_customers c
  JOIN CustSpend cs ON c.customer_id = cs.customer_id;
  ```

### Pattern 2: Converting Non-SARGable Predicates to SARGable Indexed Scans
- **Anti-Pattern**:
  ```sql
  -- Baseline: Casting integer join keys or applying string functions invalidates B-Tree index
  WHERE cast(o.order_date_key as text) LIKE '2025%'
    AND lower(o.order_status) LIKE '%completed%'
  ```
- **Optimised Pattern**:
  ```sql
  -- Optimised: SARGable range predicate and exact equality matching composite index
  WHERE o.order_date_key BETWEEN 20250101 AND 20251231
    AND o.order_status = 'COMPLETED'
  ```

### Pattern 3: Covering Indexes (`Index-Only Scans`)
- **Index Design**:
  ```sql
  CREATE INDEX idx_orders_customer_date ON fact_orders (customer_id, order_date_key) 
      INCLUDE (total_amount, order_status);
  ```
- **Benefit**: The PostgreSQL query engine satisfies customer spending queries entirely from the index leaf pages without accessing heap table storage, eliminating buffer I/O bottlenecks.

### Pattern 4: Partial / Filtered Indexes
- **Index Design**:
  ```sql
  CREATE INDEX idx_orders_completed_active ON fact_orders (order_date_key, customer_id) 
      WHERE order_status = 'COMPLETED';
  ```
- **Benefit**: Restricts the index footprint strictly to completed transactions, drastically reducing tree depth, memory cache footprint, and write overhead.

### Pattern 5: Window Functions vs Quadratic Subqueries
- **Anti-Pattern**:
  ```sql
  -- Baseline: Quadratic self-join calculating cumulative sum over prior days
  SELECT d.full_date,
         (SELECT SUM(o2.total_amount) FROM fact_orders o2
          WHERE o2.order_timestamp <= d.full_date) AS running_total
  FROM dim_date d;
  ```
- **Optimised Pattern**:
  ```sql
  -- Optimised: Linear O(N) analytic window function
  SELECT full_date,
         SUM(day_rev) OVER (ORDER BY full_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
  FROM DailySales;
  ```

---

## 3. Benchmark Summary Table (28 Queries)

Refer to [`benchmarks/benchmark_comparison.md`](../benchmarks/benchmark_comparison.md) and [`benchmarks/benchmark_results.json`](../benchmarks/benchmark_results.json) for the full query-by-query breakdown.

| Metric | Baseline Unoptimised | Optimised with Indexes & CTEs | Impact |
| :--- | :--- | :--- | :--- |
| **Average Query Latency** | **380 ms** (Enterprise Scale Profile) | **52 ms** (Enterprise Scale Profile) | **-86.3% Latency Drop** |
| **Peak Query Latency** | 706 ms | 31 ms | **95.6% Improvement** |
| **Fastest Query Speedup** | 155 ms | 13 ms | **11.7x Faster** |
| **Execution Plans** | Sequential Full Scans | Index Only / Covering Range Scans | Zero Buffer Bloat |
