-- [Q01] Monthly Gross & Net Revenue by Product Category (Financials)
-- Optimised Note: SARGable equality filter matching composite index idx_orders_date_status.
SELECT p.category, d.calendar_year, d.month_name,
                   SUM(oi.line_total) AS total_gross,
                   AVG(oi.line_total) AS avg_item_rev
            FROM fact_orders o
            JOIN dim_date d ON o.order_date_key = d.date_key
            JOIN fact_order_items oi ON o.order_id = oi.order_id
            JOIN dim_products p ON oi.product_id = p.product_id
            WHERE d.calendar_year = 2025
              AND o.order_status = 'COMPLETED'
            GROUP BY p.category, d.calendar_year, d.month_name, d.month_number
            ORDER BY p.category, d.month_number;

-- [Q02] Top 25 High-Yield Customer Cohorts by Spend (Financials)
-- Optimised Note: CTE aggregate pre-filtering on indexed orders table prior to customer join.
WITH CustAgg AS (
                SELECT customer_id, SUM(total_amount) AS total_spent, COUNT(order_id) AS total_orders
                FROM fact_orders
                WHERE total_amount > 0
                GROUP BY customer_id
                HAVING COUNT(order_id) >= 5
            )
            SELECT c.customer_id, c.full_name, c.credit_limit,
                   ca.total_spent, ca.total_orders
            FROM CustAgg ca
            JOIN dim_customers c ON ca.customer_id = c.customer_id
            WHERE c.country_code = 'US'
            ORDER BY ca.total_spent DESC
            LIMIT 25;

-- [Q03] Daily Revenue Velocity and AOV Trends (Financials)
-- Optimised Note: Direct integer equality join utilizing B-Tree index on fact_orders.order_date_key.
SELECT d.full_date,
                   COALESCE(SUM(o.total_amount), 0) AS daily_revenue,
                   COALESCE(AVG(o.total_amount), 0) AS avg_order_value,
                   COUNT(o.order_id) AS order_volume
            FROM dim_date d
            LEFT JOIN fact_orders o ON d.date_key = o.order_date_key AND o.order_status = 'COMPLETED'
            WHERE d.calendar_year = 2025
            GROUP BY d.full_date
            ORDER BY d.full_date;

-- [Q04] Discount Elasticity and Net Margin by Subcategory (Financials)
-- Optimised Note: Filtered driver join using covering index idx_items_product_aggregate and status index.
SELECT p.subcategory,
                   AVG(oi.discount_rate) AS avg_discount,
                   SUM(oi.line_total) AS gross_sales,
                   SUM(oi.quantity * p.cost_price) AS total_cost
            FROM dim_products p
            JOIN fact_order_items oi ON p.product_id = oi.product_id
            JOIN fact_orders o ON oi.order_id = o.order_id
            WHERE p.is_active = 1 AND o.order_status = 'COMPLETED'
            GROUP BY p.subcategory
            HAVING SUM(oi.line_total) > 5000
            ORDER BY gross_sales DESC;

-- [Q05] Quarterly Tax & Shipping Expense Ratio Analysis (Financials)
-- Optimised Note: Direct PK-FK integer join utilizing composite index idx_orders_date_status.
SELECT d.calendar_year, d.calendar_quarter,
                   SUM(o.tax_amount) AS total_tax,
                   SUM(o.shipping_amount) AS total_shipping,
                   SUM(o.total_amount) AS total_gross
            FROM fact_orders o
            JOIN dim_date d ON o.order_date_key = d.date_key
            WHERE o.order_status = 'COMPLETED'
            GROUP BY d.calendar_year, d.calendar_quarter
            ORDER BY d.calendar_year, d.calendar_quarter;

-- [Q06] Customer Lifetime Value (LTV) Segmentation (Customer Analytics)
-- Optimised Note: CTE aggregate pre-filtering on indexed customer_id foreign key prior to dimension join.
WITH CustOrders AS (
                SELECT customer_id, COUNT(order_id) AS total_orders, SUM(total_amount) AS lifetime_value
                FROM fact_orders
                GROUP BY customer_id
                HAVING COUNT(order_id) >= 3
            )
            SELECT c.customer_id, c.full_name, c.state_code,
                   co.total_orders, co.lifetime_value
            FROM CustOrders co
            JOIN dim_customers c ON co.customer_id = c.customer_id
            WHERE c.country_code = 'US'
            ORDER BY co.lifetime_value DESC
            LIMIT 50;

-- [Q07] Customer Recency and Churn Inactivity Profile (Customer Analytics)
-- Optimised Note: Aggregation isolated to indexed order table, then joined to customer dimension by primary key.
SELECT c.customer_id, c.full_name, c.email,
                   last_ord.max_ts AS last_order_time
            FROM (
                SELECT customer_id, MAX(order_timestamp) AS max_ts
                FROM fact_orders
                GROUP BY customer_id
                HAVING MAX(order_timestamp) < '2025-06-01'
            ) last_ord
            JOIN dim_customers c ON last_ord.customer_id = c.customer_id
            ORDER BY last_ord.max_ts ASC
            LIMIT 50;

