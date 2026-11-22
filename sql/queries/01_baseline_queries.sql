-- [Q01] Monthly Gross & Net Revenue by Product Category (Financials)
-- Baseline Note: Wildcard LIKE predicate on order status preventing index scan on orders.
SELECT p.category, d.calendar_year, d.month_name,
                   SUM(oi.line_total) AS total_gross,
                   AVG(oi.line_total) AS avg_item_rev
            FROM fact_orders o
            JOIN dim_date d ON o.order_date_key = d.date_key
            JOIN fact_order_items oi ON o.order_id = oi.order_id
            JOIN dim_products p ON oi.product_id = p.product_id
            WHERE d.calendar_year = 2025
              AND lower(o.order_status) LIKE '%completed%'
            GROUP BY p.category, d.calendar_year, d.month_name, d.month_number
            ORDER BY p.category, d.month_number;

-- [Q02] Top 25 High-Yield Customer Cohorts by Spend (Financials)
-- Baseline Note: Grouping on wide customer text columns before aggregate filtering.
SELECT c.customer_id, c.full_name, c.credit_limit,
                   SUM(o.total_amount) AS total_spent,
                   COUNT(o.order_id) AS total_orders
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE upper(c.country_code) LIKE '%US%'
            GROUP BY c.customer_id, c.full_name, c.credit_limit
            HAVING COUNT(o.order_id) >= 5
            ORDER BY total_spent DESC
            LIMIT 25;

-- [Q03] Daily Revenue Velocity and AOV Trends (Financials)
-- Baseline Note: Unindexed outer join with wildcard LIKE on order status.
SELECT d.full_date,
                   SUM(o.total_amount) AS daily_revenue,
                   AVG(o.total_amount) AS avg_order_value,
                   COUNT(o.order_id) AS order_volume
            FROM dim_date d
            LEFT JOIN fact_orders o ON d.date_key = o.order_date_key
            WHERE d.calendar_year = 2025 AND lower(o.order_status) LIKE '%completed%'
            GROUP BY d.full_date
            ORDER BY d.full_date;

-- [Q04] Discount Elasticity and Net Margin by Subcategory (Financials)
-- Baseline Note: Unindexed 3-table join with wildcard status pattern forcing nested scans.
SELECT p.subcategory,
                   AVG(oi.discount_rate) AS avg_discount,
                   SUM(oi.line_total) AS gross_sales,
                   SUM(oi.quantity * p.cost_price) AS total_cost
            FROM fact_order_items oi
            JOIN dim_products p ON oi.product_id = p.product_id
            JOIN fact_orders o ON oi.order_id = o.order_id
            WHERE p.is_active = 1 AND lower(o.order_status) LIKE '%completed%'
            GROUP BY p.subcategory
            HAVING SUM(oi.line_total) > 5000
            ORDER BY gross_sales DESC;

-- [Q05] Quarterly Tax & Shipping Expense Ratio Analysis (Financials)
-- Baseline Note: Wildcard LIKE status scan forcing sequential scan across all orders.
SELECT d.calendar_year, d.calendar_quarter,
                   SUM(o.tax_amount) AS total_tax,
                   SUM(o.shipping_amount) AS total_shipping,
                   SUM(o.total_amount) AS total_gross
            FROM fact_orders o
            JOIN dim_date d ON o.order_date_key = d.date_key
            WHERE lower(o.order_status) LIKE '%completed%'
            GROUP BY d.calendar_year, d.calendar_quarter
            ORDER BY d.calendar_year, d.calendar_quarter;

-- [Q06] Customer Lifetime Value (LTV) Segmentation (Customer Analytics)
-- Baseline Note: Grouping large unindexed outer join with customer metadata before aggregate filtering.
SELECT c.customer_id, c.full_name, c.state_code,
                   COUNT(o.order_id) AS total_orders,
                   SUM(o.total_amount) AS lifetime_value
            FROM dim_customers c
            LEFT JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE upper(c.country_code) LIKE '%US%'
            GROUP BY c.customer_id, c.full_name, c.state_code
            HAVING COUNT(o.order_id) >= 3
            ORDER BY lifetime_value DESC
            LIMIT 50;

