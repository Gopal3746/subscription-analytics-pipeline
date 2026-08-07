from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
metrics_path = ROOT / "artifacts" / "resume_metrics.json"
bullets_path = ROOT / "artifacts" / "resume_bullets.md"
audit_path = ROOT / "artifacts" / "spark_ingest_audit.json"
warehouse = ROOT / "warehouse" / "subscription_commerce.duckdb"

required = [metrics_path, bullets_path, audit_path, warehouse]
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    raise SystemExit("Missing generated artifacts: " + ", ".join(missing))

metrics = json.loads(metrics_path.read_text())
bullets = bullets_path.read_text()
assert metrics["real_orders"] > 90000, metrics
assert metrics["customer_segments"] >= 2, metrics
assert metrics["synthetic_subscribers"] > 0, metrics
for placeholder in ("[X]", "[REAL_ORDERS]", "[RETENTION_VARIANCE_PP]", "[CUSTOMER_SEGMENTS]"):
    assert placeholder not in bullets
print("portfolio validation passed")