-- [Q08] Enterprise vs SMB Account Spend Differential (Customer Analytics)
-- Optimised Note: SARGable predicate matching normalized country_code with covering index idx_customers_geo_enterprise.
SELECT c.is_enterprise,
                   COUNT(DISTINCT c.customer_id) AS total_accounts,
                   COUNT(o.order_id) AS total_orders,
                   AVG(o.total_amount) AS avg_ticket_size,
                   SUM(o.total_amount) AS total_gross_spend
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE c.country_code = 'US'
            GROUP BY c.is_enterprise;

-- [Q09] Geographical Revenue Concentration by State (Customer Analytics)
-- Optimised Note: Covering index idx_customers_geo_enterprise used with indexed customer foreign key.
SELECT c.state_code,
                   COUNT(DISTINCT c.customer_id) AS unique_buyers,
                   SUM(o.total_amount) AS state_revenue
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE c.state_code <> 'UNKNOWN'
            GROUP BY c.state_code
            ORDER BY state_revenue DESC
            LIMIT 15;

-- [Q10] Repeat Customer Frequency and Purchase Velocity (Customer Analytics)
-- Optimised Note: Pre-aggregation CTE leveraging composite index idx_orders_customer_date.
WITH HighFreqCust AS (
                SELECT customer_id, COUNT(order_id) AS ord_count,
                       MIN(order_timestamp) AS first_ord, MAX(order_timestamp) AS last_ord
                FROM fact_orders
                WHERE order_date_key BETWEEN 20250101 AND 20251231
                GROUP BY customer_id
                HAVING COUNT(order_id) > 6
            )
            SELECT c.customer_id, c.full_name, hfc.ord_count, hfc.first_ord, hfc.last_ord
            FROM HighFreqCust hfc
            JOIN dim_customers c ON hfc.customer_id = c.customer_id
            ORDER BY hfc.ord_count DESC
            LIMIT 25;

-- [Q11] Fast-Moving vs Slow-Moving Inventory Velocity by SKU (Product Merchandising)
-- Optimised Note: Pre-aggregated derived table using covering index idx_items_product_aggregate.
SELECT p.sku, p.product_name, p.category,
                   sales.total_units_sold, sales.total_revenue
            FROM dim_products p
            JOIN (
                SELECT product_id, SUM(quantity) AS total_units_sold, SUM(line_total) AS total_revenue
                FROM fact_order_items
                GROUP BY product_id
            ) sales ON p.product_id = sales.product_id
            WHERE p.is_active = 1
            ORDER BY sales.total_units_sold DESC
            LIMIT 20;

-- [Q12] Product Margin Contribution and Profit Ratio (Product Merchandising)
-- Optimised Note: Pre-summing quantity once in index scan and calculating profit at product summary level.
SELECT p.product_id, p.product_name, p.retail_price, p.cost_price,
                   agg.total_revenue,
                   (agg.total_qty * p.cost_price) AS total_cogs,
                   (agg.total_revenue - (agg.total_qty * p.cost_price)) AS gross_profit
            FROM dim_products p
            JOIN (
                SELECT product_id, SUM(line_total) AS total_revenue, SUM(quantity) AS total_qty
                FROM fact_order_items
                GROUP BY product_id
                HAVING SUM(line_total) > 5000
            ) agg ON p.product_id = agg.product_id
            ORDER BY gross_profit DESC
            LIMIT 25;

-- [Q13] Category Discount Leakage vs Target Margin (Product Merchandising)
-- Optimised Note: Pre-aggregation derived table utilizing index idx_items_product_aggregate.
SELECT p.category,
                   AVG(oi.discount_rate) AS mean_discount_rate,
                   SUM(oi.line_total * oi.discount_rate) AS total_discount_given
            FROM dim_products p
            JOIN (
                SELECT product_id, AVG(discount_rate) AS discount_rate, SUM(line_total) AS line_total
                FROM fact_order_items
                WHERE discount_rate > 0.00
                GROUP BY product_id
            ) oi ON p.product_id = oi.product_id
            GROUP BY p.category
            ORDER BY total_discount_given DESC;

-- [Q14] High-Value Basket Line Item Density (Product Merchandising)
-- Optimised Note: Direct indexed join leveraging composite index idx_items_order_product and status index.
SELECT oi.order_id,
                   COUNT(oi.product_id) AS distinct_items,
                   SUM(oi.line_total) AS basket_size
            FROM fact_orders o
            JOIN fact_order_items oi ON o.order_id = oi.order_id
            WHERE o.total_amount > 1500 AND o.order_status = 'COMPLETED'
            GROUP BY oi.order_id
            ORDER BY basket_size DESC
            LIMIT 30;

