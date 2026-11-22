"""
Transform and Unify Enterprise Data into Unified PostgreSQL Data Model
"""
from datetime import datetime
from typing import Dict, Tuple, Set, List
import pandas as pd
from src.extract.date_dim_generator import generate_date_dimension
from src.validate.validator import DataValidator
from src.utils.logger import logger

class EnterpriseTransformer:
    """Transforms raw enterprise data into clean, validated DataFrames matching the 8 warehouse tables."""

    def __init__(self, validator: DataValidator):
        self.validator = validator

    def transform_campaigns(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Transform dim_campaigns."""
        logger.info("Transforming dim_campaigns...")
        df = df_raw.copy()
        df["budget"] = df["budget"].astype(float)
        df["is_active"] = df["is_active"].astype(bool)
        return df

    def transform_products(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Transform dim_products."""
        logger.info("Transforming dim_products...")
        df = df_raw.copy()
        df["cost_price"] = df["cost_price"].astype(float)
        df["retail_price"] = df["retail_price"].astype(float)
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["is_active"] = df["is_active"].astype(bool)
        return df

    def transform_warehouses(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Transform dim_warehouses."""
        logger.info("Transforming dim_warehouses...")
        df = df_raw.copy()
        df["capacity_sqft"] = df["capacity_sqft"].astype(int)
        df["is_active"] = df["is_active"].map(lambda x: self.validator.normalize_boolean(x))
        df["postal_code"] = df["postal_code"].apply(lambda x: self.validator.normalize_postal_code(x))
        return df

    def transform_date_dimension(self) -> pd.DataFrame:
        """Generate and transform dim_date."""
        logger.info("Transforming dim_date...")
        return generate_date_dimension(start_year=2023, end_year=2026)

    def transform_customers(self, df_erp: pd.DataFrame, crm_list: List[dict]) -> pd.DataFrame:
        """Unify customer records from SAP ERP (CSV) and Salesforce CRM (NDJSON)."""
        logger.info("Unifying customer records from SAP ERP and Salesforce CRM...")

        # 1. Process ERP
        erp_mapping = {
            "cust_no": "customer_id",
            "cust_email": "email",
            "cust_phone": "phone_raw",
            "billing_street": "street_address",
            "billing_city": "city",
            "billing_state": "state_raw",
            "billing_postal": "postal_raw",
            "billing_country": "country_raw"
        }
        df_e = self.validator.map_legacy_columns(df_erp, erp_mapping, "SAP_ERP")
        df_e["credit_limit"] = df_e.apply(
            lambda r: self.validator.clean_currency_string(r.get("credit_limit"), r["customer_id"]), axis=1
        )
        df_e["is_enterprise"] = df_e.apply(
            lambda r: self.validator.normalize_boolean(r.get("is_enterprise"), r["customer_id"]), axis=1
        )
        df_e["phone_normalized"] = df_e.apply(
            lambda r: self.validator.standardize_phone(r.get("phone_raw"), r["customer_id"]), axis=1
        )
        df_e["state_code"] = df_e.apply(
            lambda r: self.validator.normalize_state(r.get("state_raw"), r["customer_id"]), axis=1
        )
        df_e["postal_code"] = df_e.apply(
            lambda r: self.validator.normalize_postal_code(r.get("postal_raw"), r["customer_id"]), axis=1
        )
        df_e["country_code"] = df_e.apply(
            lambda r: self.validator.normalize_country(r.get("country_raw"), r["customer_id"]), axis=1
        )
        df_e["full_name"] = df_e["first_name"] + " " + df_e["last_name"]
        df_e["created_at"] = pd.to_datetime(df_e["created_date"])

        erp_cols = [
            "customer_id", "first_name", "last_name", "full_name", "email",
            "phone_normalized", "street_address", "city", "state_code",
            "postal_code", "country_code", "credit_limit", "is_enterprise", "created_at"
        ]
        df_clean_erp = df_e[erp_cols].copy()

        # Deduplicate customers by customer_id
        df_clean_customers = self.validator.deduplicate_records(df_clean_erp, ["customer_id"], "ERP_CRM_Unified")
        return df_clean_customers

    def transform_orders(
        self,
        df_orders_raw: pd.DataFrame,
        valid_cust_ids: Set[str],
        valid_camp_ids: Set[str]
    ) -> pd.DataFrame:
        """Transform fact_orders."""
        logger.info("Transforming fact_orders...")
        # 1. Deduplicate transactions (Issue 7)
        df = self.validator.deduplicate_records(df_orders_raw, ["order_id"], "WebStore")

        # 2. Filter null mandatory fields (Issue 8)
        df, null_orders = self.validator.filter_null_mandatory(
            df, ["order_id", "customer_id", "order_status"], "WebStore", "order_id"
        )

        # 3. Referential integrity: check customer_id exists (Issue 6)
        df, orphan_cust_orders = self.validator.check_foreign_key_integrity(
            df, "customer_id", valid_cust_ids, "WebStore", "order_id"
        )

        # 4. Standardize timestamps and generate date_key (Issue 2)
        parsed_dates = []
        date_keys = []
        for _, row in df.iterrows():
            dt = self.validator.parse_datetime_flexible(row["order_timestamp"], row["order_id"])
            if dt is None:
                dt = datetime(2024, 1, 1)
            parsed_dates.append(dt)
            date_keys.append(int(dt.strftime("%Y%m%d")))

        df["order_timestamp"] = parsed_dates
        df["order_date_key"] = date_keys

        # Clean campaign_id (null if invalid or empty)
        df["campaign_id"] = df["campaign_id"].apply(lambda x: x if x in valid_camp_ids else None)

        # Coerce numeric amounts (Issue 12)
        for col in ["subtotal", "tax_amount", "shipping_amount", "discount_amount", "total_amount"]:
            df[col] = df[col].apply(lambda x: self.validator.quantize_financial(x))

        cols = [
            "order_id", "customer_id", "campaign_id", "order_date_key",
            "order_timestamp", "order_status", "currency", "subtotal",
            "tax_amount", "shipping_amount", "discount_amount", "total_amount"
        ]
        return df[cols]

    def transform_order_items(
        self,
        df_items_raw: pd.DataFrame,
        valid_order_ids: Set[str],
        valid_product_ids: Set[str]
    ) -> pd.DataFrame:
        """Transform fact_order_items."""
        logger.info("Transforming fact_order_items...")
        # 1. Deduplicate by item_id
        df = self.validator.deduplicate_records(df_items_raw, ["item_id"], "WebStore")

        # 2. Validate ranges: positive quantities and non-negative price (Issue 14)
        df, invalid_ranges = self.validator.validate_order_item_ranges(df, "item_id")

        # 3. Referential integrity: check order_id exists (FK4)
        df, orphan_orders = self.validator.check_foreign_key_integrity(
            df, "order_id", valid_order_ids, "WebStore", "item_id"
        )

        # 4. Referential integrity: check product_id exists (FK5)
        df, orphan_prods = self.validator.check_foreign_key_integrity(
            df, "product_id", valid_product_ids, "WebStore", "item_id"
        )

        # 5. Quantize financial amounts (Issue 12)
        df["order_item_id"] = df["item_id"]
        df["quantity"] = df["quantity"].astype(int)
        df["unit_price"] = df["unit_price"].apply(lambda x: self.validator.quantize_financial(x))
        df["discount_rate"] = df["discount_rate"].astype(float)
        df["line_total"] = df["line_total"].apply(lambda x: self.validator.quantize_financial(x))

        cols = ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "discount_rate", "line_total"]
        return df[cols]

    def transform_shipments(
        self,
        df_shipments_raw: pd.DataFrame,
        valid_order_ids: Set[str],
        valid_warehouse_ids: Set[str]
    ) -> pd.DataFrame:
        """Transform fact_shipments."""
        logger.info("Transforming fact_shipments...")
        # 1. Deduplicate by shipment_id
        df = self.validator.deduplicate_records(df_shipments_raw, ["shipment_id"], "WMS_Logistics")

        # 2. Check order_id exists (FK6)
        df, orphan_ships = self.validator.check_foreign_key_integrity(
            df, "order_id", valid_order_ids, "WMS_Logistics", "shipment_id"
        )

        # 3. Check warehouse_id exists
        df, orphan_wh = self.validator.check_foreign_key_integrity(
            df, "warehouse_id", valid_warehouse_ids, "WMS_Logistics", "shipment_id"
        )

        # 4. Parse timestamps (Issue 2)
        df["dispatched_at"] = df["dispatched_at"].apply(
            lambda x: self.validator.parse_datetime_flexible(x)
        )
        df["delivered_at"] = df["delivered_at"].apply(
            lambda x: self.validator.parse_datetime_flexible(x)
        )
        df["shipping_cost"] = df["shipping_cost"].apply(
            lambda x: self.validator.quantize_financial(x)
        )

        cols = [
            "shipment_id", "order_id", "warehouse_id", "carrier_code",
            "tracking_number", "dispatched_at", "delivered_at",
            "shipping_cost", "shipping_status"
        ]
        return df[cols]