-- [Q07] Customer Recency and Churn Inactivity Profile (Customer Analytics)
-- Baseline Note: Grouping across wide customer text columns during full table scan.
SELECT c.customer_id, c.full_name, c.email,
                   MAX(o.order_timestamp) AS last_order_time
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE o.order_timestamp < '2025-06-01'
            GROUP BY c.customer_id, c.full_name, c.email
            ORDER BY last_order_time ASC
            LIMIT 50;

-- [Q08] Enterprise vs SMB Account Spend Differential (Customer Analytics)
-- Baseline Note: Function upper() on country_code invalidating index use on customers.
SELECT c.is_enterprise,
                   COUNT(DISTINCT c.customer_id) AS total_accounts,
                   COUNT(o.order_id) AS total_orders,
                   AVG(o.total_amount) AS avg_ticket_size,
                   SUM(o.total_amount) AS total_gross_spend
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE upper(c.country_code) LIKE '%US%'
            GROUP BY c.is_enterprise;

-- [Q09] Geographical Revenue Concentration by State (Customer Analytics)
-- Baseline Note: Redundant IS NOT NULL scan over wide customer table; unindexed join.
SELECT c.state_code,
                   COUNT(DISTINCT c.customer_id) AS unique_buyers,
                   SUM(o.total_amount) AS state_revenue
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE c.state_code IS NOT NULL AND c.state_code <> 'UNKNOWN'
            GROUP BY c.state_code
            ORDER BY state_revenue DESC
            LIMIT 15;

-- [Q10] Repeat Customer Frequency and Purchase Velocity (Customer Analytics)
-- Baseline Note: Grouping wide customer columns during multi-table join.
SELECT c.customer_id, c.full_name,
                   COUNT(o.order_id) AS ord_count,
                   MIN(o.order_timestamp) AS first_ord,
                   MAX(o.order_timestamp) AS last_ord
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE o.order_date_key >= 20250101 AND o.order_date_key <= 20251231
            GROUP BY c.customer_id, c.full_name
            HAVING COUNT(o.order_id) > 6
            ORDER BY ord_count DESC
            LIMIT 25;

-- [Q11] Fast-Moving vs Slow-Moving Inventory Velocity by SKU (Product Merchandising)
-- Baseline Note: Grouping product metadata across 45k item rows in nested scan.
SELECT p.sku, p.product_name, p.category,
                   SUM(oi.quantity) AS total_units_sold,
                   SUM(oi.line_total) AS total_revenue
            FROM dim_products p
            JOIN fact_order_items oi ON p.product_id = oi.product_id
            WHERE p.is_active = 1
            GROUP BY p.sku, p.product_name, p.category
            ORDER BY total_units_sold DESC
            LIMIT 20;

-- [Q12] Product Margin Contribution and Profit Ratio (Product Merchandising)
-- Baseline Note: Redundant repeated multiplication across 45k item rows in comma-join syntax.
SELECT p.product_id, p.product_name, p.retail_price, p.cost_price,
                   SUM(oi.line_total) AS total_revenue,
                   SUM(oi.quantity * p.cost_price) AS total_cogs,
                   SUM(oi.line_total) - SUM(oi.quantity * p.cost_price) AS gross_profit
            FROM dim_products p, fact_order_items oi
            WHERE p.product_id = oi.product_id
            GROUP BY p.product_id, p.product_name, p.retail_price, p.cost_price
            HAVING SUM(oi.line_total) > 5000
            ORDER BY gross_profit DESC
            LIMIT 25;

-- [Q13] Category Discount Leakage vs Target Margin (Product Merchandising)
-- Baseline Note: String casting on numeric discount_rate in WHERE clause disabling B-Tree indexing.
SELECT p.category,
                   AVG(oi.discount_rate) AS mean_discount_rate,
                   SUM(oi.quantity * oi.unit_price * oi.discount_rate) AS total_discount_given
            FROM fact_order_items oi
            JOIN dim_products p ON oi.product_id = p.product_id
            WHERE cast(oi.discount_rate as text) <> '0.0'
            GROUP BY p.category
            ORDER BY total_discount_given DESC;

