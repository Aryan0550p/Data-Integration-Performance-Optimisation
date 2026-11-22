"""
Enterprise Source Systems Synthetic Data Generator
Generates datasets for 5 enterprise systems with 14 injected integration issues.
"""
import csv
import json
import random
from datetime import datetime, date, timedelta
from pathlib import Path
from faker import Faker
from config.settings import RAW_DATA_DIR
from src.utils.logger import logger

fake = Faker()
Faker.seed(42)
random.seed(42)

def generate_enterprise_data(
    num_customers: int = 2500,
    num_orders: int = 15000,
    num_products: int = 250,
    num_warehouses: int = 15,
    num_campaigns: int = 30
):
    """Generate source data files for all 5 enterprise systems."""
    logger.info("Starting enterprise source systems data generation...")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. HubSpot Marketing Campaigns (JSON)
    # -------------------------------------------------------------------------
    logger.info("Generating System 1: HubSpot Marketing Campaigns (JSON)...")
    campaigns = []
    channels = ["Paid Search", "Social Media", "Email Marketing", "Affiliate", "Display Ads", "Organic Search"]
    for i in range(1, num_campaigns + 1):
        cid = f"CMP-{i:04d}"
        start = fake.date_between(start_date="-2y", end_date="-1y")
        end = start + timedelta(days=random.randint(30, 180))
        campaigns.append({
            "campaign_id": cid,
            "campaign_name": f"{fake.company()} {random.choice(['Q1 Promo', 'Summer Sale', 'Black Friday', 'Brand Awareness', 'Retargeting'])}",
            "channel_type": random.choice(channels),
            "budget": round(random.uniform(5000.0, 150000.0), 2),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "utm_source": random.choice(["google", "facebook", "linkedin", "newsletter", "twitter", "partner"]),
            "utm_medium": random.choice(["cpc", "social", "email", "referral", "banner"]),
            "target_region": random.choice(["North America", "EMEA", "APAC", "LATAM", "Global"]),
            "is_active": True
        })
    with open(RAW_DATA_DIR / "hubspot_campaigns.json", "w", encoding="utf-8") as f:
        json.dump(campaigns, f, indent=2)

    # -------------------------------------------------------------------------
    # 2. WMS Logistics & Warehouses (TSV)
    # -------------------------------------------------------------------------
    logger.info("Generating System 2: WMS Logistics & Warehouses (TSV)...")
    warehouses = []
    for i in range(1, num_warehouses + 1):
        wid = f"WH-{i:03d}"
        warehouses.append({
            "warehouse_id": wid,
            "warehouse_name": f"{fake.city()} Logistics Hub",
            "warehouse_code": f"HUB_{fake.city()[:3].upper()}_{i:02d}",
            "facility_type": random.choice(["Distribution Center", "Fulfillment Hub", "Cross-Dock", "Cold Storage"]),
            "capacity_sqft": random.randint(30000, 300000),
            "city": fake.city(),
            "state_code": fake.state_abbr(),
            "postal_code": fake.zipcode(),
            "country_code": "US",
            "is_active": True
        })
    with open(RAW_DATA_DIR / "wms_warehouses.tsv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(warehouses[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(warehouses)

    # -------------------------------------------------------------------------
    # 3. Product Catalog (CSV - baseline reference)
    # -------------------------------------------------------------------------
    logger.info("Generating Master Product Catalog...")
    categories = {
        "Enterprise Hardware": ["Servers", "Networking", "Storage", "UPS & Power"],
        "Office Supplies": ["Furniture", "Paper & Print", "Desk Accessories"],
        "Cloud Solutions": ["SaaS Licenses", "Security Appliances", "Backup Storage"],
        "Industrial Components": ["Sensors", "Controllers", "Wiring & Cables"]
    }
    products = []
    for i in range(1, num_products + 1):
        cat = random.choice(list(categories.keys()))
        subcat = random.choice(categories[cat])
        cost = round(random.uniform(15.0, 850.0), 2)
        retail = round(cost * random.uniform(1.25, 2.2), 2)
        products.append({
            "product_id": f"PRD-{i:05d}",
            "sku": f"SKU-{cat[:3].upper()}-{i:04d}",
            "product_name": f"{fake.word().capitalize()} {subcat[:-1] if subcat.endswith('s') else subcat} Model {i}",
            "category": cat,
            "subcategory": subcat,
            "cost_price": cost,
            "retail_price": retail,
            "weight_kg": round(random.uniform(0.2, 35.0), 2),
            "is_active": True
        })
    with open(RAW_DATA_DIR / "master_products.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(products[0].keys()))
        writer.writeheader()
        writer.writerows(products)

    # -------------------------------------------------------------------------
    # 4. SAP ERP Billing System (CSV - with ISO-8859-1 / Windows-1252 encoding,
    #    legacy headers, currency symbols, and booleans 'Y'/'N')
    # -------------------------------------------------------------------------
    logger.info("Generating System 3: SAP ERP Billing System (CSV, Windows-1252)...")
    erp_records = []
    # Accented sample names for encoding conflict (Issue 1)
    accented_first_names = ["René", "François", "Müller", "Jürgen", "Élodie", "Søren", "Hélène", "Inês", "Björn", "Gérard"]
    accented_last_names = ["López", "García", "Schröder", "Hernández", "Benoît", "Strauß", "Kovács", "Dubois"]

    for i in range(1, num_customers + 1):
        cid = f"CUST-{i:06d}"
        if i <= 50:  # Inject Issue 1: Accented Latin-1 characters
            first_name = random.choice(accented_first_names)
            last_name = random.choice(accented_last_names)
        else:
            first_name = fake.first_name()
            last_name = fake.last_name()

        # Phone variations (Issue 5)
        raw_phone = random.choice([
            f"({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}",
            f"{random.randint(200,999)}.{random.randint(100,999)}.{random.randint(1000,9999)}",
            f"1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
            f"{random.randint(2000000000,9999999999)}"
        ])

        # Currency string formatting (Issue 4)
        credit_val = round(random.uniform(1000.0, 75000.0), 2)
        credit_str = f"${credit_val:,.2f}"

        # Boolean divergence (Issue 11)
        is_ent_val = random.choice(["Y", "N", "1", "0", "true", "false"])

        erp_records.append({
            # Legacy column names (Issue 3)
            "cust_no": cid,
            "first_name": first_name,
            "last_name": last_name,
            "cust_email": f"{first_name.lower().replace('é','e').replace('ü','u')}.{last_name.lower()}@{fake.domain_name()}",
            "cust_phone": raw_phone,
            "billing_street": fake.street_address(),
            "billing_city": fake.city(),
            "billing_state": fake.state_abbr(),
            "billing_postal": fake.zipcode(),
            "billing_country": "USA",
            "credit_limit": credit_str,
            "is_enterprise": is_ent_val,
            "created_date": fake.date_between(start_date="-3y", end_date="-1y").strftime("%Y-%m-%d")
        })

    # Save specifically in Windows-1252 / latin1
    with open(RAW_DATA_DIR / "sap_erp_billing.csv", "w", encoding="windows-1252", errors="replace", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(erp_records[0].keys()))
        writer.writeheader()
        writer.writerows(erp_records)

    # -------------------------------------------------------------------------
    # 5. Salesforce CRM (NDJSON - nested addresses, case variations, postal issues)
    # -------------------------------------------------------------------------
    logger.info("Generating System 4: Salesforce CRM (NDJSON)...")
    crm_records = []
    state_variations = ["california", "CA", "Texas", "TX", "new york", "NY", "Florida", "FL", "Illinois", "IL"]
    country_variations = ["usa", "USA", "United States", "US", "u.s.a."]

    with open(RAW_DATA_DIR / "salesforce_crm.ndjson", "w", encoding="utf-8") as f:
        for i in range(1, num_customers + 1):
            cid = f"CUST-{i:06d}"
            # Issue 13: Corrupted postal code missing leading zero (e.g. "07001" saved as "7001")
            raw_zip = fake.zipcode()
            if random.random() < 0.15:
                raw_zip = f"{random.randint(1000, 9999)}"  # 4 digits, needs zero padding!

            record = {
                "account_id": cid,
                "account_name": f"{fake.company()} LLC",
                "contact_email": f"contact_{i}@{fake.domain_name()}",
                "primary_phone": fake.phone_number(),
                # Issue 10: Nested address payload
                "address": {
                    "street": fake.street_address(),
                    "city": fake.city(),
                    # Issue 9: Mixed case state & country
                    "state": random.choice(state_variations),
                    "postal": raw_zip,
                    "country": random.choice(country_variations)
                },
                "is_enterprise": random.choice([True, False]),
                "created_at": fake.date_time_between(start_date="-3y", end_date="-1y").isoformat()
            }
            crm_records.append(record)
            f.write(json.dumps(record) + "\n")

    # -------------------------------------------------------------------------
    # 6. E-Commerce WebStore Orders & Items (CSV)
    # -------------------------------------------------------------------------
    logger.info("Generating System 5: WebStore Orders & Items (CSV)...")
    orders = []
    order_items = []
    shipments = []

    carrier_list = ["UPS_GROUND", "FEDEX_2DAY", "USPS_PRIORITY", "DHL_EXPRESS"]
    statuses = ["COMPLETED", "COMPLETED", "COMPLETED", "SHIPPED", "PROCESSING", "CANCELLED"]

    base_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_delta = (end_date - base_date).days

    for i in range(1, num_orders + 1):
        oid = f"ORD-{i:07d}"
        cust_id = f"CUST-{random.randint(1, num_customers):06d}"
        camp_id = f"CMP-{random.randint(1, num_campaigns):04d}" if random.random() < 0.65 else None

        # Issue 2: Mixed datetime formats
        order_dt = base_date + timedelta(days=random.randint(0, date_delta), seconds=random.randint(0, 86400))
        fmt_choice = random.choice(["iso", "us_slash", "epoch", "hyphen"])
        if fmt_choice == "iso":
            raw_ts = order_dt.strftime("%Y-%m-%d %H:%M:%S")
        elif fmt_choice == "us_slash":
            raw_ts = order_dt.strftime("%m/%d/%Y %I:%M %p")
        elif fmt_choice == "epoch":
            raw_ts = str(int(order_dt.timestamp()))
        else:
            raw_ts = order_dt.strftime("%d-%m-%Y %H:%M:%S")

        # Generate 1 to 5 line items
        num_items = random.randint(1, 5)
        order_subtotal = 0.0

        for item_idx in range(1, num_items + 1):
            item_id = f"ITEM-{oid}-{item_idx:02d}"
            prod = random.choice(products)
            qty = random.randint(1, 8)

            # Issue 14: Outlier corrupted quantity in a few rows
            if i % 750 == 0 and item_idx == 1:
                qty = -2  # Negative quantity!

            unit_price = prod["retail_price"]
            discount_rate = random.choice([0.0, 0.05, 0.10, 0.15])
            # Issue 12: Float precision rounding inaccuracy
            line_total = round(qty * unit_price * (1.0 - discount_rate), 4)
            order_subtotal += line_total

            # Issue 6: Injected orphaned foreign key (referencing non-existent product)
            target_prod_id = prod["product_id"]
            if i % 1200 == 0:
                target_prod_id = "PRD-99999"  # Non-existent product!

            order_items.append({
                "item_id": item_id,
                "order_id": oid,
                "product_id": target_prod_id,
                "quantity": qty,
                "unit_price": unit_price,
                "discount_rate": discount_rate,
                "line_total": line_total
            })

        tax = round(order_subtotal * 0.08, 2)
        shipping = 15.0 if order_subtotal < 100 else 0.0
        discount = round(order_subtotal * 0.05 if random.random() < 0.2 else 0.0, 2)
        total = round(order_subtotal + tax + shipping - discount, 2)
        status = random.choice(statuses)

        # Issue 8: Injected null in mandatory customer_id for a tiny fraction
        target_cust = cust_id
        if i % 1500 == 0:
            target_cust = ""  # Mandatory null violation!

        orders.append({
            "order_id": oid,
            "customer_id": target_cust,
            "campaign_id": camp_id if camp_id else "",
            "order_timestamp": raw_ts,
            "order_status": status,
            "currency": "USD",
            "subtotal": round(order_subtotal, 2),
            "tax_amount": tax,
            "shipping_amount": shipping,
            "discount_amount": discount,
            "total_amount": total
        })

        # Issue 7: Duplicate transactions (retry mechanism duplicates)
        if i % 400 == 0:
            orders.append(orders[-1].copy())  # Exact duplicate order_id!

        # Shipment generation for shipped/completed orders
        if status in ["COMPLETED", "SHIPPED"]:
            ship_id = f"SHIP-{oid}"
            target_wh = f"WH-{random.randint(1, num_warehouses):03d}"
            dispatch_dt = order_dt + timedelta(hours=random.randint(6, 48))
            delivered_dt = dispatch_dt + timedelta(days=random.randint(1, 5)) if status == "COMPLETED" else None

            # Issue 6: Orphan shipment pointing to non-existent order in a few cases
            ship_oid = oid
            if i % 1800 == 0:
                ship_oid = "ORD-9999999"  # Orphaned order ID!

            shipments.append({
                "shipment_id": ship_id,
                "order_id": ship_oid,
                "warehouse_id": target_wh,
                "carrier_code": random.choice(carrier_list),
                "tracking_number": f"TRK-{fake.uuid4()[:16].upper()}",
                "dispatched_at": dispatch_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "delivered_at": delivered_dt.strftime("%Y-%m-%d %H:%M:%S") if delivered_dt else "",
                "shipping_cost": round(random.uniform(5.50, 45.00), 2),
                "shipping_status": "DELIVERED" if status == "COMPLETED" else "IN_TRANSIT"
            })

    # Write webstore orders
    with open(RAW_DATA_DIR / "webstore_orders.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(orders[0].keys()))
        writer.writeheader()
        writer.writerows(orders)

    # Write webstore order items
    with open(RAW_DATA_DIR / "webstore_order_items.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(order_items[0].keys()))
        writer.writeheader()
        writer.writerows(order_items)

    # Write WMS shipments
    with open(RAW_DATA_DIR / "wms_shipments.tsv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(shipments[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(shipments)

    logger.info(
        f"Data generation complete: {len(erp_records)} ERP customers, "
        f"{len(crm_records)} CRM records, {len(orders)} orders, "
        f"{len(order_items)} items, {len(shipments)} shipments, "
        f"{len(products)} products, {len(warehouses)} warehouses, "
        f"{len(campaigns)} campaigns."
    )

if __name__ == "__main__":
    generate_enterprise_data()
