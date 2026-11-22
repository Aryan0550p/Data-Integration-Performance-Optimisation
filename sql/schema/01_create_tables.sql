-- ============================================================================
-- Enterprise Unified Data Model (PostgreSQL DDL)
-- 8 Tables, 6 Foreign Keys
-- ============================================================================

-- Drop tables if existing (in reverse dependency order)
DROP TABLE IF EXISTS fact_shipments CASCADE;
DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_campaigns CASCADE;
DROP TABLE IF EXISTS dim_warehouses CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;

-- 1. Dimension: Customers
CREATE TABLE dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone_normalized VARCHAR(30),
    street_address VARCHAR(255),
    city VARCHAR(100),
    state_code VARCHAR(10),
    postal_code VARCHAR(20),
    country_code VARCHAR(10),
    credit_limit NUMERIC(12, 2) DEFAULT 0.00,
    is_enterprise BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dimension: Products
CREATE TABLE dim_products (
    product_id VARCHAR(50) PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    cost_price NUMERIC(10, 2) NOT NULL,
    retail_price NUMERIC(10, 2) NOT NULL,
    weight_kg NUMERIC(8, 2) DEFAULT 1.00,
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. Dimension: Warehouses
CREATE TABLE dim_warehouses (
    warehouse_id VARCHAR(50) PRIMARY KEY,
    warehouse_name VARCHAR(150) NOT NULL,
    warehouse_code VARCHAR(50) UNIQUE NOT NULL,
    facility_type VARCHAR(50) DEFAULT 'Distribution Center',
    capacity_sqft INTEGER DEFAULT 50000,
    city VARCHAR(100) NOT NULL,
    state_code VARCHAR(10) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country_code VARCHAR(10) DEFAULT 'US',
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. Dimension: Campaigns
CREATE TABLE dim_campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_name VARCHAR(150) NOT NULL,
    channel_type VARCHAR(50) NOT NULL,
    budget NUMERIC(12, 2) DEFAULT 0.00,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    target_region VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

-- 5. Dimension: Date
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY, -- Format: YYYYMMDD
    full_date DATE UNIQUE NOT NULL,
    day_of_week SMALLINT NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    day_of_month SMALLINT NOT NULL,
    day_of_year SMALLINT NOT NULL,
    week_of_year SMALLINT NOT NULL,
    month_number SMALLINT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    calendar_quarter SMALLINT NOT NULL,
    calendar_year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- 6. Fact: Orders (Contains FK1, FK2, FK3)
CREATE TABLE fact_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(50),
    order_date_key INTEGER NOT NULL,
    order_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    currency VARCHAR(5) DEFAULT 'USD',
    subtotal NUMERIC(12, 2) NOT NULL,
    tax_amount NUMERIC(12, 2) NOT NULL,
    shipping_amount NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(12, 2) DEFAULT 0.00,
    total_amount NUMERIC(12, 2) NOT NULL,
    
    -- Foreign Key 1: dim_customers
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) 
        REFERENCES dim_customers(customer_id) ON DELETE RESTRICT,
        
    -- Foreign Key 2: dim_campaigns
    CONSTRAINT fk_orders_campaign FOREIGN KEY (campaign_id) 
        REFERENCES dim_campaigns(campaign_id) ON DELETE SET NULL,
        
    -- Foreign Key 3: dim_date
    CONSTRAINT fk_orders_date FOREIGN KEY (order_date_key) 
        REFERENCES dim_date(date_key) ON DELETE RESTRICT
);

-- 7. Fact: Order Items (Contains FK4, FK5)
CREATE TABLE fact_order_items (
    order_item_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount_rate NUMERIC(5, 2) DEFAULT 0.00,
    line_total NUMERIC(12, 2) NOT NULL,
    
    -- Foreign Key 4: fact_orders
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) 
        REFERENCES fact_orders(order_id) ON DELETE CASCADE,
        
    -- Foreign Key 5: dim_products
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) 
        REFERENCES dim_products(product_id) ON DELETE RESTRICT
);

-- 8. Fact: Shipments (Contains FK6)
CREATE TABLE fact_shipments (
    shipment_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    warehouse_id VARCHAR(50) NOT NULL,
    carrier_code VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(100) UNIQUE NOT NULL,
    dispatched_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    shipping_cost NUMERIC(10, 2) DEFAULT 0.00,
    shipping_status VARCHAR(30) NOT NULL,
    
    -- Foreign Key 6: fact_orders
    CONSTRAINT fk_shipments_order FOREIGN KEY (order_id) 
        REFERENCES fact_orders(order_id) ON DELETE CASCADE,
        
    -- Additional Referential Integrity: dim_warehouses
    CONSTRAINT fk_shipments_warehouse FOREIGN KEY (warehouse_id)
        REFERENCES dim_warehouses(warehouse_id) ON DELETE RESTRICT
);
