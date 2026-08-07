from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_OLIST = ROOT / "data" / "raw" / "olist"
RAW_MOCK = ROOT / "data" / "raw" / "mock"
BRONZE = ROOT / "data" / "bronze"
WAREHOUSE_DIR = ROOT / "warehouse"
WAREHOUSE = WAREHOUSE_DIR / "subscription_commerce.duckdb"
ARTIFACTS = ROOT / "artifacts"
DBT_DIR = ROOT / "dbt"

REQUIRED_OLIST = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "products": "olist_products_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def ensure_dirs() -> None:
    for path in (RAW_OLIST, RAW_MOCK, BRONZE, WAREHOUSE_DIR, ARTIFACTS):
        path.mkdir(parents=True, exist_ok=True)


def missing_olist_files() -> list[str]:
    return [name for name in REQUIRED_OLIST.values() if not (RAW_OLIST / name).exists()]
