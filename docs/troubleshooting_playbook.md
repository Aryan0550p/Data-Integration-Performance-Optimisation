# Integration Troubleshooting & Data Validation Playbook

## 1. Overview
During enterprise data integration from multiple upstream source systems, data quality issues inevitably arise. This playbook documents the **14 specific integration issues** encountered across the 5 enterprise systems, detailing their **root causes**, **detection logic**, **resolution strategies**, and **quarantine policies**.

---

## 2. Directory of 14 Resolved Integration Issues

### Issue 1: Character Encoding Conflict (`ISSUE_01_ENCODING_CONFLICT`)
- **Source System**: SAP ERP Billing (`sap_erp_billing.csv`).
- **Root Cause**: Upstream legacy billing exports use Windows-1252 / ISO-8859-1 encoding. European client names containing diacritics and umlauts (`René`, `Müller`, `François`, `Élodie`) produce byte decode exceptions when ingested by modern UTF-8 pipelines.
- **Detection Logic**: Byte-sequence decode attempt against standard UTF-8; catches `UnicodeDecodeError`.
- **Resolution Strategy**: Dynamic fallback decoder to `windows-1252` with error replacement, followed by NFC Unicode normalization.
- **Auditing**: Logged with transformed original byte string and transcoded UTF-8 string.

### Issue 2: Date/Timestamp Parsing Discrepancy (`ISSUE_02_DATE_FORMAT_DISCREPANCY`)
- **Source System**: WebStore E-Commerce transactions (`webstore_orders.csv`).
- **Root Cause**: Heterogeneous API gateways and microservices emit dates in competing formats: ISO-8601 (`YYYY-MM-DD HH:MM:SS`), US slash notation (`MM/DD/YYYY HH:MM AM/PM`), European hyphen notation (`DD-MM-YYYY HH:MM:SS`), and 10/13-digit Unix epoch timestamps.
- **Detection Logic**: Regex inspection and multi-stage format pattern matching.
- **Resolution Strategy**: Flexible parser converting epochs and strings to UTC `datetime` objects and deriving an integer surrogate date key `YYYYMMDD` for zero-cost join against `dim_date`.
- **Auditing**: Raw date string and ISO-8601 output logged.

### Issue 3: Schema Drift & Legacy Column Drift (`ISSUE_03_SCHEMA_DRIFT_COLUMN_MAPPING`)
- **Source System**: SAP ERP (`sap_erp_billing.csv`).
- **Root Cause**: Mainframe ERP table exports employ legacy abbreviation naming conventions (`cust_no`, `tx_val`, `cust_email`, `cust_phone`, `billing_street`) inconsistent with the Kimball warehouse target schema (`customer_id`, `total_amount`, `email`, etc.).
- **Detection Logic**: Schema contract validator checking column headers against target data dictionary.
- **Resolution Strategy**: Explicit schema alias translation map applied during extraction stage before passing to the transformation engine.
- **Auditing**: Mapped source column pairs recorded in audit log.

### Issue 4: Numeric Currency String Formatting (`ISSUE_04_NUMERIC_CURRENCY_STRING`)
- **Source System**: SAP ERP (`sap_erp_billing.csv`).
- **Root Cause**: Accounting fields exported with currency symbols, thousand commas, and trailing decimals (e.g., `"$12,450.50"`, `"$ 450.00"`). Ingestion directly into numeric database columns triggers database cast exceptions.
- **Detection Logic**: Regex pattern `[^\d.-]` matching currency symbols or punctuation.
- **Resolution Strategy**: Stripping non-numeric characters, preserving minus signs and decimal points, casting to standard Python `float` and SQL `NUMERIC(12, 2)`.
- **Auditing**: Raw string and parsed float recorded.

### Issue 5: Phone Number & Contact Discrepancies (`ISSUE_05_PHONE_STANDARDIZATION`)
- **Source System**: SAP ERP and Salesforce CRM.
- **Root Cause**: Customers input telephone numbers in unstructured formats: `(555) 123-4567`, `555.123.4567`, `1-555-123-4567`, `5551234567`.
- **Detection Logic**: Digit length extraction comparing length to 10 or 11 digits.
- **Resolution Strategy**: Extract raw digits, strip leading country code `1`, and normalize into standard E.164-compatible format: `+1-XXX-XXX-XXXX`.
- **Auditing**: Re-formatted phone string recorded.

### Issue 6: Orphaned Foreign Keys (`ISSUE_06_ORPHANED_FOREIGN_KEYS`)
- **Source System**: WebStore Order Items and WMS Shipments.
- **Root Cause**: Asynchronous order placement and fulfillment systems produce child line items referencing deleted or non-existent product IDs (`PRD-99999`) or shipments referencing non-existent order IDs (`ORD-9999999`).
- **Detection Logic**: Set membership verification against loaded master primary keys (`dim_products.product_id` and `fact_orders.order_id`).
- **Resolution Strategy**: Orphaned rows are filtered out from the production loading stream and routed to `data/quarantine/quarantine_audit_log.json` with exact orphan foreign key details, preventing database constraint failures.
- **Auditing**: Quarantined with record ID and invalid parent reference.

