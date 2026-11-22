"""
Comprehensive Test Suite for 14 Integration Issues
Verifies that each issue is accurately detected, resolved, and audited.
"""
from datetime import datetime
import pandas as pd
import pytest
from src.validate.issues import IntegrationIssueCode
from src.validate.quarantine import QuarantineManager
from src.validate.validator import DataValidator

@pytest.fixture
def validator():
    qm = QuarantineManager()
    val = DataValidator(quarantine_mgr=qm)
    return val

def test_issue_01_encoding_conflict(validator):
    # Latin-1 / Windows-1252 bytes with accented names
    latin1_bytes = "René Müller".encode("windows-1252")
    res = validator.resolve_encoding(latin1_bytes, record_id="CUST-001")
    assert "René Müller" in res
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_01_ENCODING_CONFLICT in codes

def test_issue_02_datetime_parsing(validator):
    dt1 = validator.parse_datetime_flexible("1716123456", "ORD-1")
    assert isinstance(dt1, datetime)
    dt2 = validator.parse_datetime_flexible("10/24/2024 03:45 PM", "ORD-2")
    assert isinstance(dt2, datetime)
    assert dt2.month == 10 and dt2.day == 24
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_02_DATE_FORMAT_DISCREPANCY in codes

def test_issue_03_legacy_column_mapping(validator):
    df = pd.DataFrame({"cust_no": ["C-1"], "tx_val": [100.0]})
    res = validator.map_legacy_columns(df, {"cust_no": "customer_id", "tx_val": "total_amount"}, "SAP_ERP")
    assert "customer_id" in res.columns
    assert "total_amount" in res.columns
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_03_SCHEMA_DRIFT_COLUMN_MAPPING in codes

def test_issue_04_currency_cleaning(validator):
    val = validator.clean_currency_string("$12,450.50", "REC-1")
    assert val == 12450.50
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_04_NUMERIC_CURRENCY_STRING in codes

def test_issue_05_phone_standardization(validator):
    res = validator.standardize_phone("(555) 234-5678", "CUST-1")
    assert res == "+1-555-234-5678"
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_05_PHONE_STANDARDIZATION in codes

def test_issue_06_orphaned_foreign_keys(validator):
    df = pd.DataFrame({
        "item_id": ["I-1", "I-2"],
        "product_id": ["P-VALID", "P-ORPHAN"]
    })
    valid_products = {"P-VALID"}
    valid_df, orphans_df = validator.check_foreign_key_integrity(
        df, "product_id", valid_products, "WebStore", "item_id"
    )
    assert len(valid_df) == 1
    assert len(orphans_df) == 1
    assert orphans_df.iloc[0]["product_id"] == "P-ORPHAN"
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_06_ORPHANED_FOREIGN_KEYS in codes

def test_issue_07_duplicate_transactions(validator):
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-1", "ORD-2"],
        "amount": [50.0, 50.0, 75.0]
    })
    res = validator.deduplicate_records(df, ["order_id"], "WebStore")
    assert len(res) == 2
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_07_DUPLICATE_TRANSACTIONS in codes

def test_issue_08_mandatory_fields_null(validator):
    df = pd.DataFrame({
        "order_id": ["O-1", "O-2"],
        "customer_id": ["C-1", ""]
    })
    valid_df, invalid_df = validator.filter_null_mandatory(df, ["customer_id"], "WebStore", "order_id")
    assert len(valid_df) == 1
    assert len(invalid_df) == 1
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_08_NULL_MANDATORY_FIELDS in codes

def test_issue_09_case_inconsistency(validator):
    res = validator.normalize_state("california", "CUST-1")
    assert res == "CA"
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_09_CASE_INCONSISTENCY in codes

def test_issue_10_nested_json_flattening(validator):
    payload = [{
        "account_id": "ACC-1",
        "address": {"street": "100 Main St", "city": "Oakland", "state": "CA", "postal": "94601"}
    }]
    flattened = validator.flatten_crm_records(payload)
    assert "street" in flattened.columns
    assert flattened.iloc[0]["city"] == "Oakland"
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_10_NESTED_STRUCTURAL_MUTATION in codes

def test_issue_11_boolean_divergence(validator):
    assert validator.normalize_boolean("Y", "REC-1") is True
    assert validator.normalize_boolean("0", "REC-2") is False
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_11_BOOLEAN_DIVERGENCE in codes

def test_issue_12_float_precision(validator):
    val = validator.quantize_financial(19.9940001, "ITEM-1")
    assert val == 19.99
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_12_FLOAT_PRECISION_ROUNDING in codes

def test_issue_13_corrupted_postal_codes(validator):
    val = validator.normalize_postal_code("7001", "CUST-1")
    assert val == "07001"
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_13_CORRUPTED_POSTAL_CODES in codes

def test_issue_14_outlier_range_anomalies(validator):
    df = pd.DataFrame({
        "item_id": ["I-1", "I-2"],
        "quantity": [3, -2],
        "unit_price": [10.0, 15.0]
    })
    valid_df, invalid_df = validator.validate_order_item_ranges(df, "item_id")
    assert len(valid_df) == 1
    assert len(invalid_df) == 1
    codes = [r.issue_code for r in validator.qm.audit_log]
    assert IntegrationIssueCode.ISSUE_14_OUTLIER_RANGE_ANOMALIES in codes
