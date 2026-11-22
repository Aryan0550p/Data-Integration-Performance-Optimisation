# Unified Data Model: Entity-Relationship Diagram (ERD)

## 1. Schema Specifications
- **Architecture**: Kimball Dimensional Star Schema / 3NF Warehouse Model
- **Total Tables**: 8 Tables (5 Dimension Tables, 3 Fact Tables)
- **Total Relational Foreign Keys**: 6 Primary Explicit Foreign Key Constraints
- **Database Engine**: PostgreSQL 17 (with dialect-compatible SQLite 3 mode)

---

## 2. Entity-Relationship Diagram (Mermaid)

```mermaid
erDiagram
    dim_customers ||--o{ fact_orders : "places (FK1)"
    dim_campaigns ||--o{ fact_orders : "attributes (FK2)"
    dim_date ||--o{ fact_orders : "occurs_on (FK3)"
    fact_orders ||--|{ fact_order_items : "contains (FK4)"
    dim_products ||--o{ fact_order_items : "identifies (FK5)"
    fact_orders ||--o| fact_shipments : "fulfills (FK6)"
    dim_warehouses ||--o{ fact_shipments : "dispatches_from"

    dim_customers {
        varchar customer_id PK "Unique Customer Business Identifier"
        varchar first_name "First Name"
        varchar last_name "Last Name"
        varchar full_name "Full Composite Name"
        varchar email "Contact Email Address"
        varchar phone_normalized "Standardized E.164 Telephone"
        varchar street_address "Billing Street Address"
        varchar city "City"
        varchar state_code "2-Letter State Code"
        varchar postal_code "5-Digit Padded Postal Code"
        varchar country_code "ISO Country Code"
        numeric credit_limit "Approved Credit Limit"
        boolean is_enterprise "Enterprise Account Flag"
        timestamp created_at "Account Creation Timestamp"
    }

    dim_products {
        varchar product_id PK "Unique Product Identifier"
        varchar sku UK "Unique Stock Keeping Unit"
        varchar product_name "Product Catalog Name"
        varchar category "Primary Merchandising Category"
        varchar subcategory "Specialized Subcategory"
        numeric cost_price "Unit Wholesale Cost Price"
        numeric retail_price "Unit MSRP Retail Price"
        numeric weight_kg "Unit Weight in Kilograms"
        boolean is_active "Active Product Catalog Flag"
    }

    dim_warehouses {
        varchar warehouse_id PK "Warehouse Facility Identifier"
        varchar warehouse_name "Logistics Center Name"
        varchar warehouse_code UK "Unique Logistics Hub Code"
        varchar facility_type "Fulfillment / Cold Storage / Cross-Dock"
        integer capacity_sqft "Total Facility Square Footage"
        varchar city "Facility City"
        varchar state_code "Facility State Code"
        varchar postal_code "Facility Postal Code"
        varchar country_code "Facility Country Code"
        boolean is_active "Active Facility Status Flag"
    }

    dim_campaigns {
        varchar campaign_id PK "Marketing Campaign Identifier"
        varchar campaign_name "Marketing Campaign Name"
        varchar channel_type "Paid Search / Social / Email / Affiliate"
        numeric budget "Total Campaign Budget Allocation"
        date start_date "Campaign Flight Start Date"
        date end_date "Campaign Flight End Date"
        varchar utm_source "Marketing Attribution UTM Source"
        varchar utm_medium "Marketing Attribution UTM Medium"
        varchar target_region "Target Geographic Region"
        boolean is_active "Active Campaign Flight Status"
    }

    dim_date {
        integer date_key PK "Calendar Date Key (YYYYMMDD)"
        date full_date UK "Exact Calendar Date"
        smallint day_of_week "Day of Week (1=Monday, 7=Sunday)"
        varchar day_name "Name of Day (Monday..Sunday)"
        smallint day_of_month "Day of Calendar Month (1..31)"
        smallint day_of_year "Day of Calendar Year (1..366)"
        smallint week_of_year "ISO Week of Year (1..53)"
        smallint month_number "Calendar Month (1..12)"
        varchar month_name "Name of Month (January..December)"
        smallint calendar_quarter "Calendar Quarter (1..4)"
        integer calendar_year "Calendar Year (e.g. 2024, 2025)"
        boolean is_weekend "Weekend Flag"
        boolean is_holiday "Federal Holiday Flag"
    }

    fact_orders {
        varchar order_id PK "Unique Transaction Order ID"
        varchar customer_id FK "FK1: References dim_customers"
        varchar campaign_id FK "FK2: References dim_campaigns"
        integer order_date_key FK "FK3: References dim_date"
        timestamp order_timestamp "Transaction Placement Timestamp"
        varchar order_status "COMPLETED / SHIPPED / PROCESSING"
        varchar currency "ISO Currency Code (USD)"
        numeric subtotal "Order Subtotal Before Tax/Shipping"
        numeric tax_amount "Total Sales Tax"
        numeric shipping_amount "Total Shipping & Handling"
        numeric discount_amount "Promotional Discount Applied"
        numeric total_amount "Final Billed Order Total"
    }

    fact_order_items {
        varchar order_item_id PK "Unique Line Item Identifier"
        varchar order_id FK "FK4: References fact_orders"
        varchar product_id FK "FK5: References dim_products"
        integer quantity "Purchased Units (Check > 0)"
        numeric unit_price "Unit Selling Price (Check >= 0)"
        numeric discount_rate "Line Item Discount Rate (0.00..1.00)"
        numeric line_total "Final Billed Item Line Total"
    }

    fact_shipments {
        varchar shipment_id PK "Unique Shipment Parcel Identifier"
        varchar order_id FK "FK6: References fact_orders"
        varchar warehouse_id FK "References dim_warehouses"
        varchar carrier_code "UPS / FedEx / USPS / DHL"
        varchar tracking_number UK "Unique Carrier Tracking Barcode"
        timestamp dispatched_at "Carrier Pickup Timestamp"
        timestamp delivered_at "Customer Delivery Timestamp"
        numeric shipping_cost "Carrier Freight Cost"
        varchar shipping_status "DELIVERED / IN_TRANSIT"
    }
```

---

## 3. Explicit Foreign Key Constraint Directory

| Constraint Name | Source Table | Constrained Column | Target Table | Referenced Column | Referential Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **fk_orders_customer** (FK1) | `fact_orders` | `customer_id` | `dim_customers` | `customer_id` | `ON DELETE RESTRICT` |
| **fk_orders_campaign** (FK2) | `fact_orders` | `campaign_id` | `dim_campaigns` | `campaign_id` | `ON DELETE SET NULL` |
| **fk_orders_date** (FK3) | `fact_orders` | `order_date_key` | `dim_date` | `date_key` | `ON DELETE RESTRICT` |
| **fk_items_order** (FK4) | `fact_order_items` | `order_id` | `fact_orders` | `order_id` | `ON DELETE CASCADE` |
| **fk_items_product** (FK5) | `fact_order_items` | `product_id` | `dim_products` | `product_id` | `ON DELETE RESTRICT` |
| **fk_shipments_order** (FK6) | `fact_shipments` | `order_id` | `fact_orders` | `order_id` | `ON DELETE CASCADE` |
| **fk_shipments_warehouse** | `fact_shipments` | `warehouse_id` | `dim_warehouses` | `warehouse_id` | `ON DELETE RESTRICT` |