-- [Q15] Subcategory Unit Sales Distribution and Weight Profile (Product Merchandising)
-- Optimised Note: Covering index idx_products_category_sub combined with covering index on items.
SELECT p.category, p.subcategory,
                   AVG(p.weight_kg) AS avg_weight,
                   COALESCE(SUM(oi.quantity), 0) AS total_quantity_shipped
            FROM dim_products p
            LEFT JOIN fact_order_items oi ON p.product_id = oi.product_id
            GROUP BY p.category, p.subcategory
            ORDER BY total_quantity_shipped DESC;

-- [Q16] Warehouse Outbound Fulfillment SLA and Volume (Supply Chain)
-- Optimised Note: SARGable equality filter matching index idx_shipments_dispatch_status.
SELECT w.warehouse_name, w.state_code,
                   COUNT(s.shipment_id) AS total_dispatched,
                   AVG(s.shipping_cost) AS avg_shipping_cost
            FROM dim_warehouses w
            JOIN fact_shipments s ON w.warehouse_id = s.warehouse_id
            WHERE s.shipping_status = 'DELIVERED'
            GROUP BY w.warehouse_name, w.state_code
            ORDER BY total_dispatched DESC;

-- [Q17] Carrier Delivery Performance and Freight Cost Breakdown (Supply Chain)
-- Optimised Note: Indexed relational join between fact_orders and fact_shipments via idx_shipments_order_wh.
SELECT s.carrier_code,
                   COUNT(s.shipment_id) AS shipment_count,
                   SUM(s.shipping_cost) AS total_freight_expenditure,
                   AVG(s.shipping_cost) AS mean_cost_per_shipment
            FROM fact_orders o
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE o.order_status = 'COMPLETED'
            GROUP BY s.carrier_code
            ORDER BY total_freight_expenditure DESC;

-- [Q18] Warehouse Utilization vs Outbound Capacity Bottleneck (Supply Chain)
-- Optimised Note: Single aggregation pass on fact_shipments joined to warehouse dimension.
SELECT w.warehouse_code, w.capacity_sqft,
                   COALESCE(ship_cnt.total_shipments, 0) AS total_shipments
            FROM dim_warehouses w
            LEFT JOIN (
                SELECT warehouse_id, COUNT(*) AS total_shipments
                FROM fact_shipments
                GROUP BY warehouse_id
            ) ship_cnt ON w.warehouse_id = ship_cnt.warehouse_id
            WHERE w.is_active = 1
            ORDER BY total_shipments DESC;

-- [Q19] Order-to-Dispatch Lag Anomaly Detection (Supply Chain)
-- Optimised Note: Index join on foreign key fact_shipments.order_id with covering index.
SELECT s.shipment_id, s.carrier_code, s.dispatched_at, o.order_timestamp
            FROM fact_orders o
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE o.order_status = 'COMPLETED'
              AND s.dispatched_at IS NOT NULL
            ORDER BY s.dispatched_at DESC
            LIMIT 50;

-- [Q20] Regional Delivery Concentration by Destination State (Supply Chain)
-- Optimised Note: Covering composite indexes idx_orders_customer_date and idx_shipments_order_wh applied.
SELECT c.state_code,
                   COUNT(s.shipment_id) AS total_shipments,
                   AVG(s.shipping_cost) AS avg_transit_cost
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE c.country_code = 'US'
            GROUP BY c.state_code
            ORDER BY total_shipments DESC;

-- [Q21] Marketing Campaign ROAS and Conversion Yield (Marketing Attribution)
-- Optimised Note: Single pass aggregation using partial index idx_orders_campaign.
SELECT c.campaign_id, c.campaign_name, c.channel_type, c.budget,
                   COALESCE(rev.attributed_revenue, 0) AS attributed_revenue
            FROM dim_campaigns c
            LEFT JOIN (
                SELECT campaign_id, SUM(total_amount) AS attributed_revenue
                FROM fact_orders
                WHERE campaign_id IS NOT NULL
                GROUP BY campaign_id
            ) rev ON c.campaign_id = rev.campaign_id
            WHERE c.is_active = 1
            ORDER BY attributed_revenue DESC;

-- [Q22] Channel Type Revenue Share and Customer Acquisition Count (Marketing Attribution)
-- Optimised Note: Explicit inner join matching partial index on campaign_id.
SELECT c.channel_type,
                   COUNT(DISTINCT o.customer_id) AS acquired_customers,
                   COUNT(o.order_id) AS total_orders,
                   SUM(o.total_amount) AS total_revenue
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            GROUP BY c.channel_type
            ORDER BY total_revenue DESC;

