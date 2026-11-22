# Data Flow Diagrams (DFD Level 0 & Level 1)

## 1. DFD Level 0: Context Diagram

The Level 0 Context Diagram depicts the high-level boundary of the data integration platform, showing the primary enterprise entities and the final analytical interfaces.

```mermaid
flowchart LR
    ERP["SAP ERP Billing<br/>(Invoices, Customers)"] -->|CSV / Windows-1252| SYS["Data Integration & Performance<br/>Optimization Platform"]
    CRM["Salesforce CRM<br/>(Accounts, Addresses)"] -->|NDJSON / UTF-8| SYS
    WEB["WebStore E-Commerce<br/>(Orders, Line Items)"] -->|CSV / Mixed Dates| SYS
    WMS["WMS Logistics Hub<br/>(Warehouses, Shipments)"] -->|TSV / Truncated Zips| SYS
    MKT["HubSpot Marketing<br/>(Campaigns, Budgets)"] -->|JSON / Metadata| SYS

    SYS -->|Unified Relational Warehouse| DWH[("Unified Data Warehouse<br/>(8 Tables, 6 Foreign Keys)")]
    SYS -->|Audit Trails & Quarantined Rows| QUA[("Quarantine Logs<br/>(data/quarantine/)")]
    DWH -->|Optimised Queries & EXPLAIN| BI["Executive Dashboards & Analysts<br/>(Avg Latency: 52ms)"]
```

---

## 2. DFD Level 1: Subsystem Data Flow Diagram

The Level 1 Diagram decomposes the platform into its four internal operational processes:
1. Ingestion & Pre-Processing
2. Validation & Quarantine Routing
3. Transformation & Data Cleansing
4. Warehouse Loading & Analytical Benchmarking

```mermaid
flowchart TD
    %% Source Inputs
    subgraph Sources["Enterprise Sources"]
        S1["SAP ERP Billing (CSV)"]
        S2["Salesforce CRM (NDJSON)"]
        S3["WebStore Transactions (CSV)"]
        S4["WMS Logistics (TSV)"]
        S5["HubSpot Campaigns (JSON)"]
    end

    %% Process 1: Ingestion
    subgraph P1["Process 1: Ingestion & Encoding Handling"]
        E1["Extractor: Windows-1252 to UTF-8"]
        E2["Extractor: NDJSON Stream Parser"]
        E3["Extractor: CSV Reader & Type Inference"]
        E4["Extractor: TSV Delimiter Parser"]
        E5["Extractor: JSON Deserializer"]
    end

    S1 --> E1
    S2 --> E2
    S3 --> E3
    S4 --> E4
    S5 --> E5

    %% Process 2: Validation Engine
    subgraph P2["Process 2: 14-Issue Validation Engine"]
        V_ENC["Issue 1: Encoding Transcoder"]
        V_DAT["Issue 2: Date Parser (Epoch, ISO, Slash)"]
        V_MAP["Issue 3: Legacy Schema Column Mapper"]
        V_CUR["Issue 4: Currency String Sanitizer"]
        V_PHO["Issue 5: Phone Standardizer (E.164)"]
        V_FK["Issue 6: Foreign Key Referential Verifier"]
        V_DUP["Issue 7: Business Key Deduplicator"]
        V_NUL["Issue 8: Mandatory Null Enforcer"]
        V_CAS["Issue 9: State/Country Case Normalizer"]
        V_FLT["Issue 10: Nested Payload Flattener"]
        V_BOL["Issue 11: Boolean Coercer ('Y'/'N'->bool)"]
        V_RND["Issue 12: Decimal Precision Quantizer"]
        V_ZIP["Issue 13: Postal Zero Padder ('7001'->'07001')"]
        V_RNG["Issue 14: Numeric Range Boundary Checker"]
    end

    E1 --> V_ENC --> V_MAP --> V_CUR --> V_PHO --> V_BOL
    E2 --> V_FLT --> V_CAS --> V_ZIP
    E3 --> V_DAT --> V_DUP --> V_NUL --> V_RND --> V_RNG
    E4 --> V_ZIP
    E5 --> V_MAP

    %% Quarantine Datastore
    Q_LOG[("Quarantine Audit Datastore<br/>data/quarantine/quarantine_audit_log.json")]
    V_FK -.->|Orphaned Child Rows| Q_LOG
    V_NUL -.->|Missing Mandatory Keys| Q_LOG
    V_RNG -.->|Negative Quantities| Q_LOG

    %% Process 3: Transformation
    subgraph P3["Process 3: Relational Transformation & Modeling"]
        T_CUST["Customer Synthesizer (dim_customers)"]
        T_PROD["Product Catalog (dim_products)"]
        T_WH["Warehouse Dimension (dim_warehouses)"]
        T_CAMP["Campaign Dimension (dim_campaigns)"]
        T_DATE["Calendar Generator (dim_date)"]
        T_ORD["Order Fact Pipeline (fact_orders)"]
        T_ITEM["Item Fact Pipeline (fact_order_items)"]
        T_SHIP["Shipment Fact Pipeline (fact_shipments)"]
    end

    V_PHO & V_ZIP & V_CAS --> T_CUST
    V_DAT & V_DUP --> T_ORD
    V_RND & V_RNG --> T_ITEM
    V_ZIP --> T_WH
    V_MAP --> T_CAMP

    %% Process 4: Loading
    subgraph P4["Process 4: High-Performance Bulk Load"]
        LOAD_DIM["Load Dimension Tables (FK Targets)"]
        LOAD_FACT["Load Fact Tables (FK Sources)"]
    end

    T_CUST & T_PROD & T_WH & T_CAMP & T_DATE --> LOAD_DIM
    T_ORD & T_ITEM & T_SHIP --> LOAD_FACT

    %% Warehouse Tables
    subgraph DWH["Unified PostgreSQL Data Warehouse (8 Tables)"]
        D_ALL[("dim_customers<br/>dim_products<br/>dim_warehouses<br/>dim_campaigns<br/>dim_date")]
        F_ALL[("fact_orders<br/>fact_order_items<br/>fact_shipments")]
    end

    LOAD_DIM --> D_ALL
    LOAD_FACT --> F_ALL

    %% Process 5: Query Optimization
    subgraph P5["Process 5: Benchmarking & EXPLAIN ANALYZE"]
        IDX["Composite B-Tree & Covering Indexes"]
        QUERIES["28 Analytical Queries (CTEs, Windows)"]
        BENCH["EXPLAIN ANALYZE Metric Reporter"]
    end

    D_ALL & F_ALL --> IDX
    IDX --> QUERIES
    QUERIES --> BENCH
    BENCH --> REP["Performance Benchmark Report<br/>380ms -> 52ms"]
```