-- [Q14] High-Value Basket Line Item Density (Product Merchandising)
-- Baseline Note: Unindexed join with wildcard status pattern forcing nested scans.
SELECT oi.order_id,
                   COUNT(oi.product_id) AS distinct_items,
                   SUM(oi.line_total) AS basket_size
            FROM fact_order_items oi
            JOIN fact_orders o ON oi.order_id = o.order_id
            WHERE o.total_amount > 1500 AND lower(o.order_status) LIKE '%completed%'
            GROUP BY oi.order_id
            ORDER BY basket_size DESC
            LIMIT 30;

-- [Q15] Subcategory Unit Sales Distribution and Weight Profile (Product Merchandising)
-- Baseline Note: Sequential scan of products and unindexed fact_order_items join.
SELECT p.category, p.subcategory,
                   AVG(p.weight_kg) AS avg_weight,
                   SUM(oi.quantity) AS total_quantity_shipped
            FROM dim_products p
            LEFT JOIN fact_order_items oi ON p.product_id = oi.product_id
            GROUP BY p.category, p.subcategory
            ORDER BY total_quantity_shipped DESC;

-- [Q16] Warehouse Outbound Fulfillment SLA and Volume (Supply Chain)
-- Baseline Note: Non-SARGable LIKE pattern preventing index scan on shipment status.
SELECT w.warehouse_name, w.state_code,
                   COUNT(s.shipment_id) AS total_dispatched,
                   AVG(s.shipping_cost) AS avg_shipping_cost
            FROM dim_warehouses w
            JOIN fact_shipments s ON w.warehouse_id = s.warehouse_id
            WHERE s.shipping_status LIKE '%DELIVERED%'
            GROUP BY w.warehouse_name, w.state_code
            ORDER BY total_dispatched DESC;

-- [Q17] Carrier Delivery Performance and Freight Cost Breakdown (Supply Chain)
-- Baseline Note: Wildcard pattern on order status forcing full scan across orders.
SELECT s.carrier_code,
                   COUNT(s.shipment_id) AS shipment_count,
                   SUM(s.shipping_cost) AS total_freight_expenditure,
                   AVG(s.shipping_cost) AS mean_cost_per_shipment
            FROM fact_shipments s
            JOIN fact_orders o ON s.order_id = o.order_id
            WHERE lower(o.order_status) LIKE '%completed%'
            GROUP BY s.carrier_code
            ORDER BY total_freight_expenditure DESC;

-- [Q18] Warehouse Utilization vs Outbound Capacity Bottleneck (Supply Chain)
-- Baseline Note: Outer join scanning full shipments table during warehouse grouping.
SELECT w.warehouse_code, w.capacity_sqft,
                   COUNT(s.shipment_id) AS total_shipments
            FROM dim_warehouses w
            LEFT JOIN fact_shipments s ON w.warehouse_id = s.warehouse_id
            WHERE w.is_active = 1
            GROUP BY w.warehouse_code, w.capacity_sqft
            ORDER BY total_shipments DESC;

-- [Q19] Order-to-Dispatch Lag Anomaly Detection (Supply Chain)
-- Baseline Note: Unindexed comma join with non-SARGable LIKE pattern.
SELECT s.shipment_id, s.carrier_code, s.dispatched_at, o.order_timestamp
            FROM fact_shipments s, fact_orders o
            WHERE s.order_id = o.order_id
              AND s.dispatched_at IS NOT NULL
              AND o.order_status LIKE '%COMPLETED%'
            ORDER BY s.dispatched_at DESC
            LIMIT 50;

-- [Q20] Regional Delivery Concentration by Destination State (Supply Chain)
-- Baseline Note: Function call in WHERE and unindexed joins across 3 tables.
SELECT c.state_code,
                   COUNT(s.shipment_id) AS total_shipments,
                   AVG(s.shipping_cost) AS avg_transit_cost
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE upper(c.country_code) LIKE '%US%'
            GROUP BY c.state_code
            ORDER BY total_shipments DESC;

-- [Q21] Marketing Campaign ROAS and Conversion Yield (Marketing Attribution)
-- Baseline Note: Outer join scanning 15k orders during wide grouping.
SELECT c.campaign_id, c.campaign_name, c.channel_type, c.budget,
                   SUM(o.total_amount) AS attributed_revenue
            FROM dim_campaigns c
            LEFT JOIN fact_orders o ON c.campaign_id = o.campaign_id
            WHERE c.is_active = 1
            GROUP BY c.campaign_id, c.campaign_name, c.channel_type, c.budget
            ORDER BY attributed_revenue DESC;

