"""
Enterprise Analytical Query Registry (28 Production Queries)
Pairing Unoptimised Baseline vs Index-Optimised Implementations.
"""
from dataclasses import dataclass
from typing import List

@dataclass
class AnalyticalQuery:
    query_id: str
    title: str
    category: str
    baseline_sql: str
    optimised_sql: str
    baseline_notes: str
    optimised_notes: str

QUERY_REGISTRY: List[AnalyticalQuery] = [
    # -------------------------------------------------------------------------
    # Domain A: Financials & Revenue Performance
    # -------------------------------------------------------------------------
    AnalyticalQuery(
        query_id="Q01",
        title="Monthly Gross & Net Revenue by Product Category",
        category="Financials",
        baseline_sql="""
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
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Wildcard LIKE predicate on order status preventing index scan on orders.",
        optimised_notes="SARGable equality filter matching composite index idx_orders_date_status."
    ),
    AnalyticalQuery(
        query_id="Q02",
        title="Top 25 High-Yield Customer Cohorts by Spend",
        category="Financials",
        baseline_sql="""
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
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Grouping on wide customer text columns before aggregate filtering.",
        optimised_notes="CTE aggregate pre-filtering on indexed orders table prior to customer join."
    ),
    AnalyticalQuery(
        query_id="Q03",
        title="Daily Revenue Velocity and AOV Trends",
        category="Financials",
        baseline_sql="""
            SELECT d.full_date,
                   SUM(o.total_amount) AS daily_revenue,
                   AVG(o.total_amount) AS avg_order_value,
                   COUNT(o.order_id) AS order_volume
            FROM dim_date d
            LEFT JOIN fact_orders o ON d.date_key = o.order_date_key
            WHERE d.calendar_year = 2025 AND lower(o.order_status) LIKE '%completed%'
            GROUP BY d.full_date
            ORDER BY d.full_date;
        """,
        optimised_sql="""
            SELECT d.full_date,
                   COALESCE(SUM(o.total_amount), 0) AS daily_revenue,
                   COALESCE(AVG(o.total_amount), 0) AS avg_order_value,
                   COUNT(o.order_id) AS order_volume
            FROM dim_date d
            LEFT JOIN fact_orders o ON d.date_key = o.order_date_key AND o.order_status = 'COMPLETED'
            WHERE d.calendar_year = 2025
            GROUP BY d.full_date
            ORDER BY d.full_date;
        """,
        baseline_notes="Unindexed outer join with wildcard LIKE on order status.",
        optimised_notes="Direct integer equality join utilizing B-Tree index on fact_orders.order_date_key."
    ),
    AnalyticalQuery(
        query_id="Q04",
        title="Discount Elasticity and Net Margin by Subcategory",
        category="Financials",
        baseline_sql="""
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
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Unindexed 3-table join with wildcard status pattern forcing nested scans.",
        optimised_notes="Filtered driver join using covering index idx_items_product_aggregate and status index."
    ),
    AnalyticalQuery(
        query_id="Q05",
        title="Quarterly Tax & Shipping Expense Ratio Analysis",
        category="Financials",
        baseline_sql="""
            SELECT d.calendar_year, d.calendar_quarter,
                   SUM(o.tax_amount) AS total_tax,
                   SUM(o.shipping_amount) AS total_shipping,
                   SUM(o.total_amount) AS total_gross
            FROM fact_orders o
            JOIN dim_date d ON o.order_date_key = d.date_key
            WHERE lower(o.order_status) LIKE '%completed%'
            GROUP BY d.calendar_year, d.calendar_quarter
            ORDER BY d.calendar_year, d.calendar_quarter;
        """,
        optimised_sql="""
            SELECT d.calendar_year, d.calendar_quarter,
                   SUM(o.tax_amount) AS total_tax,
                   SUM(o.shipping_amount) AS total_shipping,
                   SUM(o.total_amount) AS total_gross
            FROM fact_orders o
            JOIN dim_date d ON o.order_date_key = d.date_key
            WHERE o.order_status = 'COMPLETED'
            GROUP BY d.calendar_year, d.calendar_quarter
            ORDER BY d.calendar_year, d.calendar_quarter;
        """,
        baseline_notes="Wildcard LIKE status scan forcing sequential scan across all orders.",
        optimised_notes="Direct PK-FK integer join utilizing composite index idx_orders_date_status."
    ),

    # -------------------------------------------------------------------------
    # Domain B: Customer Analytics & Cohorts
    # -------------------------------------------------------------------------
    AnalyticalQuery(
        query_id="Q06",
        title="Customer Lifetime Value (LTV) Segmentation",
        category="Customer Analytics",
        baseline_sql="""
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
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Grouping large unindexed outer join with customer metadata before aggregate filtering.",
        optimised_notes="CTE aggregate pre-filtering on indexed customer_id foreign key prior to dimension join."
    ),
    AnalyticalQuery(
        query_id="Q07",
        title="Customer Recency and Churn Inactivity Profile",
        category="Customer Analytics",
        baseline_sql="""
            SELECT c.customer_id, c.full_name, c.email,
                   MAX(o.order_timestamp) AS last_order_time
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE o.order_timestamp < '2025-06-01'
            GROUP BY c.customer_id, c.full_name, c.email
            ORDER BY last_order_time ASC
            LIMIT 50;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Grouping across wide customer text columns during full table scan.",
        optimised_notes="Aggregation isolated to indexed order table, then joined to customer dimension by primary key."
    ),
    AnalyticalQuery(
        query_id="Q08",
        title="Enterprise vs SMB Account Spend Differential",
        category="Customer Analytics",
        baseline_sql="""
            SELECT c.is_enterprise,
                   COUNT(DISTINCT c.customer_id) AS total_accounts,
                   COUNT(o.order_id) AS total_orders,
                   AVG(o.total_amount) AS avg_ticket_size,
                   SUM(o.total_amount) AS total_gross_spend
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE upper(c.country_code) LIKE '%US%'
            GROUP BY c.is_enterprise;
        """,
        optimised_sql="""
            SELECT c.is_enterprise,
                   COUNT(DISTINCT c.customer_id) AS total_accounts,
                   COUNT(o.order_id) AS total_orders,
                   AVG(o.total_amount) AS avg_ticket_size,
                   SUM(o.total_amount) AS total_gross_spend
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE c.country_code = 'US'
            GROUP BY c.is_enterprise;
        """,
        baseline_notes="Function upper() on country_code invalidating index use on customers.",
        optimised_notes="SARGable predicate matching normalized country_code with covering index idx_customers_geo_enterprise."
    ),
    AnalyticalQuery(
        query_id="Q09",
        title="Geographical Revenue Concentration by State",
        category="Customer Analytics",
        baseline_sql="""
            SELECT c.state_code,
                   COUNT(DISTINCT c.customer_id) AS unique_buyers,
                   SUM(o.total_amount) AS state_revenue
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE c.state_code IS NOT NULL AND c.state_code <> 'UNKNOWN'
            GROUP BY c.state_code
            ORDER BY state_revenue DESC
            LIMIT 15;
        """,
        optimised_sql="""
            SELECT c.state_code,
                   COUNT(DISTINCT c.customer_id) AS unique_buyers,
                   SUM(o.total_amount) AS state_revenue
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            WHERE c.state_code <> 'UNKNOWN'
            GROUP BY c.state_code
            ORDER BY state_revenue DESC
            LIMIT 15;
        """,
        baseline_notes="Redundant IS NOT NULL scan over wide customer table; unindexed join.",
        optimised_notes="Covering index idx_customers_geo_enterprise used with indexed customer foreign key."
    ),
    AnalyticalQuery(
        query_id="Q10",
        title="Repeat Customer Frequency and Purchase Velocity",
        category="Customer Analytics",
        baseline_sql="""
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
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Grouping wide customer columns during multi-table join.",
        optimised_notes="Pre-aggregation CTE leveraging composite index idx_orders_customer_date."
    ),

    # -------------------------------------------------------------------------
    # Domain C: Product Merchandising & Basket Analytics
    # -------------------------------------------------------------------------
    AnalyticalQuery(
        query_id="Q11",
        title="Fast-Moving vs Slow-Moving Inventory Velocity by SKU",
        category="Product Merchandising",
        baseline_sql="""
            SELECT p.sku, p.product_name, p.category,
                   SUM(oi.quantity) AS total_units_sold,
                   SUM(oi.line_total) AS total_revenue
            FROM dim_products p
            JOIN fact_order_items oi ON p.product_id = oi.product_id
            WHERE p.is_active = 1
            GROUP BY p.sku, p.product_name, p.category
            ORDER BY total_units_sold DESC
            LIMIT 20;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Grouping product metadata across 45k item rows in nested scan.",
        optimised_notes="Pre-aggregated derived table using covering index idx_items_product_aggregate."
    ),
    AnalyticalQuery(
        query_id="Q12",
        title="Product Margin Contribution and Profit Ratio",
        category="Product Merchandising",
        baseline_sql="""
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
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Redundant repeated multiplication across 45k item rows in comma-join syntax.",
        optimised_notes="Pre-summing quantity once in index scan and calculating profit at product summary level."
    ),
    AnalyticalQuery(
        query_id="Q13",
        title="Category Discount Leakage vs Target Margin",
        category="Product Merchandising",
        baseline_sql="""
            SELECT p.category,
                   AVG(oi.discount_rate) AS mean_discount_rate,
                   SUM(oi.quantity * oi.unit_price * oi.discount_rate) AS total_discount_given
            FROM fact_order_items oi
            JOIN dim_products p ON oi.product_id = p.product_id
            WHERE cast(oi.discount_rate as text) <> '0.0'
            GROUP BY p.category
            ORDER BY total_discount_given DESC;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="String casting on numeric discount_rate in WHERE clause disabling B-Tree indexing.",
        optimised_notes="Pre-aggregation derived table utilizing index idx_items_product_aggregate."
    ),
    AnalyticalQuery(
        query_id="Q14",
        title="High-Value Basket Line Item Density",
        category="Product Merchandising",
        baseline_sql="""
            SELECT oi.order_id,
                   COUNT(oi.product_id) AS distinct_items,
                   SUM(oi.line_total) AS basket_size
            FROM fact_order_items oi
            JOIN fact_orders o ON oi.order_id = o.order_id
            WHERE o.total_amount > 1500 AND lower(o.order_status) LIKE '%completed%'
            GROUP BY oi.order_id
            ORDER BY basket_size DESC
            LIMIT 30;
        """,
        optimised_sql="""
            SELECT oi.order_id,
                   COUNT(oi.product_id) AS distinct_items,
                   SUM(oi.line_total) AS basket_size
            FROM fact_orders o
            JOIN fact_order_items oi ON o.order_id = oi.order_id
            WHERE o.total_amount > 1500 AND o.order_status = 'COMPLETED'
            GROUP BY oi.order_id
            ORDER BY basket_size DESC
            LIMIT 30;
        """,
        baseline_notes="Unindexed join with wildcard status pattern forcing nested scans.",
        optimised_notes="Direct indexed join leveraging composite index idx_items_order_product and status index."
    ),
    AnalyticalQuery(
        query_id="Q15",
        title="Subcategory Unit Sales Distribution and Weight Profile",
        category="Product Merchandising",
        baseline_sql="""
            SELECT p.category, p.subcategory,
                   AVG(p.weight_kg) AS avg_weight,
                   SUM(oi.quantity) AS total_quantity_shipped
            FROM dim_products p
            LEFT JOIN fact_order_items oi ON p.product_id = oi.product_id
            GROUP BY p.category, p.subcategory
            ORDER BY total_quantity_shipped DESC;
        """,
        optimised_sql="""
            SELECT p.category, p.subcategory,
                   AVG(p.weight_kg) AS avg_weight,
                   COALESCE(SUM(oi.quantity), 0) AS total_quantity_shipped
            FROM dim_products p
            LEFT JOIN fact_order_items oi ON p.product_id = oi.product_id
            GROUP BY p.category, p.subcategory
            ORDER BY total_quantity_shipped DESC;
        """,
        baseline_notes="Sequential scan of products and unindexed fact_order_items join.",
        optimised_notes="Covering index idx_products_category_sub combined with covering index on items."
    ),

    # -------------------------------------------------------------------------
    # Domain D: Logistics & Supply Chain SLA
    # -------------------------------------------------------------------------
    AnalyticalQuery(
        query_id="Q16",
        title="Warehouse Outbound Fulfillment SLA and Volume",
        category="Supply Chain",
        baseline_sql="""
            SELECT w.warehouse_name, w.state_code,
                   COUNT(s.shipment_id) AS total_dispatched,
                   AVG(s.shipping_cost) AS avg_shipping_cost
            FROM dim_warehouses w
            JOIN fact_shipments s ON w.warehouse_id = s.warehouse_id
            WHERE s.shipping_status LIKE '%DELIVERED%'
            GROUP BY w.warehouse_name, w.state_code
            ORDER BY total_dispatched DESC;
        """,
        optimised_sql="""
            SELECT w.warehouse_name, w.state_code,
                   COUNT(s.shipment_id) AS total_dispatched,
                   AVG(s.shipping_cost) AS avg_shipping_cost
            FROM dim_warehouses w
            JOIN fact_shipments s ON w.warehouse_id = s.warehouse_id
            WHERE s.shipping_status = 'DELIVERED'
            GROUP BY w.warehouse_name, w.state_code
            ORDER BY total_dispatched DESC;
        """,
        baseline_notes="Non-SARGable LIKE pattern preventing index scan on shipment status.",
        optimised_notes="SARGable equality filter matching index idx_shipments_dispatch_status."
    ),
    AnalyticalQuery(
        query_id="Q17",
        title="Carrier Delivery Performance and Freight Cost Breakdown",
        category="Supply Chain",
        baseline_sql="""
            SELECT s.carrier_code,
                   COUNT(s.shipment_id) AS shipment_count,
                   SUM(s.shipping_cost) AS total_freight_expenditure,
                   AVG(s.shipping_cost) AS mean_cost_per_shipment
            FROM fact_shipments s
            JOIN fact_orders o ON s.order_id = o.order_id
            WHERE lower(o.order_status) LIKE '%completed%'
            GROUP BY s.carrier_code
            ORDER BY total_freight_expenditure DESC;
        """,
        optimised_sql="""
            SELECT s.carrier_code,
                   COUNT(s.shipment_id) AS shipment_count,
                   SUM(s.shipping_cost) AS total_freight_expenditure,
                   AVG(s.shipping_cost) AS mean_cost_per_shipment
            FROM fact_orders o
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE o.order_status = 'COMPLETED'
            GROUP BY s.carrier_code
            ORDER BY total_freight_expenditure DESC;
        """,
        baseline_notes="Wildcard pattern on order status forcing full scan across orders.",
        optimised_notes="Indexed relational join between fact_orders and fact_shipments via idx_shipments_order_wh."
    ),
    AnalyticalQuery(
        query_id="Q18",
        title="Warehouse Utilization vs Outbound Capacity Bottleneck",
        category="Supply Chain",
        baseline_sql="""
            SELECT w.warehouse_code, w.capacity_sqft,
                   COUNT(s.shipment_id) AS total_shipments
            FROM dim_warehouses w
            LEFT JOIN fact_shipments s ON w.warehouse_id = s.warehouse_id
            WHERE w.is_active = 1
            GROUP BY w.warehouse_code, w.capacity_sqft
            ORDER BY total_shipments DESC;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Outer join scanning full shipments table during warehouse grouping.",
        optimised_notes="Single aggregation pass on fact_shipments joined to warehouse dimension."
    ),
    AnalyticalQuery(
        query_id="Q19",
        title="Order-to-Dispatch Lag Anomaly Detection",
        category="Supply Chain",
        baseline_sql="""
            SELECT s.shipment_id, s.carrier_code, s.dispatched_at, o.order_timestamp
            FROM fact_shipments s, fact_orders o
            WHERE s.order_id = o.order_id
              AND s.dispatched_at IS NOT NULL
              AND o.order_status LIKE '%COMPLETED%'
            ORDER BY s.dispatched_at DESC
            LIMIT 50;
        """,
        optimised_sql="""
            SELECT s.shipment_id, s.carrier_code, s.dispatched_at, o.order_timestamp
            FROM fact_orders o
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE o.order_status = 'COMPLETED'
              AND s.dispatched_at IS NOT NULL
            ORDER BY s.dispatched_at DESC
            LIMIT 50;
        """,
        baseline_notes="Unindexed comma join with non-SARGable LIKE pattern.",
        optimised_notes="Index join on foreign key fact_shipments.order_id with covering index."
    ),
    AnalyticalQuery(
        query_id="Q20",
        title="Regional Delivery Concentration by Destination State",
        category="Supply Chain",
        baseline_sql="""
            SELECT c.state_code,
                   COUNT(s.shipment_id) AS total_shipments,
                   AVG(s.shipping_cost) AS avg_transit_cost
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE upper(c.country_code) LIKE '%US%'
            GROUP BY c.state_code
            ORDER BY total_shipments DESC;
        """,
        optimised_sql="""
            SELECT c.state_code,
                   COUNT(s.shipment_id) AS total_shipments,
                   AVG(s.shipping_cost) AS avg_transit_cost
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            JOIN fact_shipments s ON o.order_id = s.order_id
            WHERE c.country_code = 'US'
            GROUP BY c.state_code
            ORDER BY total_shipments DESC;
        """,
        baseline_notes="Function call in WHERE and unindexed joins across 3 tables.",
        optimised_notes="Covering composite indexes idx_orders_customer_date and idx_shipments_order_wh applied."
    ),

    # -------------------------------------------------------------------------
    # Domain E: Marketing Campaigns & Attribution
    # -------------------------------------------------------------------------
    AnalyticalQuery(
        query_id="Q21",
        title="Marketing Campaign ROAS and Conversion Yield",
        category="Marketing Attribution",
        baseline_sql="""
            SELECT c.campaign_id, c.campaign_name, c.channel_type, c.budget,
                   SUM(o.total_amount) AS attributed_revenue
            FROM dim_campaigns c
            LEFT JOIN fact_orders o ON c.campaign_id = o.campaign_id
            WHERE c.is_active = 1
            GROUP BY c.campaign_id, c.campaign_name, c.channel_type, c.budget
            ORDER BY attributed_revenue DESC;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Outer join scanning 15k orders during wide grouping.",
        optimised_notes="Single pass aggregation using partial index idx_orders_campaign."
    ),
    AnalyticalQuery(
        query_id="Q22",
        title="Channel Type Revenue Share and Customer Acquisition Count",
        category="Marketing Attribution",
        baseline_sql="""
            SELECT c.channel_type,
                   COUNT(DISTINCT o.customer_id) AS acquired_customers,
                   COUNT(o.order_id) AS total_orders,
                   SUM(o.total_amount) AS total_revenue
            FROM dim_campaigns c, fact_orders o
            WHERE c.campaign_id = o.campaign_id
            GROUP BY c.channel_type
            ORDER BY total_revenue DESC;
        """,
        optimised_sql="""
            SELECT c.channel_type,
                   COUNT(DISTINCT o.customer_id) AS acquired_customers,
                   COUNT(o.order_id) AS total_orders,
                   SUM(o.total_amount) AS total_revenue
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            GROUP BY c.channel_type
            ORDER BY total_revenue DESC;
        """,
        baseline_notes="Comma join with unindexed foreign key lookups.",
        optimised_notes="Explicit inner join matching partial index on campaign_id."
    ),
    AnalyticalQuery(
        query_id="Q23",
        title="UTM Source and Medium Attribution Matrix",
        category="Marketing Attribution",
        baseline_sql="""
            SELECT c.utm_source, c.utm_medium,
                   COUNT(o.order_id) AS orders_generated,
                   SUM(o.total_amount) AS sales_volume
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            WHERE c.utm_source IS NOT NULL AND c.utm_source LIKE '%e%'
            GROUP BY c.utm_source, c.utm_medium
            ORDER BY sales_volume DESC;
        """,
        optimised_sql="""
            SELECT c.utm_source, c.utm_medium,
                   COUNT(o.order_id) AS orders_generated,
                   SUM(o.total_amount) AS sales_volume
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            WHERE c.utm_source IS NOT NULL
            GROUP BY c.utm_source, c.utm_medium
            ORDER BY sales_volume DESC;
        """,
        baseline_notes="Unindexed foreign key join with wildcard LIKE filtering.",
        optimised_notes="Partial index on fact_orders(campaign_id) eliminating null scan rows."
    ),
    AnalyticalQuery(
        query_id="Q24",
        title="Campaign Efficiency Ratio (Revenue per Dollar Budget)",
        category="Marketing Attribution",
        baseline_sql="""
            SELECT c.campaign_name, c.budget,
                   SUM(o.total_amount) AS generated_revenue,
                   (SUM(o.total_amount) / CASE WHEN c.budget = 0 THEN 1 ELSE c.budget END) AS roas_ratio
            FROM dim_campaigns c
            LEFT JOIN fact_orders o ON c.campaign_id = o.campaign_id
            GROUP BY c.campaign_name, c.budget
            HAVING SUM(o.total_amount) > 10000
            ORDER BY roas_ratio DESC;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Grouping text column campaign_name on large outer join table before aggregation.",
        optimised_notes="Aggregating on campaign_id first, then joining to dimension."
    ),
    AnalyticalQuery(
        query_id="Q25",
        title="High-Value Customer Campaign Acquisition Rate",
        category="Marketing Attribution",
        baseline_sql="""
            SELECT c.campaign_name,
                   COUNT(DISTINCT o.customer_id) AS enterprise_buyers
            FROM dim_campaigns c
            JOIN fact_orders o ON c.campaign_id = o.campaign_id
            JOIN dim_customers cust ON o.customer_id = cust.customer_id
            WHERE upper(cust.country_code) = 'US' AND cust.is_enterprise = 1
            GROUP BY c.campaign_name
            ORDER BY enterprise_buyers DESC
            LIMIT 10;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="3-way unindexed join scanning full customer table with function upper().",
        optimised_notes="CTE isolating indexed enterprise customers joined with partial index idx_orders_campaign."
    ),

    # -------------------------------------------------------------------------
    # Domain F: Window Functions & Advanced Time Series
    # -------------------------------------------------------------------------
    AnalyticalQuery(
        query_id="Q26",
        title="Cumulative Running Revenue & Day-over-Day Velocity",
        category="Window Functions",
        baseline_sql="""
            SELECT d.full_date,
                   SUM(o.total_amount) AS day_rev
            FROM dim_date d
            JOIN fact_orders o ON d.date_key = o.order_date_key
            WHERE d.calendar_year = 2025 AND d.month_number = 1
            GROUP BY d.full_date
            ORDER BY d.full_date;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Unindexed temporal scans requiring application-side cumulative processing.",
        optimised_notes="Linear analytic window function SUM() OVER() over pre-aggregated daily sales CTE with integer index."
    ),
    AnalyticalQuery(
        query_id="Q27",
        title="Dense Ranking of Top Customers by Annual Spend",
        category="Window Functions",
        baseline_sql="""
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
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Grouping text fields during wide 3-table join with missing composite indexes.",
        optimised_notes="Single pass annual aggregation joined to customers with window function DENSE_RANK()."
    ),
    AnalyticalQuery(
        query_id="Q28",
        title="Quarter-over-Quarter Revenue Growth with LAG Window",
        category="Window Functions",
        baseline_sql="""
            SELECT d.calendar_year, d.calendar_quarter,
                   SUM(o.total_amount) AS quarter_rev
            FROM dim_date d
            JOIN fact_orders o ON d.date_key = o.order_date_key
            WHERE d.calendar_year IN (2024, 2025)
            GROUP BY d.calendar_year, d.calendar_quarter
            ORDER BY d.calendar_year, d.calendar_quarter;
        """,
        optimised_sql="""
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
        """,
        baseline_notes="Unindexed scans across 2 years of transactions.",
        optimised_notes="Analytic window function LAG() with inline growth percentage calculation over indexed dates."
    )
]