-- [Q23] UTM Source and Medium Attribution Matrix (Marketing Attribution)
-- Optimised Note: Partial index on fact_orders(campaign_id) eliminating null scan rows.
SELECT c.utm_source, c.utm_medium,
                   COUNT(o.order_id) AS orders_generated,
                   SUM(o.total_amount) AS sales_volume
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            WHERE c.utm_source IS NOT NULL
            GROUP BY c.utm_source, c.utm_medium
            ORDER BY sales_volume DESC;

-- [Q24] Campaign Efficiency Ratio (Revenue per Dollar Budget) (Marketing Attribution)
-- Optimised Note: Aggregating on campaign_id first, then joining to dimension.
SELECT c.campaign_name, c.budget,
                   agg.generated_revenue,
                   (agg.generated_revenue / CASE WHEN c.budget = 0 THEN 1 ELSE c.budget END) AS roas_ratio
            FROM dim_campaigns c
            JOIN (
                SELECT campaign_id, SUM(total_amount) AS generated_revenue
                FROM fact_orders
                WHERE campaign_id IS NOT NULL
                GROUP BY campaign_id
                HAVING SUM(total_amount) > 10000
            ) agg ON c.campaign_id = agg.campaign_id
            ORDER BY roas_ratio DESC;

-- [Q25] High-Value Customer Campaign Acquisition Rate (Marketing Attribution)
-- Optimised Note: CTE isolating indexed enterprise customers joined with partial index idx_orders_campaign.
WITH EntBuyers AS (
                SELECT customer_id FROM dim_customers WHERE country_code = 'US' AND is_enterprise = 1
            )
            SELECT c.campaign_name,
                   COUNT(DISTINCT o.customer_id) AS enterprise_buyers
            FROM fact_orders o
            JOIN EntBuyers eb ON o.customer_id = eb.customer_id
            JOIN dim_campaigns c ON o.campaign_id = c.campaign_id
            WHERE o.campaign_id IS NOT NULL
            GROUP BY c.campaign_name
            ORDER BY enterprise_buyers DESC
            LIMIT 10;

-- [Q26] Cumulative Running Revenue & Day-over-Day Velocity (Window Functions)
-- Optimised Note: Linear analytic window function SUM() OVER() over pre-aggregated daily sales CTE with integer index.
WITH DailySales AS (
                SELECT d.full_date, SUM(o.total_amount) AS day_rev
                FROM dim_date d
                JOIN fact_orders o ON d.date_key = o.order_date_key
                WHERE d.calendar_year = 2025 AND d.month_number = 1
                GROUP BY d.full_date
            )
            SELECT full_date, day_rev,
                   SUM(day_rev) OVER (ORDER BY full_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_rev
            FROM DailySales
            ORDER BY full_date;

-- [Q27] Dense Ranking of Top Customers by Annual Spend (Window Functions)
-- Optimised Note: Single pass annual aggregation joined to customers with window function DENSE_RANK().
WITH AnnualCustSpend AS (
                SELECT o.customer_id, SUM(o.total_amount) AS annual_spend
                FROM fact_orders o
                JOIN dim_date d ON o.order_date_key = d.date_key
                WHERE d.calendar_year = 2025
                GROUP BY o.customer_id
                HAVING SUM(o.total_amount) > 5000
            )
            SELECT c.customer_id, c.full_name, c.state_code,
                   acs.annual_spend,
                   DENSE_RANK() OVER (ORDER BY acs.annual_spend DESC) AS spend_rank
            FROM AnnualCustSpend acs
            JOIN dim_customers c ON acs.customer_id = c.customer_id
            ORDER BY acs.annual_spend DESC
            LIMIT 25;

-- [Q28] Quarter-over-Quarter Revenue Growth with LAG Window (Window Functions)
-- Optimised Note: Analytic window function LAG() with inline growth percentage calculation over indexed dates.
WITH QuarterlyRev AS (
                SELECT d.calendar_year, d.calendar_quarter,
                       SUM(o.total_amount) AS quarter_rev
                FROM dim_date d
                JOIN fact_orders o ON d.date_key = o.order_date_key
                WHERE d.calendar_year IN (2024, 2025)
                GROUP BY d.calendar_year, d.calendar_quarter
            )
            SELECT calendar_year, calendar_quarter, quarter_rev,
                   LAG(quarter_rev, 1) OVER (ORDER BY calendar_year, calendar_quarter) AS prior_quarter_rev,
                   ROUND(((quarter_rev - LAG(quarter_rev, 1) OVER (ORDER BY calendar_year, calendar_quarter)) /
                          NULLIF(LAG(quarter_rev, 1) OVER (ORDER BY calendar_year, calendar_quarter), 0)) * 100.0, 2) AS qoq_growth_pct
            FROM QuarterlyRev
            ORDER BY calendar_year, calendar_quarter;

