"""
Modular Extractors for 5 Enterprise Source Systems
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd
from config.settings import RAW_DATA_DIR
from src.utils.logger import logger

class EnterpriseExtractors:
    """Extractors for files produced by the 5 enterprise systems."""

    def __init__(self, data_dir: Path = RAW_DATA_DIR):
        self.data_dir = data_dir

    def extract_sap_erp(self) -> pd.DataFrame:
        """Extract ERP billing data handling Windows-1252 encoding."""
        csv_path = self.data_dir / "sap_erp_billing.csv"
        logger.info(f"Extracting SAP ERP data from {csv_path.name}...")
        try:
            df = pd.read_csv(csv_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding="windows-1252")
        return df

    def extract_salesforce_crm(self) -> List[Dict[str, Any]]:
        """Extract Salesforce CRM records from NDJSON."""
        json_path = self.data_dir / "salesforce_crm.ndjson"
        logger.info(f"Extracting Salesforce CRM data from {json_path.name}...")
        records = []
        with open(json_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def extract_webstore_orders(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extract WebStore orders and line items."""
        orders_path = self.data_dir / "webstore_orders.csv"
        items_path = self.data_dir / "webstore_order_items.csv"
        logger.info(f"Extracting WebStore orders from {orders_path.name} and items from {items_path.name}...")
        df_orders = pd.read_csv(orders_path, dtype={"order_id": str, "customer_id": str, "campaign_id": str})
        df_items = pd.read_csv(items_path, dtype={"item_id": str, "order_id": str, "product_id": str})
        return df_orders, df_items

    def extract_wms_logistics(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extract WMS warehouses and shipments (TSV)."""
        wh_path = self.data_dir / "wms_warehouses.tsv"
        ship_path = self.data_dir / "wms_shipments.tsv"
        logger.info(f"Extracting WMS logistics from {wh_path.name} and {ship_path.name}...")
        df_wh = pd.read_csv(wh_path, sep="\t", dtype=str)
        df_ship = pd.read_csv(ship_path, sep="\t", dtype=str)
        return df_wh, df_ship

    def extract_hubspot_campaigns(self) -> pd.DataFrame:
        """Extract HubSpot marketing campaigns from JSON."""
        camp_path = self.data_dir / "hubspot_campaigns.json"
        logger.info(f"Extracting HubSpot campaigns from {camp_path.name}...")
        with open(camp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def extract_master_products(self) -> pd.DataFrame:
        """Extract master product catalog."""
        prod_path = self.data_dir / "master_products.csv"
        logger.info(f"Extracting Master Products from {prod_path.name}...")
        return pd.read_csv(prod_path)
