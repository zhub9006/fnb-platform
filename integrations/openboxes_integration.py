"""
FnB Inventory Integration Scaffold
====================================
Target system : OpenBoxes (https://openboxes.com)
GitHub        : https://github.com/openboxes/openboxes  ★ 843

This module provides a production-ready scaffold for integrating
the ACME FnB Platform with an OpenBoxes supply-chain backend.

Quick-start
-----------
1. Set BASE_URL and API_KEY to your OpenBoxes instance.
2. Flip `mock=False` in `fetch_inventory()` to hit the live API.
3. Run:  python openboxes_integration.py

Author  : ACME FnB Engineering
Branch  : feature/fnb-inventory-integration
"""

import json
import logging
from datetime import datetime, timedelta

import requests  # pip install requests

# ── Configuration ─────────────────────────────────────────────────────────────

BASE_URL = "https://demo.openboxes.com/openboxes/api"
API_KEY  = "YOUR_API_KEY_HERE"   # set via env var in production

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Mock / seed data (used when mock=True) ────────────────────────────────────

MOCK_INVENTORY = [
    {"id": "ITEM-001", "name": "Whole Milk",           "category": "Dairy",     "unit": "litre",  "qty_on_hand": 320, "reorder_level": 100, "supplier": "FreshFarm Co."},
    {"id": "ITEM-002", "name": "All-Purpose Flour",    "category": "Dry Goods", "unit": "kg",     "qty_on_hand": 85,  "reorder_level": 50,  "supplier": "GrainMaster Ltd."},
    {"id": "ITEM-003", "name": "Cane Sugar",           "category": "Dry Goods", "unit": "kg",     "qty_on_hand": 40,  "reorder_level": 60,  "supplier": "SweetSource Inc."},
    {"id": "ITEM-004", "name": "Olive Oil (Extra V.)", "category": "Oils",      "unit": "litre",  "qty_on_hand": 55,  "reorder_level": 30,  "supplier": "MedOil Imports"},
    {"id": "ITEM-005", "name": "Free-Range Eggs",      "category": "Poultry",   "unit": "dozen",  "qty_on_hand": 200, "reorder_level": 80,  "supplier": "HappyHen Farm"},
    {"id": "ITEM-006", "name": "Tomato Paste",         "category": "Canned",    "unit": "can",    "qty_on_hand": 18,  "reorder_level": 25,  "supplier": "SunRipe Foods"},
    {"id": "ITEM-007", "name": "Yeast (Active Dry)",   "category": "Baking",    "unit": "packet", "qty_on_hand": 150, "reorder_level": 50,  "supplier": "BakePro Supply"},
    {"id": "ITEM-008", "name": "Heavy Cream",          "category": "Dairy",     "unit": "litre",  "qty_on_hand": 90,  "reorder_level": 40,  "supplier": "FreshFarm Co."},
]

MOCK_MANIFEST = {
    "manifest_id":   "MFT-2024-0047",
    "shipment_date": (datetime.today() + timedelta(days=2)).strftime("%Y-%m-%d"),
    "origin":      {"name": "FreshFarm Co. Distribution Center", "location": "Portland, OR"},
    "destination": {"name": "ACME FnB Central Warehouse",        "location": "Seattle, WA"},
    "carrier":     "CoolChain Logistics",
    "status":      "IN_TRANSIT",
    "line_items": [
        {"item_id": "ITEM-001", "description": "Whole Milk",      "qty": 200, "unit": "litre", "temp_req": "2-4 C"},
        {"item_id": "ITEM-008", "description": "Heavy Cream",     "qty": 60,  "unit": "litre", "temp_req": "2-4 C"},
        {"item_id": "ITEM-005", "description": "Free-Range Eggs", "qty": 100, "unit": "dozen", "temp_req": "4-7 C"},
    ],
}

# ── Core integration functions ─────────────────────────────────────────────────

