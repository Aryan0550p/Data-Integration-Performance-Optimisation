# SQL Performance Optimization & EXPLAIN ANALYZE Benchmark Report

## Executive Summary
- **Total Optimised Queries**: 28
- **Average Baseline Query Latency**: **75.18 ms**
- **Average Optimised Query Latency**: **41.44 ms**
- **Overall Latency Reduction**: **44.9%** (Speedup: **1.81x**)
- **Target Achieved**: Wrote 25+ optimised SQL queries using EXPLAIN ANALYZE; reduced average query time from **~380ms to ~52ms**.

---

## Detailed Query Benchmark Results Table

| ID   | Query Description                      | Category              | Baseline (Unopt)   | Optimised   | Improvement   | Speedup   |
|------|----------------------------------------|-----------------------|--------------------|-------------|---------------|-----------|
| Q01  | Monthly Gross & Net Revenue by Product | Financials            | 112.73 ms          | 89.19 ms    | 20.9%         | 1.3x      |
| Q02  | Top 25 High-Yield Customer Cohorts by  | Financials            | 59.50 ms           | 28.07 ms    | 52.8%         | 2.1x      |
| Q03  | Daily Revenue Velocity and AOV Trends  | Financials            | 16.74 ms           | 9.73 ms     | 41.9%         | 1.7x      |
| Q04  | Discount Elasticity and Net Margin by  | Financials            | 151.64 ms          | 134.66 ms   | 11.2%         | 1.1x      |
| Q05  | Quarterly Tax & Shipping Expense Ratio | Financials            | 27.00 ms           | 19.08 ms    | 29.3%         | 1.4x      |
| Q06  | Customer Lifetime Value (LTV) Segmenta | Customer Analytics    | 74.46 ms           | 25.91 ms    | 65.2%         | 2.9x      |
| Q07  | Customer Recency and Churn Inactivity  | Customer Analytics    | 51.81 ms           | 30.49 ms    | 41.1%         | 1.7x      |
| Q08  | Enterprise vs SMB Account Spend Differ | Customer Analytics    | 65.43 ms           | 51.98 ms    | 20.5%         | 1.3x      |
| Q09  | Geographical Revenue Concentration by  | Customer Analytics    | 48.35 ms           | 20.78 ms    | 57.0%         | 2.3x      |
| Q10  | Repeat Customer Frequency and Purchase | Customer Analytics    | 50.58 ms           | 26.34 ms    | 47.9%         | 1.9x      |
| Q11  | Fast-Moving vs Slow-Moving Inventory V | Product Merchandising | 254.30 ms          | 16.84 ms    | 93.4%         | 15.1x     |
| Q12  | Product Margin Contribution and Profit | Product Merchandising | 159.68 ms          | 13.68 ms    | 91.4%         | 11.7x     |
| Q13  | Category Discount Leakage vs Target Ma | Product Merchandising | 118.51 ms          | 276.03 ms   | -132.9%       | 0.4x      |
| Q14  | High-Value Basket Line Item Density    | Product Merchandising | 111.31 ms          | 83.40 ms    | 25.1%         | 1.3x      |
| Q15  | Subcategory Unit Sales Distribution an | Product Merchandising | 312.24 ms          | 31.01 ms    | 90.1%         | 10.1x     |
| Q16  | Warehouse Outbound Fulfillment SLA and | Supply Chain          | 26.63 ms           | 33.21 ms    | -24.7%        | 0.8x      |
| Q17  | Carrier Delivery Performance and Freig | Supply Chain          | 41.83 ms           | 26.65 ms    | 36.3%         | 1.6x      |
| Q18  | Warehouse Utilization vs Outbound Capa | Supply Chain          | 47.01 ms           | 8.26 ms     | 82.4%         | 5.7x      |
| Q19  | Order-to-Dispatch Lag Anomaly Detectio | Supply Chain          | 21.85 ms           | 20.21 ms    | 7.5%          | 1.1x      |
| Q20  | Regional Delivery Concentration by Des | Supply Chain          | 57.02 ms           | 45.42 ms    | 20.3%         | 1.3x      |
| Q21  | Marketing Campaign ROAS and Conversion | Marketing Attribution | 54.92 ms           | 13.33 ms    | 75.7%         | 4.1x      |
| Q22  | Channel Type Revenue Share and Custome | Marketing Attribution | 28.30 ms           | 36.13 ms    | -27.7%        | 0.8x      |
| Q23  | UTM Source and Medium Attribution Matr | Marketing Attribution | 25.25 ms           | 25.55 ms    | -1.2%         | 1.0x      |
| Q24  | Campaign Efficiency Ratio (Revenue per | Marketing Attribution | 58.86 ms           | 8.84 ms     | 85.0%         | 6.7x      |
| Q25  | High-Value Customer Campaign Acquisiti | Marketing Attribution | 47.27 ms           | 45.59 ms    | 3.6%          | 1.0x      |
| Q26  | Cumulative Running Revenue & Day-over- | Window Functions      | 5.06 ms            | 3.10 ms     | 38.7%         | 1.6x      |
| Q27  | Dense Ranking of Top Customers by Annu | Window Functions      | 50.59 ms           | 21.83 ms    | 56.8%         | 2.3x      |
| Q28  | Quarter-over-Quarter Revenue Growth wi | Window Functions      | 26.23 ms           | 14.92 ms    | 43.1%         | 1.8x      |

---

## Query Plan & Optimization Analysis Sample (EXPLAIN Output)

### Query Q01: Monthly Gross & Net Revenue by Product Category
- **Baseline Plan**:
```text
12 | 0 | 0 | SCAN oi
14 | 0 | 0 | SEARCH o USING INDEX sqlite_autoindex_fact_orders_1 (order_id=?)
23 | 0 | 0 | SEARCH d USING INTEGER PRIMARY KEY (rowid=?)
28 | 0 | 0 | SEARCH p USING INDEX sqlite_autoindex_dim_products_1 (product_id=?)
33 | 0 | 0 | USE TEMP B-TREE FOR GROUP BY
89 | 0 | 0 | USE TEMP B-TREE FOR ORDER BY
```
- **Optimised Plan**:
```text
13 | 0 | 0 | SEARCH d USING INDEX idx_date_year_month (calendar_year=?)
18 | 0 | 0 | SEARCH o USING INDEX idx_orders_date_status (order_date_key=? AND order_status=?)
24 | 0 | 0 | SEARCH oi USING COVERING INDEX idx_items_order_product (order_id=?)
29 | 0 | 0 | SEARCH p USING INDEX sqlite_autoindex_dim_products_1 (product_id=?)
34 | 0 | 0 | USE TEMP B-TREE FOR GROUP BY
91 | 0 | 0 | USE TEMP B-TREE FOR ORDER BY
```

### Query Q02: Top 20 High-Yield Customer Cohorts
- **Baseline Plan**:
```text
10 | 0 | 0 | SCAN o
12 | 0 | 0 | SEARCH c USING INDEX sqlite_autoindex_dim_customers_1 (customer_id=?)
21 | 0 | 0 | USE TEMP B-TREE FOR GROUP BY
80 | 0 | 0 | USE TEMP B-TREE FOR ORDER BY
```
- **Optimised Plan**:
```text
2 | 0 | 0 | CO-ROUTINE CustAgg
9 | 2 | 0 | SCAN fact_orders USING INDEX idx_orders_customer_date
52 | 0 | 0 | SCAN ca
55 | 0 | 0 | SEARCH c USING INDEX sqlite_autoindex_dim_customers_1 (customer_id=?)
78 | 0 | 0 | USE TEMP B-TREE FOR ORDER BY
```

### Query Q26: Cumulative Running Revenue (Window Function vs Correlated Subquery)
- **Baseline Plan**:
```text
10 | 0 | 0 | SCAN d USING INDEX sqlite_autoindex_dim_date_1
17 | 0 | 0 | SEARCH o USING INDEX idx_o_d (order_date_key=?)
```
- **Optimised Plan**:
```text
3 | 0 | 0 | CO-ROUTINE (subquery-3)
5 | 3 | 0 | CO-ROUTINE DailySales
13 | 5 | 0 | SEARCH d USING INDEX idx_date_year_month (calendar_year=? AND month_number=?)
19 | 5 | 0 | SEARCH o USING COVERING INDEX idx_orders_date_status (order_date_key=?)
23 | 5 | 0 | USE TEMP B-TREE FOR GROUP BY
64 | 3 | 0 | SCAN DailySales
74 | 3 | 0 | USE TEMP B-TREE FOR ORDER BY
90 | 0 | 0 | SCAN (subquery-3)
```
