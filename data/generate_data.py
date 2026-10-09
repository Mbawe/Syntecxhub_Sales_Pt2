"""Generator for high-fidelity retail transactional ledger test datasets.
Synthesizes multi-item orders, seasonal demand surges, mixed date formats, and geographic distributions.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)

CATEGORIES_AND_SKUS = {
    "Consumer Electronics": [
        ("SKU-LAPTOP-PRO16", 1499.00),
        ("SKU-4K-MONITOR-32", 499.00),
        ("SKU-TABLET-AIR10", 649.00),
        ("SKU-PHONE-ULTRA", 999.00),
    ],
    "Accessories & Audio": [
        ("SKU-ANC-HEADPHONES", 249.00),
        ("SKU-WIRELESS-MOUSE", 49.00),
        ("SKU-MECH-KEYBOARD", 129.00),
        ("SKU-USB-C-DOCK", 89.00),
    ],
    "Office Furniture": [
        ("SKU-ERGO-CHAIR-X", 389.00),
        ("SKU-STAND-DESK-PRO", 599.00),
        ("SKU-MONITOR-ARM-DUAL", 119.00),
    ],
    "Smart Home & IoT": [
        ("SKU-SMART-CAM-360", 79.00),
        ("SKU-SMART-HUB-GEN2", 119.00),
        ("SKU-SMART-PLUG-4PK", 39.00),
    ],
    "Software & Services": [
        ("SKU-CLOUD-BACKUP-YR", 99.00),
        ("SKU-SECURITY-SUITE", 149.00),
        ("SKU-COLLAB-PRO-SEAT", 199.00),
    ],
}

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
REGION_WEIGHTS = [0.38, 0.28, 0.20, 0.08, 0.06]

def generate_master_dataset(num_records: int = 6000, output_filename: str = "retail_transactions_master.csv") -> Path:
    random.seed(42)
    np.random.seed(42)

    start_date = datetime(2024, 1, 1)
    records = []

    # Generate roughly num_records lines across realistic transactions
    txn_counter = 10001

    while len(records) < num_records:
        txn_id = f"TXN-{txn_counter}"
        txn_counter += 1

        # Date distribution with holiday surge in Nov/Dec and back-to-school in Aug
        day_offset = random.randint(0, 364)
        order_date = start_date + timedelta(days=day_offset, minutes=random.randint(0, 1439))

        # Weight month selection: higher in Nov/Dec
        m = order_date.month
        surge_mult = 1.0
        if m in [11, 12]:
            surge_mult = 1.85
        elif m in [8, 9]:
            surge_mult = 1.35
        elif m in [1, 2]:
            surge_mult = 0.75

        # Geographic region for this customer transaction
        region = random.choices(REGIONS, weights=REGION_WEIGHTS)[0]

        # Order size: 1 to 4 items in this cart
        cart_size = random.choices([1, 2, 3, 4], weights=[0.55, 0.25, 0.15, 0.05])[0]

        for _ in range(cart_size):
            cat = random.choice(list(CATEGORIES_AND_SKUS.keys()))
            sku, base_price = random.choice(CATEGORIES_AND_SKUS[cat])
            
            # Slight price variance (+- 5%)
            unit_price = round(base_price * random.uniform(0.95, 1.05), 2)
            
            # Quantity
            qty = random.choices([1, 2, 3, 5, 10], weights=[0.60, 0.22, 0.10, 0.05, 0.03])[0]

            # Discount (promotions in peak months)
            if random.random() < (0.35 * surge_mult):
                discount = round(unit_price * qty * random.uniform(0.05, 0.25), 2)
            else:
                discount = 0.0

            # Deliberately mix timestamp string formats to test normalization engine
            fmt_choice = random.choice([1, 2, 3, 4])
            if fmt_choice == 1:
                timestamp_str = order_date.strftime("%Y-%m-%d %H:%M:%S")
            elif fmt_choice == 2:
                timestamp_str = order_date.strftime("%m/%d/%Y %H:%M")
            elif fmt_choice == 3:
                timestamp_str = order_date.strftime("%Y-%m-%d")
            else:
                timestamp_str = order_date.strftime("%d/%m/%Y")

            records.append({
                "Transaction_ID": txn_id,
                "Timestamp": timestamp_str,
                "Product_SKU": sku,
                "Product_Category": cat,
                "Quantity_Sold": qty,
                "Unit_Price": unit_price,
                "Discount_Applied": discount,
                "Geographic_Region": region,
            })

            if len(records) >= num_records:
                break

    df = pd.DataFrame(records)

    # Inject minor realistic non-critical missing data (e.g., 1% blank discounts or regions) to verify robustness
    mask_disc_nan = np.random.rand(len(df)) < 0.02
    df.loc[mask_disc_nan, "Discount_Applied"] = np.nan

    out_path = DATA_DIR / output_filename
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} transactions to {out_path}")
    return out_path

if __name__ == "__main__":
    generate_master_dataset()