def fetch_inventory(mock: bool = True) -> list[dict]:
    """
    Fetch all inventory items from OpenBoxes.

    Parameters
    ----------
    mock : bool
        True  -> return local seed data (no network required).
        False -> call the live OpenBoxes REST API.

    Returns
    -------
    list[dict]  List of product/inventory records.
    """
    if mock:
        log.info("fetch_inventory: using mock data (%d items)", len(MOCK_INVENTORY))
        return MOCK_INVENTORY

    url = f"{BASE_URL}/products"
    log.info("fetch_inventory: GET %s", url)
    response = requests.get(
        url,
        headers={"API-Key": API_KEY, "Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    log.info("fetch_inventory: received %d items", len(data))
    return data


def parse_supply_chain_manifest(manifest: dict) -> dict:
    """
    Parse an inbound shipment manifest and return a structured summary.

    Parameters
    ----------
    manifest : dict
        Raw manifest payload (from OpenBoxes webhook or file import).

    Returns
    -------
    dict  Normalised manifest summary.
    """
    total_units = sum(item["qty"] for item in manifest["line_items"])
    temp_requirements = sorted({i["temp_req"] for i in manifest["line_items"]})

    return {
        "manifest_id":       manifest["manifest_id"],
        "shipment_date":     manifest["shipment_date"],
        "from":              manifest["origin"]["name"],
        "to":                manifest["destination"]["name"],
        "carrier":           manifest["carrier"],
        "status":            manifest["status"],
        "total_line_items":  len(manifest["line_items"]),
        "total_units":       total_units,
        "temp_requirements": temp_requirements,
        "line_items":        manifest["line_items"],
    }


def flag_low_stock(inventory: list[dict], threshold_pct: float = 1.0) -> list[dict]:
    """
    Return items whose qty_on_hand is at or below reorder_level * threshold_pct.

    Parameters
    ----------
    inventory     : list[dict]  Inventory records (from fetch_inventory).
    threshold_pct : float
        1.0 -> flag exactly at/below reorder level  (default).
        1.2 -> early warning: flag within 20 % of reorder level.

    Returns
    -------
    list[dict]  Alert records with added 'shortfall' and 'urgency' keys.
    """
    alerts = []
    for item in inventory:
        if item["qty_on_hand"] <= item["reorder_level"] * threshold_pct:
            gap = item["reorder_level"] - item["qty_on_hand"]
            alerts.append({
                **item,
                "shortfall": max(gap, 0),
                "urgency":   "CRITICAL" if item["qty_on_hand"] < item["reorder_level"] else "WARNING",
            })
    return alerts


def generate_reorder_report(alerts: list[dict]) -> str:
    """
    Generate a plain-text reorder report for ops / procurement teams.

    Parameters
    ----------
    alerts : list[dict]  Output of flag_low_stock().

    Returns
    -------
    str  Human-readable report.
    """
    lines = [
        "=" * 70,
        "  ACME FnB Platform -- Reorder Alert Report",
        f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
    ]
    if not alerts:
        lines.append("  All stock levels are healthy. No action required.")
    else:
        for a in alerts:
            icon = "[CRITICAL]" if a["urgency"] == "CRITICAL" else "[WARNING] "
            lines.append(
                f"  {icon} {a['name']:<25s} "
                f"On-hand: {a['qty_on_hand']:>4} {a['unit']:<7}  "
                f"Reorder @ {a['reorder_level']:<5}  "
                f"Shortfall: {a['shortfall']:>3}  "
                f"Supplier: {a['supplier']}"
            )
    lines.append("=" * 70)
    return "\n".join(lines)


# ── CLI entry-point ────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 70)
    print("  FnB Inventory Integration Scaffold -- OpenBoxes")
    print("=" * 70 + "\n")

    # 1. Fetch inventory
    inventory = fetch_inventory(mock=True)
    print(f"Fetched {len(inventory)} inventory items\n")
    print(f"  {'ID':<10} {'Name':<25} {'Category':<12} {'On-hand':>8}  {'Unit':<8} {'Reorder':>8}")
    print(f"  {'-'*10} {'-'*25} {'-'*12} {'-'*8}  {'-'*8} {'-'*8}")
    for item in inventory:
        print(f"  {item['id']:<10} {item['name']:<25} {item['category']:<12} "
              f"{item['qty_on_hand']:>8}  {item['unit']:<8} {item['reorder_level']:>8}")

    # 2. Parse supply chain manifest
    print("\n\nParsing inbound supply chain manifest ...\n")
    summary = parse_supply_chain_manifest(MOCK_MANIFEST)
    print(json.dumps(summary, indent=2))

    # 3. Flag low-stock items (early-warning: within 20 % of reorder level)
    print("\n\nRunning low-stock check (threshold = 120 % of reorder level) ...\n")
    alerts = flag_low_stock(inventory, threshold_pct=1.2)
    print(generate_reorder_report(alerts))

    print("\nScaffold run complete. Ready to wire up live API endpoints.\n")


if __name__ == "__main__":
    main()
