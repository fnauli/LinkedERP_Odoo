# Demo Seed Scripts

## kjuice_demo_seed.py

Seeds the K-Juice Booster / PT Sajindo Kimura Raya demo dataset into an Odoo 19
database over XML-RPC: fruits with lot + expiry tracking, juice BoMs, suppliers,
franchisee outlets, brand analytic accounts, CRM franchise leads, and draft
PO/SO/MO transactions tagged `KJ-DEMO`.

The script is idempotent — it searches before creating, so it is safe to re-run.

### Prerequisites

In the target Odoo database, install: Inventory, Purchase, Sales,
Accounting/Invoicing, Manufacturing, CRM, Point of Sale. The script skips
anything that isn't installed. For fruit expiry dates, enable **Expiration
Dates** under Inventory → Configuration → Settings (the script falls back
gracefully if it's off).

### Usage

```bash
export ODOO_URL="https://demo-skr.odoo.com"   # a pasted /odoo/ browser URL also works
export ODOO_USER="your.email@example.com"
export ODOO_API_KEY="xxxxxxxxxxxxxxxx"        # Odoo: Preferences -> Account Security -> API Keys
# ODOO_DB is optional for Odoo Online (*.odoo.com) - it defaults to the subdomain
python3 scripts/kjuice_demo_seed.py
```

The script honors `HTTPS_PROXY` and the standard CA-bundle environment
variables (`SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`), so it also works from
proxied environments such as Claude Code cloud sessions — provided the
session's network policy allows the Odoo host.

After seeding, review in Odoo: Products, BoMs, Contacts, the CRM pipeline, and
the draft PO/SO/MO tagged `KJ-DEMO`. Confirm them live during the demo to show
the purchase → manufacture → sell flow.
