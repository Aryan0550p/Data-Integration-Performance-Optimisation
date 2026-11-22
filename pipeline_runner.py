"""
Master Pipeline Runner: End-to-End Enterprise Data Integration
Extracts from 5 enterprise systems, resolves 14 integration issues,
and loads into a unified 8-table relational data warehouse.
"""
import sys
import time
from tabulate import tabulate
from src.extract.extractors import EnterpriseExtractors
from src.load.db_session import reset_db
from src.load.loader import DatabaseLoader
from src.transform.transformers import EnterpriseTransformer
from src.utils.logger import logger
from src.validate.quarantine import QuarantineManager
from src.validate.validator import DataValidator

def run_integration_pipeline() -> dict:
    """Execute the end-to-end data integration and ETL pipeline."""
    total_start = time.time()
    logger.info("=================================================================")
    logger.info("Starting Enterprise Data Integration Pipeline")
    logger.info("=================================================================")

    # 1. Reset & Initialize Database Schema
    reset_db()

    # 2. Extract Data from 5 Source Systems
    extractors = EnterpriseExtractors()
    df_erp = extractors.extract_sap_erp()
    crm_records = extractors.extract_salesforce_crm()
    df_orders_raw, df_items_raw = extractors.extract_webstore_orders()
    df_wh_raw, df_ship_raw = extractors.extract_wms_logistics()
    df_camp_raw = extractors.extract_hubspot_campaigns()
    df_prod_raw = extractors.extract_master_products()

    # 3. Initialize Validation & Quarantine Engines
    quarantine_mgr = QuarantineManager()
    validator = DataValidator(quarantine_mgr=quarantine_mgr)
    transformer = EnterpriseTransformer(validator=validator)

    # 4. Transform Dimensions
    df_campaigns = transformer.transform_campaigns(df_camp_raw)
    df_products = transformer.transform_products(df_prod_raw)
    df_warehouses = transformer.transform_warehouses(df_wh_raw)
    df_date = transformer.transform_date_dimension()
    df_customers = transformer.transform_customers(df_erp, crm_records)

    # Valid key sets for referential integrity checks
    valid_cust_ids = set(df_customers["customer_id"])
    valid_camp_ids = set(df_campaigns["campaign_id"])
    valid_prod_ids = set(df_products["product_id"])
    valid_wh_ids = set(df_warehouses["warehouse_id"])

    # 5. Transform Facts (with Referential Integrity Cross-checks)
    df_orders = transformer.transform_orders(df_orders_raw, valid_cust_ids, valid_camp_ids)
    valid_order_ids = set(df_orders["order_id"])

    df_order_items = transformer.transform_order_items(df_items_raw, valid_order_ids, valid_prod_ids)
    df_shipments = transformer.transform_shipments(df_ship_raw, valid_order_ids, valid_wh_ids)

    # 6. Persist Quarantine Audit Logs
    audit_file = quarantine_mgr.persist_log()

    # 7. Load into Relational Data Warehouse
    tables_to_load = {
        "dim_customers": df_customers,
        "dim_products": df_products,
        "dim_warehouses": df_warehouses,
        "dim_campaigns": df_campaigns,
        "dim_date": df_date,
        "fact_orders": df_orders,
        "fact_order_items": df_order_items,
        "fact_shipments": df_shipments
    }

    loader = DatabaseLoader()
    load_summary = loader.load_all(tables_to_load)
    final_counts = loader.get_table_counts()

    total_duration = time.time() - total_start
    issue_counts = quarantine_mgr.get_summary_by_code()

    # 8. Print Executive Summary Dashboard
    print("\n" + "=" * 75)
    print("      ENTERPRISE DATA INTEGRATION & VALIDATION EXECUTION DASHBOARD")
    print("=" * 75)
    print(f"Total Pipeline Duration: {total_duration:.2f} seconds\n")

    print("[1] Unified Relational Warehouse Table Row Counts (8 Tables, 6 Foreign Keys):")
    counts_table = [[tbl, final_counts.get(tbl, 0)] for tbl in final_counts]
    print(tabulate(counts_table, headers=["Table Name", "Loaded Row Count"], tablefmt="github"))

    print("\n[2] Data Integration Issues Handled & Resolved (14 Issues Breakdown):")
    issues_table = [[code, cnt] for code, cnt in sorted(issue_counts.items())]
    print(tabulate(issues_table, headers=["Integration Issue Code", "Events Handled"], tablefmt="github"))
    print(f"Total Quality Events Handled: {sum(issue_counts.values()):,}")
    print(f"Quarantine Audit Log Path: {audit_file}\n" + "=" * 75)

    return {
        "duration_seconds": total_duration,
        "table_counts": final_counts,
        "issue_counts": issue_counts
    }

if __name__ == "__main__":
    run_integration_pipeline()
