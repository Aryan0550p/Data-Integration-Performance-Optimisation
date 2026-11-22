-- ============================================================================
-- Enterprise Performance Optimisation Indexes (PostgreSQL)
-- B-Tree, Composite, Partial, and Covering Indexes
-- ============================================================================

-- 1. Orders: Covering Composite Index on Customer & Order Date
CREATE INDEX idx_orders_customer_date ON fact_orders (customer_id, order_date_key) 
    INCLUDE (total_amount, order_status);

-- 2. Orders: Covering Composite Index on Date Key & Status
CREATE INDEX idx_orders_date_status ON fact_orders (order_date_key, order_status) 
    INCLUDE (total_amount, subtotal, discount_amount);

-- 3. Orders: Partial Index on Completed Orders
CREATE INDEX idx_orders_completed_active ON fact_orders (order_date_key, customer_id) 
    WHERE order_status = 'COMPLETED';

-- 4. Orders: Campaign Attribution Index
CREATE INDEX idx_orders_campaign ON fact_orders (campaign_id) 
    WHERE campaign_id IS NOT NULL;

-- 5. Order Items: Composite Index on Order ID & Product ID
CREATE INDEX idx_items_order_product ON fact_order_items (order_id, product_id) 
    INCLUDE (quantity, unit_price, line_total);

-- 6. Order Items: Covering Index on Product ID for Aggregations
CREATE INDEX idx_items_product_aggregate ON fact_order_items (product_id) 
    INCLUDE (quantity, line_total);

-- 7. Shipments: Composite Index on Order & Warehouse
CREATE INDEX idx_shipments_order_wh ON fact_shipments (order_id, warehouse_id) 
    INCLUDE (carrier_code, shipping_cost, shipping_status);

-- 8. Shipments: Dispatched & Delivered Temporal Index
CREATE INDEX idx_shipments_dispatch_status ON fact_shipments (shipping_status, dispatched_at, delivered_at);

-- 9. Customers: Covering Index on State, Country & Enterprise Flag
CREATE INDEX idx_customers_geo_enterprise ON dim_customers (state_code, country_code, is_enterprise) 
    INCLUDE (customer_id, full_name, credit_limit);

-- 10. Products: Composite Index on Category & Subcategory
CREATE INDEX idx_products_category_sub ON dim_products (category, subcategory) 
    INCLUDE (product_id, retail_price, cost_price);

-- 11. Date Dimension: Calendar Year & Month Hierarchy Index
CREATE INDEX idx_date_year_month ON dim_date (calendar_year, month_number, date_key);

-- 12. Campaigns: Channel & Date Range Index
CREATE INDEX idx_campaigns_channel_dates ON dim_campaigns (channel_type, start_date, end_date) 
    INCLUDE (campaign_id, budget);