### Issue 7: Duplicate Primary & Transactional Keys (`ISSUE_07_DUPLICATE_TRANSACTIONS`)
- **Source System**: WebStore E-Commerce (`webstore_orders.csv`).
- **Root Cause**: Webhook retries and distributed network drops re-submit identical order transactions multiple times.
- **Detection Logic**: Pandas `duplicated(subset=['order_id'])` check.
- **Resolution Strategy**: Idempotent deduplication retaining the first successful transaction and discarding retries.
- **Auditing**: Duplicate order ID recorded in quarantine audit log.

### Issue 8: Mandatory Null Field Violations (`ISSUE_08_NULL_MANDATORY_FIELDS`)
- **Source System**: WebStore Orders (`webstore_orders.csv`).
- **Root Cause**: Network payload truncation producing empty string or `null` values in required fields such as `customer_id` or `order_status`.
- **Detection Logic**: Vectorized `isna() | (str.strip() == '')` check across mandatory schema columns.
- **Resolution Strategy**: Quarantines records lacking essential business keys; prevents relational null constraint errors.
- **Auditing**: Dropped record ID and null column logged.

### Issue 9: State/Country Case & Code Inconsistencies (`ISSUE_09_CASE_INCONSISTENCY`)
- **Source System**: Salesforce CRM (`salesforce_crm.ndjson`).
- **Root Cause**: User free-text entry yields state names as `'california'`, `'CA'`, `'California'` and country as `'usa'`, `'USA'`, `'United States'`.
- **Detection Logic**: Case-insensitive dictionary lookup against ISO-3166 country codes and US Postal 2-letter state codes.
- **Resolution Strategy**: Normalized to canonical 2-letter uppercase postal abbreviations (`CA`, `TX`, `NY`) and country code `US`.
- **Auditing**: Standardized mapping event recorded.

### Issue 10: Nested JSON Payload Structural Mutation (`ISSUE_10_NESTED_STRUCTURAL_MUTATION`)
- **Source System**: Salesforce CRM (`salesforce_crm.ndjson`).
- **Root Cause**: CRM exports contain nested sub-objects (`address: {street, city, state, postal, country}`) that cannot be directly inserted into flat relational columns.
- **Detection Logic**: Type checking for `dict` values in incoming JSON records.
- **Resolution Strategy**: Flattening nested dictionary structures into relational column schemas (`street_address`, `city`, `state_code`, `postal_code`, `country_code`).
- **Auditing**: Schema flattening event audited.

### Issue 11: Boolean Representation Divergence (`ISSUE_11_BOOLEAN_DIVERGENCE`)
- **Source System**: SAP ERP (`sap_erp_billing.csv`).
- **Root Cause**: Legacy database exports represent boolean attributes as `'Y'/'N'`, `'1'/'0'`, `'T'/'F'`, or text `'true'/'false'`.
- **Detection Logic**: Membership evaluation in truthy and falsy string sets.
- **Resolution Strategy**: Coerced to native boolean `True`/`False` matching PostgreSQL `BOOLEAN` and SQLite `INTEGER (0/1)`.
- **Auditing**: Divergent raw value and normalized boolean audited.

### Issue 12: Float Precision & Financial Rounding (`ISSUE_12_FLOAT_PRECISION_ROUNDING`)
- **Source System**: WebStore Order Items and Orders.
- **Root Cause**: Standard IEEE 754 floating-point calculations introduce fractional inaccuracies in monetary sums (e.g., `19.990000000000002`).
- **Detection Logic**: String inspection checking for decimal expansions beyond 2 fractional places.
- **Resolution Strategy**: Quantization using `Decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)`.
- **Auditing**: Quantized financial value recorded.

### Issue 13: Corrupted / Truncated Postal Codes (`ISSUE_13_CORRUPTED_POSTAL_CODES`)
- **Source System**: Salesforce CRM and WMS Logistics.
- **Root Cause**: Spreadsheet exports or integer casting drop leading zeroes from East Coast postal codes (e.g., Boston/New Jersey zip code `07001` stored as `7001`).
- **Detection Logic**: Numeric strings of length 4.
- **Resolution Strategy**: Padded with leading zero via `.zfill(5)`.
- **Auditing**: Padded postal code recorded in audit log.

### Issue 14: Outlier & Range Boundary Anomalies (`ISSUE_14_OUTLIER_RANGE_ANOMALIES`)
- **Source System**: WebStore Order Items (`webstore_order_items.csv`).
- **Root Cause**: Upstream catalog bugs or returns incorrectly recorded with negative item quantities (e.g. `quantity = -2`) or invalid prices (`unit_price < 0`).
- **Detection Logic**: Numerical boundary check `quantity > 0` and `unit_price >= 0.0`.
- **Resolution Strategy**: Corrupted line items are quarantined with error details; prevents corrupting revenue analytics.
- **Auditing**: Quarantined row with invalid metric value recorded.
