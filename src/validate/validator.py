"""
Data Validation and Cleansing Engine resolving 14 Integration Issues
"""
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd
from src.validate.issues import IntegrationIssueCode, IntegrationIssueRecord
from src.validate.quarantine import QuarantineManager

STATE_MAPPING = {
    "california": "CA", "texas": "TX", "new york": "NY", "florida": "FL",
    "illinois": "IL", "pennsylvania": "PA", "ohio": "OH", "georgia": "GA",
    "north carolina": "NC", "michigan": "MI", "washington": "WA"
}

COUNTRY_MAPPING = {
    "usa": "US", "united states": "US", "u.s.a.": "US", "us": "US",
    "canada": "CA", "uk": "GB", "germany": "DE", "france": "FR"
}

class DataValidator:
    """Core validator implementing resolution logic for all 14 integration issues."""

    def __init__(self, quarantine_mgr: Optional[QuarantineManager] = None):
        self.qm = quarantine_mgr or QuarantineManager()

    # Issue 1: Encoding Conflict
    def resolve_encoding(self, text: Any, record_id: str = "UNKNOWN") -> str:
        if text is None or pd.isna(text):
            return ""
        if isinstance(text, bytes):
            try:
                val = text.decode("utf-8")
            except UnicodeDecodeError:
                val = text.decode("windows-1252", errors="replace")
                self.qm.record_issue(IntegrationIssueRecord(
                    issue_code=IntegrationIssueCode.ISSUE_01_ENCODING_CONFLICT,
                    source_system="SAP_ERP",
                    record_identifier=record_id,
                    field_name="text",
                    raw_value=str(text[:20]),
                    resolved_value=val[:20],
                    action_taken="TRANSFORMED",
                    description="Transcoded Windows-1252 bytes to UTF-8"
                ))
            return val
        s = str(text).strip()
        return s

    # Issue 2: Date Format Discrepancies
    def parse_datetime_flexible(self, val: Any, record_id: str = "UNKNOWN") -> Optional[datetime]:
        if val is None or pd.isna(val) or str(val).strip() == "":
            return None
        s = str(val).strip()

        # Unix epoch
        if s.isdigit() and len(s) in [10, 13]:
            ts = int(s) if len(s) == 10 else int(s) / 1000.0
            dt = datetime.fromtimestamp(ts, timezone.utc).replace(tzinfo=None)
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_02_DATE_FORMAT_DISCREPANCY,
                source_system="WebStore",
                record_identifier=record_id,
                field_name="timestamp",
                raw_value=s,
                resolved_value=dt.isoformat(),
                action_taken="TRANSFORMED",
                description="Parsed Unix timestamp epoch to UTC datetime"
            ))
            return dt

        patterns = [
            ("%Y-%m-%d %H:%M:%S", False),
            ("%Y-%m-%d", False),
            ("%m/%d/%Y %I:%M %p", True),
            ("%m/%d/%Y %H:%M", True),
            ("%d-%m-%Y %H:%M:%S", True),
            ("%Y-%m-%dT%H:%M:%S", False),
        ]
        for pat, is_alt in patterns:
            try:
                dt = datetime.strptime(s, pat)
                if is_alt:
                    self.qm.record_issue(IntegrationIssueRecord(
                        issue_code=IntegrationIssueCode.ISSUE_02_DATE_FORMAT_DISCREPANCY,
                        source_system="WebStore",
                        record_identifier=record_id,
                        field_name="timestamp",
                        raw_value=s,
                        resolved_value=dt.isoformat(),
                        action_taken="TRANSFORMED",
                        description=f"Standardized date format from '{pat}'"
                    ))
                return dt
            except ValueError:
                continue

        # Pandas parser fallback
        try:
            dt = pd.to_datetime(s).to_pydatetime()
            return dt
        except Exception:
            return None

    # Issue 3: Schema Drift & Legacy Column Mapping
    def map_legacy_columns(self, df: pd.DataFrame, mapping: Dict[str, str], source_name: str) -> pd.DataFrame:
        renamed = {}
        for old_col, new_col in mapping.items():
            if old_col in df.columns:
                renamed[old_col] = new_col
                self.qm.record_issue(IntegrationIssueRecord(
                    issue_code=IntegrationIssueCode.ISSUE_03_SCHEMA_DRIFT_COLUMN_MAPPING,
                    source_system=source_name,
                    record_identifier="HEADER",
                    field_name=old_col,
                    raw_value=old_col,
                    resolved_value=new_col,
                    action_taken="TRANSFORMED",
                    description=f"Mapped legacy source column '{old_col}' -> '{new_col}'"
                ))
        return df.rename(columns=renamed)

    # Issue 4: Numeric Currency String Parsing
    def clean_currency_string(self, val: Any, record_id: str = "UNKNOWN") -> float:
        if val is None or pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        cleaned = re.sub(r"[^\d.-]", "", s)
        try:
            parsed = float(cleaned) if cleaned else 0.0
            if "$" in s or "," in s:
                self.qm.record_issue(IntegrationIssueRecord(
                    issue_code=IntegrationIssueCode.ISSUE_04_NUMERIC_CURRENCY_STRING,
                    source_system="SAP_ERP",
                    record_identifier=record_id,
                    field_name="credit_limit",
                    raw_value=s,
                    resolved_value=parsed,
                    action_taken="TRANSFORMED",
                    description="Sanitized formatted currency string to numeric float"
                ))
            return parsed
        except ValueError:
            return 0.0

    # Issue 5: Phone Number Standardization (E.164)
    def standardize_phone(self, val: Any, record_id: str = "UNKNOWN") -> str:
        if val is None or pd.isna(val):
            return ""
        s = str(val).strip()
        digits = re.sub(r"\D", "", s)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) == 10:
            formatted = f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            if s != formatted:
                self.qm.record_issue(IntegrationIssueRecord(
                    issue_code=IntegrationIssueCode.ISSUE_05_PHONE_STANDARDIZATION,
                    source_system="Enterprise",
                    record_identifier=record_id,
                    field_name="phone",
                    raw_value=s,
                    resolved_value=formatted,
                    action_taken="TRANSFORMED",
                    description="Normalized disparate phone format to standard format"
                ))
            return formatted
        return s

    # Issue 6: Orphaned Foreign Keys Detection & Quarantine
    def check_foreign_key_integrity(
        self,
        df: pd.DataFrame,
        fk_column: str,
        valid_parent_ids: Set[str],
        source_name: str,
        id_column: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        mask_valid = df[fk_column].isin(valid_parent_ids) | df[fk_column].isna() | (df[fk_column] == "")
        valid_df = df[mask_valid].copy()
        orphans_df = df[~mask_valid].copy()

        for _, row in orphans_df.iterrows():
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_06_ORPHANED_FOREIGN_KEYS,
                source_system=source_name,
                record_identifier=str(row[id_column]),
                field_name=fk_column,
                raw_value=str(row[fk_column]),
                resolved_value=None,
                action_taken="QUARANTINED",
                description=f"Foreign key '{fk_column}' references non-existent parent ID"
            ))
        return valid_df, orphans_df

    # Issue 7: Duplicate Primary/Transaction Key Deduplication
    def deduplicate_records(self, df: pd.DataFrame, key_columns: List[str], source_name: str) -> pd.DataFrame:
        dups_mask = df.duplicated(subset=key_columns, keep="first")
        num_dups = dups_mask.sum()
        if num_dups > 0:
            for _, row in df[dups_mask].iterrows():
                self.qm.record_issue(IntegrationIssueRecord(
                    issue_code=IntegrationIssueCode.ISSUE_07_DUPLICATE_TRANSACTIONS,
                    source_system=source_name,
                    record_identifier=str(row[key_columns[0]]),
                    field_name=key_columns[0],
                    raw_value=str(row[key_columns[0]]),
                    resolved_value=None,
                    action_taken="DEDUPLICATED",
                    description="Identified and dropped duplicate transaction record"
                ))
        return df.drop_duplicates(subset=key_columns, keep="first").copy()

    # Issue 8: Mandatory Field Null Enforcement
    def filter_null_mandatory(
        self,
        df: pd.DataFrame,
        mandatory_columns: List[str],
        source_name: str,
        id_column: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        valid_mask = pd.Series(True, index=df.index)
        for col in mandatory_columns:
            valid_mask &= df[col].notna() & (df[col].astype(str).str.strip() != "")

        valid_df = df[valid_mask].copy()
        invalid_df = df[~valid_mask].copy()

        for _, row in invalid_df.iterrows():
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_08_NULL_MANDATORY_FIELDS,
                source_system=source_name,
                record_identifier=str(row.get(id_column, "UNKNOWN")),
                field_name=",".join(mandatory_columns),
                raw_value="NULL/EMPTY",
                resolved_value=None,
                action_taken="QUARANTINED",
                description="Mandatory business field is missing or empty"
            ))
        return valid_df, invalid_df

    # Issue 9: State/Country Case Standardization
    def normalize_state(self, val: Any, record_id: str = "UNKNOWN") -> str:
        if val is None or pd.isna(val):
            return "UNKNOWN"
        s = str(val).strip().lower()
        if s in STATE_MAPPING:
            code = STATE_MAPPING[s]
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_09_CASE_INCONSISTENCY,
                source_system="Salesforce_CRM",
                record_identifier=record_id,
                field_name="state",
                raw_value=val,
                resolved_value=code,
                action_taken="TRANSFORMED",
                description=f"Standardized state name '{val}' to postal code '{code}'"
            ))
            return code
        return str(val).strip().upper()[:10]

    def normalize_country(self, val: Any, record_id: str = "UNKNOWN") -> str:
        if val is None or pd.isna(val):
            return "US"
        s = str(val).strip().lower()
        if s in COUNTRY_MAPPING:
            return COUNTRY_MAPPING[s]
        return str(val).strip().upper()[:10]

    # Issue 10: Nested JSON Flattening
    def flatten_crm_records(self, crm_list: List[Dict[str, Any]]) -> pd.DataFrame:
        flattened = []
        for item in crm_list:
            addr = item.get("address", {}) or {}
            rec = {
                "account_id": item.get("account_id"),
                "account_name": item.get("account_name"),
                "contact_email": item.get("contact_email"),
                "primary_phone": item.get("primary_phone"),
                "street": addr.get("street", ""),
                "city": addr.get("city", ""),
                "state": addr.get("state", ""),
                "postal": addr.get("postal", ""),
                "country": addr.get("country", ""),
                "is_enterprise": item.get("is_enterprise", False),
                "created_at": item.get("created_at")
            }
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_10_NESTED_STRUCTURAL_MUTATION,
                source_system="Salesforce_CRM",
                record_identifier=str(item.get("account_id")),
                field_name="address",
                raw_value="JSON_OBJECT",
                resolved_value="FLATTENED_COLUMNS",
                action_taken="TRANSFORMED",
                description="Extracted nested JSON address object into relational columns"
            ))
            flattened.append(rec)
        return pd.DataFrame(flattened)

    # Issue 11: Boolean Representation Divergence
    def normalize_boolean(self, val: Any, record_id: str = "UNKNOWN") -> bool:
        if val is None or pd.isna(val):
            return False
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        is_true = s in ["y", "yes", "1", "t", "true"]
        if s in ["y", "n", "1", "0", "t", "f"]:
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_11_BOOLEAN_DIVERGENCE,
                source_system="SAP_ERP",
                record_identifier=record_id,
                field_name="is_enterprise",
                raw_value=val,
                resolved_value=is_true,
                action_taken="TRANSFORMED",
                description=f"Normalized divergent boolean representation '{val}' -> {is_true}"
            ))
        return is_true

    # Issue 12: Float Precision & Financial Rounding
    def quantize_financial(self, val: Any, record_id: str = "UNKNOWN") -> float:
        if val is None or pd.isna(val):
            return 0.00
        try:
            d = Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            res = float(d)
            if len(str(val).split(".")[-1]) > 2:
                self.qm.record_issue(IntegrationIssueRecord(
                    issue_code=IntegrationIssueCode.ISSUE_12_FLOAT_PRECISION_ROUNDING,
                    source_system="WebStore",
                    record_identifier=record_id,
                    field_name="line_total",
                    raw_value=val,
                    resolved_value=res,
                    action_taken="TRANSFORMED",
                    description="Standardized float precision to 2 decimal places"
                ))
            return res
        except Exception:
            return 0.00

    # Issue 13: Corrupted / Truncated Postal Codes
    def normalize_postal_code(self, val: Any, record_id: str = "UNKNOWN") -> str:
        if val is None or pd.isna(val):
            return ""
        s = str(val).strip()
        if s.isdigit() and len(s) == 4:
            padded = s.zfill(5)
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_13_CORRUPTED_POSTAL_CODES,
                source_system="CRM/Logistics",
                record_identifier=record_id,
                field_name="postal_code",
                raw_value=s,
                resolved_value=padded,
                action_taken="PADDED",
                description="Padded 4-digit truncated postal code with leading zero"
            ))
            return padded
        return s[:20]

    # Issue 14: Out-of-Range Outliers & Corrupted Metrics
    def validate_order_item_ranges(
        self,
        df: pd.DataFrame,
        id_column: str = "item_id"
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        valid_mask = (df["quantity"] > 0) & (df["unit_price"] >= 0.0)
        valid_df = df[valid_mask].copy()
        invalid_df = df[~valid_mask].copy()

        for _, row in invalid_df.iterrows():
            self.qm.record_issue(IntegrationIssueRecord(
                issue_code=IntegrationIssueCode.ISSUE_14_OUTLIER_RANGE_ANOMALIES,
                source_system="WebStore",
                record_identifier=str(row[id_column]),
                field_name="quantity",
                raw_value=row["quantity"],
                resolved_value=None,
                action_taken="QUARANTINED",
                description=f"Negative or invalid quantity ({row['quantity']}) quarantined"
            ))
        return valid_df, invalid_df
