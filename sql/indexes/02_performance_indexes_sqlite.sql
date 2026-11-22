-- ============================================================================
-- Enterprise Performance Optimisation Indexes (SQLite Compatible)
-- Composite and Covering B-Tree Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON fact_orders (customer_id, order_date_key, total_amount, order_status);
CREATE INDEX IF NOT EXISTS idx_orders_date_status ON fact_orders (order_date_key, order_status, total_amount, subtotal);
CREATE INDEX IF NOT EXISTS idx_orders_campaign ON fact_orders (campaign_id) WHERE campaign_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_order_product ON fact_order_items (order_id, product_id, quantity, line_total);
CREATE INDEX IF NOT EXISTS idx_items_product_aggregate ON fact_order_items (product_id, quantity, line_total);
CREATE INDEX IF NOT EXISTS idx_shipments_order_wh ON fact_shipments (order_id, warehouse_id, shipping_status, shipping_cost);
CREATE INDEX IF NOT EXISTS idx_shipments_dispatch_status ON fact_shipments (shipping_status, dispatched_at, delivered_at);
CREATE INDEX IF NOT EXISTS idx_customers_geo_enterprise ON dim_customers (state_code, country_code, is_enterprise, credit_limit);
CREATE INDEX IF NOT EXISTS idx_products_category_sub ON dim_products (category, subcategory, product_id, retail_price);
CREATE INDEX IF NOT EXISTS idx_date_year_month ON dim_date (calendar_year, month_number, date_key);
CREATE INDEX IF NOT EXISTS idx_campaigns_channel ON dim_campaigns (channel_type, campaign_id, budget);
