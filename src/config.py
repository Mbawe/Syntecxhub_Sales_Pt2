"""Central configuration, styling tokens, and constants for the Syntecxhub BI Dashboard.
"""
from pathlib import Path

# Base Paths
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
ASSETS_DIR = ROOT_DIR / "assets"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Theme Specifications
# Dark Mode Specification: Background (#0F172A or #1E293B), Cards (#1E293B or #334155), Text (#F8FAFC)
# Light Mode Specification: Background (#F8FAFC), Cards (#FFFFFF), Text (#0F172A)
# Primary Highlight Accent: Electric Blue (#0052FF or #3B82F6)
THEME = {
    "dark": {
        "bg": "#0F172A",
        "card_bg": "#1E293B",
        "card_border": "#334155",
        "text": "#F8FAFC",
        "text_muted": "#94A3B8",
        "accent": "#3B82F6",
        "accent_hover": "#60A5FA",
        "chart_bg": "#1E293B",
        "grid_color": "#334155",
    },
    "light": {
        "bg": "#F8FAFC",
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",
        "text": "#0F172A",
        "text_muted": "#64748B",
        "accent": "#0052FF",
        "accent_hover": "#2563EB",
        "chart_bg": "#FFFFFF",
        "grid_color": "#F1F5F9",
    },
}

# Standard Schema Columns
STANDARD_COLUMNS = {
    "transaction_id": "Transaction_ID",
    "timestamp": "Timestamp",
    "product_sku": "Product_SKU",
    "product_category": "Product_Category",
    "quantity_sold": "Quantity_Sold",
    "unit_price": "Unit_Price",
    "discount_applied": "Discount_Applied",
    "geographic_region": "Geographic_Region",
}
