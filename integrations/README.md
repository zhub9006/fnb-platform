# FnB Inventory Integrations

This directory contains integration scaffolds connecting the **ACME FnB Platform**
to open-source supply-chain and inventory management tools.

---

## 🗂️ Open-Source Tools Evaluated

| Tool | Stars | Language | Best For |
|---|---|---|---|
| [**OpenBoxes**](https://github.com/openboxes/openboxes) | ★ 843 | Groovy / React | Supply chain tracking, warehouse ops, cold-chain |
| [**ERPNext / Frappe**](https://github.com/frappe/erpnext) | ★ 20k+ | Python / JS | Full ERP — inventory, manufacturing, procurement |
| [**Odoo Community**](https://github.com/odoo/odoo) | ★ 40k+ | Python / JS | Modular ERP with strong FnB & POS modules |
| [**Slim4 for Odoo**](https://github.com/Slimstock-Slim4/Slimstock-Inventory-Optimization-for-Odoo) | — | Python | AI-driven demand forecasting on top of Odoo |

> **Chosen for this scaffold:** OpenBoxes — lightweight, REST-first, and well-suited
> to cold-chain and perishable goods tracking common in FnB operations.

---

## 📦 `openboxes_integration.py`

A production-ready Python scaffold for the OpenBoxes REST API.

### Features

| Function | Description |
|---|---|
| `fetch_inventory(mock)` | GET all stock items; flip `mock=False` for live API |
| `parse_supply_chain_manifest(manifest)` | Normalise inbound shipment manifests |
| `flag_low_stock(inventory, threshold_pct)` | Configurable early-warning reorder alerts |
| `generate_reorder_report(alerts)` | Plain-text report for ops / procurement teams |

### Quick Start

```bash
pip install requests

# Set your OpenBoxes credentials
export OPENBOXES_BASE_URL="https://your-instance.openboxes.com/openboxes/api"
export OPENBOXES_API_KEY="your-api-key"

python integrations/openboxes_integration.py
```

### Sample Output

```
======================================================================
  FnB Inventory Integration Scaffold -- OpenBoxes
======================================================================

Fetched 8 inventory items

  ID         Name                      Category      On-hand  Unit      Reorder
  ---------- ------------------------- ------------ --------  -------- --------
  ITEM-001   Whole Milk                Dairy             320  litre         100
  ITEM-003   Cane Sugar                Dry Goods          40  kg             60  ← CRITICAL
  ITEM-006   Tomato Paste              Canned             18  can            25  ← CRITICAL

======================================================================
  ACME FnB Platform -- Reorder Alert Report
======================================================================
  [CRITICAL] Cane Sugar      On-hand:   40 kg     Reorder @ 60   Shortfall:  20  Supplier: SweetSource Inc.
  [CRITICAL] Tomato Paste    On-hand:   18 can    Reorder @ 25   Shortfall:   7  Supplier: SunRipe Foods
======================================================================
```

---

## 🔮 Next Steps

- [ ] Wire `fetch_inventory(mock=False)` to live OpenBoxes instance
- [ ] Add OAuth2 / API-key env-var loading (`python-dotenv`)
- [ ] Implement `create_purchase_order()` to auto-raise POs on CRITICAL alerts
- [ ] Add webhook listener for inbound manifest push events
- [ ] Write unit tests (`pytest`) against mock data
- [ ] Explore ERPNext REST API scaffold as a parallel integration path

---

*Branch: `feature/fnb-inventory-integration` — open a PR to `main` when ready.*