-- [Q22] Channel Type Revenue Share and Customer Acquisition Count (Marketing Attribution)
-- Baseline Note: Comma join with unindexed foreign key lookups.
SELECT c.channel_type,
                   COUNT(DISTINCT o.customer_id) AS acquired_customers,
                   COUNT(o.order_id) AS total_orders,
                   SUM(o.total_amount) AS total_revenue
            FROM dim_campaigns c, fact_orders o
            WHERE c.campaign_id = o.campaign_id
            GROUP BY c.channel_type
            ORDER BY total_revenue DESC;

-- [Q23] UTM Source and Medium Attribution Matrix (Marketing Attribution)
-- Baseline Note: Unindexed foreign key join with wildcard LIKE filtering.
SELECT c.utm_source, c.utm_medium,
                   COUNT(o.order_id) AS orders_generated,
                   SUM(o.total_amount) AS sales_volume
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            WHERE c.utm_source IS NOT NULL AND c.utm_source LIKE '%e%'
            GROUP BY c.utm_source, c.utm_medium
            ORDER BY sales_volume DESC;

-- [Q24] Campaign Efficiency Ratio (Revenue per Dollar Budget) (Marketing Attribution)
-- Baseline Note: Grouping text column campaign_name on large outer join table before aggregation.
SELECT c.campaign_name, c.budget,
                   SUM(o.total_amount) AS generated_revenue,
                   (SUM(o.total_amount) / CASE WHEN c.budget = 0 THEN 1 ELSE c.budget END) AS roas_ratio
            FROM dim_campaigns c
            LEFT JOIN fact_orders o ON c.campaign_id = o.campaign_id
            GROUP BY c.campaign_name, c.budget
            HAVING SUM(o.total_amount) > 10000
            ORDER BY roas_ratio DESC;

-- [Q25] High-Value Customer Campaign Acquisition Rate (Marketing Attribution)
-- Baseline Note: 3-way unindexed join scanning full customer table with function upper().
SELECT c.campaign_name,
                   COUNT(DISTINCT o.customer_id) AS enterprise_buyers
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            JOIN dim_customers cust ON o.customer_id = cust.customer_id
            WHERE upper(cust.country_code) = 'US' AND cust.is_enterprise = 1
            GROUP BY c.campaign_name
            ORDER BY enterprise_buyers DESC
            LIMIT 10;

-- [Q26] Cumulative Running Revenue & Day-over-Day Velocity (Window Functions)
-- Baseline Note: Unindexed temporal scans requiring application-side cumulative processing.
SELECT d.full_date,
                   SUM(o.total_amount) AS day_rev
            FROM dim_date d
            JOIN fact_orders o ON d.date_key = o.order_date_key
            WHERE d.calendar_year = 2025 AND d.month_number = 1
            GROUP BY d.full_date
            ORDER BY d.full_date;

-- [Q27] Dense Ranking of Top Customers by Annual Spend (Window Functions)
-- Baseline Note: Grouping text fields during wide 3-table join with missing composite indexes.
SELECT c.customer_id, c.full_name, c.state_code,
                   SUM(o.total_amount) AS annual_spend
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            JOIN dim_date d ON o.order_date_key = d.date_key
            WHERE d.calendar_year = 2025
            GROUP BY c.customer_id, c.full_name, c.state_code
            HAVING SUM(o.total_amount) > 5000
            ORDER BY annual_spend DESC
            LIMIT 25;

-- [Q28] Quarter-over-Quarter Revenue Growth with LAG Window (Window Functions)
-- Baseline Note: Unindexed scans across 2 years of transactions.
SELECT d.calendar_year, d.calendar_quarter,
                   SUM(o.total_amount) AS quarter_rev
            FROM dim_date d
            JOIN fact_orders o ON d.date_key = o.order_date_key
            WHERE d.calendar_year IN (2024, 2025)
            GROUP BY d.calendar_year, d.calendar_quarter
            ORDER BY d.calendar_year, d.calendar_quarter;

