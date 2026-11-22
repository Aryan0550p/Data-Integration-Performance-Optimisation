-- ============================================================================
-- Enterprise Unified Data Model (SQLite Compatible DDL)
-- 8 Tables, 6 Foreign Keys
-- ============================================================================
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_shipments;
DROP TABLE IF EXISTS fact_order_items;
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_campaigns;
DROP TABLE IF EXISTS dim_warehouses;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_customers;

-- 1. Dimension: Customers
CREATE TABLE dim_customers (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone_normalized TEXT,
    street_address TEXT,
    city TEXT,
    state_code TEXT,
    postal_code TEXT,
    country_code TEXT,
    credit_limit REAL DEFAULT 0.00,
    is_enterprise INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dimension: Products
CREATE TABLE dim_products (
    product_id TEXT PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    cost_price REAL NOT NULL,
    retail_price REAL NOT NULL,
    weight_kg REAL DEFAULT 1.00,
    is_active INTEGER DEFAULT 1
);

-- 3. Dimension: Warehouses
CREATE TABLE dim_warehouses (
    warehouse_id TEXT PRIMARY KEY,
    warehouse_name TEXT NOT NULL,
    warehouse_code TEXT UNIQUE NOT NULL,
    facility_type TEXT DEFAULT 'Distribution Center',
    capacity_sqft INTEGER DEFAULT 50000,
    city TEXT NOT NULL,
    state_code TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    country_code TEXT DEFAULT 'US',
    is_active INTEGER DEFAULT 1
);

-- 4. Dimension: Campaigns
CREATE TABLE dim_campaigns (
    campaign_id TEXT PRIMARY KEY,
    campaign_name TEXT NOT NULL,
    channel_type TEXT NOT NULL,
    budget REAL DEFAULT 0.00,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    utm_source TEXT,
    utm_medium TEXT,
    target_region TEXT,
    is_active INTEGER DEFAULT 1
);

-- 5. Dimension: Date
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT UNIQUE NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    calendar_quarter INTEGER NOT NULL,
    calendar_year INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL,
    is_holiday INTEGER DEFAULT 0
);

-- 6. Fact: Orders (FK1, FK2, FK3)
CREATE TABLE fact_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    campaign_id TEXT,
    order_date_key INTEGER NOT NULL,
    order_timestamp TEXT NOT NULL,
    order_status TEXT NOT NULL,
    currency TEXT DEFAULT 'USD',
    subtotal REAL NOT NULL,
    tax_amount REAL NOT NULL,
    shipping_amount REAL NOT NULL,
    discount_amount REAL DEFAULT 0.00,
    total_amount REAL NOT NULL,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id) ON DELETE RESTRICT,
    CONSTRAINT fk_orders_campaign FOREIGN KEY (campaign_id) REFERENCES dim_campaigns(campaign_id) ON DELETE SET NULL,
    CONSTRAINT fk_orders_date FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key) ON DELETE RESTRICT
);

-- 7. Fact: Order Items (FK4, FK5)
CREATE TABLE fact_order_items (
    order_item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    discount_rate REAL DEFAULT 0.00,
    line_total REAL NOT NULL,
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES fact_orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES dim_products(product_id) ON DELETE RESTRICT
);

-- 8. Fact: Shipments (FK6)
CREATE TABLE fact_shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    warehouse_id TEXT NOT NULL,
    carrier_code TEXT NOT NULL,
    tracking_number TEXT UNIQUE NOT NULL,
    dispatched_at TEXT,
    delivered_at TEXT,
    shipping_cost REAL DEFAULT 0.00,
    shipping_status TEXT NOT NULL,
    CONSTRAINT fk_shipments_order FOREIGN KEY (order_id) REFERENCES fact_orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_shipments_warehouse FOREIGN KEY (warehouse_id) REFERENCES dim_warehouses(warehouse_id) ON DELETE RESTRICT
);
