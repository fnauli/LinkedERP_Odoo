"""
K-Juice Booster - Odoo 19 Demo Database Seeder (XML-RPC)
=========================================================
Seeds a demo-ready dataset for the K-Juice Booster / PT Sajindo Kimura Raya story:
fruits with lot+expiry tracking, juice BoMs for the central kitchen, fruit suppliers,
franchisee outlet customers, brand analytic accounts, CRM franchise leads, and
sample purchase / manufacturing / sales flows.

USAGE
-----
1. In Odoo, make sure these apps are installed (script skips anything missing):
   Inventory, Purchase, Sales, Accounting/Invoicing, Manufacturing, CRM, Point of Sale
2. Set environment variables, then run:

   export ODOO_URL="https://yourcompany.odoo.com"
   export ODOO_DB="yourcompany-db-name"
   export ODOO_USER="your.email@linkederp.com"
   export ODOO_API_KEY="xxxxxxxxxxxxxxxx"
   python3 kjuice_demo_seed.py

The script is idempotent: it searches before creating, so it is safe to re-run.
"""

import http.client
import os
import ssl
import sys
import xmlrpc.client
from datetime import date, timedelta
from urllib.parse import urlparse

URL = os.environ.get("ODOO_URL", "").rstrip("/")
# Strip a trailing /odoo path if the browser URL was pasted (e.g. https://x.odoo.com/odoo/)
if URL.endswith("/odoo"):
    URL = URL[: -len("/odoo")]
DB = os.environ.get("ODOO_DB", "")
USER = os.environ.get("ODOO_USER", "")
KEY = os.environ.get("ODOO_API_KEY", "")

if URL and not DB and URL.endswith(".odoo.com"):
    # Odoo Online: database name matches the subdomain
    DB = urlparse(URL).hostname.split(".")[0]

if not all([URL, DB, USER, KEY]):
    sys.exit("Set ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY environment variables first.")


class ProxiedSafeTransport(xmlrpc.client.SafeTransport):
    """SafeTransport that tunnels through an HTTP proxy (xmlrpc.client
    ignores HTTPS_PROXY by default). Trusts the CA bundle from the
    standard env vars when set."""

    def __init__(self, proxy_url):
        cafile = (os.environ.get("SSL_CERT_FILE")
                  or os.environ.get("REQUESTS_CA_BUNDLE")
                  or os.environ.get("CURL_CA_BUNDLE"))
        super().__init__(context=ssl.create_default_context(cafile=cafile))
        p = urlparse(proxy_url)
        self.proxy_host, self.proxy_port = p.hostname, p.port or 3128

    def make_connection(self, host):
        if self._connection and host == self._connection[0]:
            return self._connection[1]
        chost, self._extra_headers, _ = self.get_host_info(host)
        conn = http.client.HTTPSConnection(self.proxy_host, self.proxy_port,
                                           context=self.context)
        conn.set_tunnel(chost)
        self._connection = host, conn
        return conn


def _server_proxy(endpoint):
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy_url and endpoint.startswith("https://"):
        return xmlrpc.client.ServerProxy(endpoint, transport=ProxiedSafeTransport(proxy_url))
    return xmlrpc.client.ServerProxy(endpoint)


common = _server_proxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USER, KEY, {})
if not uid:
    sys.exit("Authentication failed. Check URL / DB / user / API key.")
models = _server_proxy(f"{URL}/xmlrpc/2/object")


def x(model, method, *args, **kw):
    return models.execute_kw(DB, uid, KEY, model, method, list(args), kw)


def module_installed(name):
    return bool(x("ir.module.module", "search",
                  [[("name", "=", name), ("state", "=", "installed")]], limit=1))


def get_or_create(model, domain, vals):
    ids = x(model, "search", [domain], limit=1)
    if ids:
        return ids[0], False
    return x(model, "create", [vals]), True


def log(msg):
    print(f"  {msg}")


print(f"Connected to {URL} as uid {uid}\n")

HAS_MRP = module_installed("mrp")
HAS_CRM = module_installed("crm")
HAS_POS = module_installed("point_of_sale")
HAS_ACC = module_installed("account")
HAS_ANALYTIC = module_installed("analytic")
print(f"Apps -> mrp:{HAS_MRP} crm:{HAS_CRM} pos:{HAS_POS} account:{HAS_ACC} analytic:{HAS_ANALYTIC}\n")

# ---------------------------------------------------------------- UoM refs
uom_kg = x("uom.uom", "search", [[("name", "in", ["kg", "Kg", "KG"])]], limit=1)
uom_kg = uom_kg[0] if uom_kg else False
uom_unit = x("uom.uom", "search", [[("name", "in", ["Units", "Unit(s)", "Unit"])]], limit=1)
uom_unit = uom_unit[0] if uom_unit else False

# ---------------------------------------------------------------- 1. Product categories
print("1. Product categories")
cat_ids = {}
for cat in ["Fresh Fruit", "Packaging", "Finished Juice"]:
    cid, created = get_or_create("product.category", [("name", "=", cat)], {"name": cat})
    cat_ids[cat] = cid
    log(f"{'created' if created else 'exists '}: {cat}")

# ---------------------------------------------------------------- 2. Raw materials (fruits, lot + expiry)
print("\n2. Fruits (storable, tracked by lot with expiry)")
fruits = [
    ("Orange (Sunkist)", 28000), ("Mango (Harum Manis)", 32000),
    ("Watermelon", 12000), ("Strawberry", 65000), ("Pineapple", 15000),
    ("Green Apple", 42000), ("Carrot", 14000), ("Celery", 25000),
    ("Dragon Fruit", 30000), ("Banana (Cavendish)", 18000),
]
fruit_ids = {}
for name, cost in fruits:
    vals = {
        "name": name, "type": "consu", "is_storable": True,
        "categ_id": cat_ids["Fresh Fruit"], "standard_price": cost,
        "purchase_ok": True, "sale_ok": False,
        "tracking": "lot", "use_expiration_date": True,
        "expiration_time": 7, "removal_time": 6, "alert_time": 5,
    }
    if uom_kg:
        vals.update({"uom_id": uom_kg, "uom_po_id": uom_kg})
    try:
        pid, created = get_or_create("product.template", [("name", "=", name)], vals)
        fruit_ids[name] = pid
        log(f"{'created' if created else 'exists '}: {name}")
    except Exception as e:
        # expiry fields need Expiration Dates enabled in Inventory settings
        vals = {k: v for k, v in vals.items()
                if k not in ("use_expiration_date", "expiration_time", "removal_time", "alert_time")}
        pid, created = get_or_create("product.template", [("name", "=", name)], vals)
        fruit_ids[name] = pid
        log(f"created (no expiry cfg - enable 'Expiration Dates' in Inventory settings): {name}")

# ---------------------------------------------------------------- 3. Packaging
print("\n3. Packaging")
packaging = [("Cup 16oz (K-Juice branded)", 900), ("Dome Lid", 300), ("Paper Straw", 150)]
pack_ids = {}
for name, cost in packaging:
    vals = {"name": name, "type": "consu", "is_storable": True,
            "categ_id": cat_ids["Packaging"], "standard_price": cost,
            "purchase_ok": True, "sale_ok": False}
    pid, created = get_or_create("product.template", [("name", "=", name)], vals)
    pack_ids[name] = pid
    log(f"{'created' if created else 'exists '}: {name}")

# ---------------------------------------------------------------- 4. Finished juices + BoMs
print("\n4. Finished juices")
juices = [
    ("Orange Booster 16oz", 35000, [("Orange (Sunkist)", 0.45)]),
    ("Mango Booster 16oz", 38000, [("Mango (Harum Manis)", 0.40)]),
    ("Green Detox 16oz", 42000, [("Green Apple", 0.25), ("Celery", 0.10), ("Pineapple", 0.15)]),
    ("Berry Blast 16oz", 45000, [("Strawberry", 0.30), ("Banana (Cavendish)", 0.15)]),
    ("Watermelon Fresh 16oz", 30000, [("Watermelon", 0.55)]),
]
juice_ids = {}
for name, price, recipe in juices:
    vals = {"name": name, "type": "consu", "is_storable": True,
            "categ_id": cat_ids["Finished Juice"], "list_price": price,
            "sale_ok": True, "purchase_ok": False, "available_in_pos": HAS_POS}
    try:
        pid, created = get_or_create("product.template", [("name", "=", name)], vals)
    except Exception:
        vals.pop("available_in_pos", None)
        pid, created = get_or_create("product.template", [("name", "=", name)], vals)
    juice_ids[name] = (pid, recipe)
    log(f"{'created' if created else 'exists '}: {name} @ Rp {price:,}")

if HAS_MRP:
    print("\n   BoMs (central kitchen recipes)")
    for name, (tmpl_id, recipe) in juice_ids.items():
        existing = x("mrp.bom", "search", [[("product_tmpl_id", "=", tmpl_id)]], limit=1)
        if existing:
            log(f"exists : BoM {name}")
            continue
        lines = []
        for comp_name, qty in recipe:
            comp_variant = x("product.product", "search",
                             [[("product_tmpl_id", "=", fruit_ids[comp_name])]], limit=1)
            if comp_variant:
                lines.append((0, 0, {"product_id": comp_variant[0], "product_qty": qty}))
        for pk in pack_ids.values():
            pv = x("product.product", "search", [[("product_tmpl_id", "=", pk)]], limit=1)
            if pv:
                lines.append((0, 0, {"product_id": pv[0], "product_qty": 1}))
        x("mrp.bom", "create", [{"product_tmpl_id": tmpl_id, "product_qty": 1,
                                 "type": "normal", "bom_line_ids": lines}])
        log(f"created: BoM {name}")

# ---------------------------------------------------------------- 5. Vendors
print("\n5. Fruit suppliers")
vendors = [
    ("CV Segar Buah Nusantara", "Pasar Induk Kramat Jati, Jakarta Timur"),
    ("PT Tropika Fruit Supply", "Tangerang"),
    ("UD Tani Makmur (packaging)", "Bekasi"),
]
vendor_ids = {}
for name, city in vendors:
    vid, created = get_or_create("res.partner", [("name", "=", name)],
                                 {"name": name, "is_company": True,
                                  "supplier_rank": 1, "street": city})
    vendor_ids[name] = vid
    log(f"{'created' if created else 'exists '}: {name}")

# ---------------------------------------------------------------- 6. Franchisee outlets
print("\n6. Franchisee outlet customers")
outlets = [
    "K-Juice Neo Soho Mall", "K-Juice Mall Kelapa Gading 3",
    "K-Juice Central Park", "K-Juice Tangerang City Mall", "K-Juice AEON BSD",
]
outlet_ids = {}
for name in outlets:
    oid, created = get_or_create("res.partner", [("name", "=", name)],
                                 {"name": name, "is_company": True, "customer_rank": 1,
                                  "ref": name.replace("K-Juice ", "FR-")[:16]})
    outlet_ids[name] = oid
    log(f"{'created' if created else 'exists '}: {name}")

# ---------------------------------------------------------------- 7. Brand analytic accounts
if HAS_ANALYTIC:
    print("\n7. Brand analytic accounts")
    try:
        plan_id, created = get_or_create("account.analytic.plan", [("name", "=", "Brand")],
                                         {"name": "Brand"})
        log(f"{'created' if created else 'exists '}: analytic plan 'Brand'")
        for brand in ["K-Juice Booster", "Bakmie Booster", "Dimsum Booster", "Takoyaki Booster"]:
            _, c = get_or_create("account.analytic.account",
                                 [("name", "=", brand)],
                                 {"name": brand, "plan_id": plan_id})
            log(f"{'created' if c else 'exists '}: {brand}")
    except Exception as e:
        log(f"skipped analytic setup: {e}")

# ---------------------------------------------------------------- 8. CRM franchise pipeline
if HAS_CRM:
    print("\n8. CRM franchise leads (ICE BSD expo)")
    team_id = x("crm.team", "search", [[]], limit=1)
    leads = [
        ("Franchise inquiry - Bpk Hendra (Surabaya)", 250000000),
        ("Franchise inquiry - Ibu Ratna (Bandung)", 250000000),
        ("Franchise inquiry - Bpk Wijaya (Medan, 2 outlets)", 500000000),
    ]
    for name, revenue in leads:
        _, c = get_or_create("crm.lead", [("name", "=", name)],
                             {"name": name, "type": "opportunity",
                              "expected_revenue": revenue,
                              "team_id": team_id[0] if team_id else False,
                              "description": "Met at ICE BSD franchise expo. Interested in vending machine outlet package."})
        log(f"{'created' if c else 'exists '}: {name}")

# ---------------------------------------------------------------- 9. Sample transactions
print("\n9. Sample transactions")
today = date.today()

# Purchase order for fruit
try:
    orange_v = x("product.product", "search", [[("product_tmpl_id", "=", fruit_ids["Orange (Sunkist)"])]], limit=1)
    mango_v = x("product.product", "search", [[("product_tmpl_id", "=", fruit_ids["Mango (Harum Manis)"])]], limit=1)
    po_exists = x("purchase.order", "search",
                  [[("partner_id", "=", vendor_ids["CV Segar Buah Nusantara"]), ("origin", "=", "KJ-DEMO")]], limit=1)
    if not po_exists:
        x("purchase.order", "create", [{
            "partner_id": vendor_ids["CV Segar Buah Nusantara"],
            "origin": "KJ-DEMO",
            "order_line": [
                (0, 0, {"product_id": orange_v[0], "product_qty": 50}),
                (0, 0, {"product_id": mango_v[0], "product_qty": 30}),
            ]}])
        log("created: draft PO to CV Segar Buah Nusantara (50kg orange, 30kg mango)")
    else:
        log("exists : demo PO")
except Exception as e:
    log(f"skipped PO: {e}")

# Sales orders to franchisees
try:
    for outlet in ["K-Juice Neo Soho Mall", "K-Juice Mall Kelapa Gading 3"]:
        so_exists = x("sale.order", "search",
                      [[("partner_id", "=", outlet_ids[outlet]), ("origin", "=", "KJ-DEMO")]], limit=1)
        if so_exists:
            log(f"exists : demo SO for {outlet}")
            continue
        lines = []
        for jname in ["Orange Booster 16oz", "Mango Booster 16oz", "Green Detox 16oz"]:
            jv = x("product.product", "search", [[("product_tmpl_id", "=", juice_ids[jname][0])]], limit=1)
            lines.append((0, 0, {"product_id": jv[0], "product_uom_qty": 40}))
        x("sale.order", "create", [{"partner_id": outlet_ids[outlet], "origin": "KJ-DEMO",
                                    "order_line": lines}])
        log(f"created: draft SO for {outlet} (weekly juice replenishment)")
except Exception as e:
    log(f"skipped SO: {e}")

# Manufacturing order
if HAS_MRP:
    try:
        jv = x("product.product", "search", [[("product_tmpl_id", "=", juice_ids["Orange Booster 16oz"][0])]], limit=1)
        bom = x("mrp.bom", "search", [[("product_tmpl_id", "=", juice_ids["Orange Booster 16oz"][0])]], limit=1)
        mo_exists = x("mrp.production", "search", [[("origin", "=", "KJ-DEMO")]], limit=1)
        if not mo_exists and jv and bom:
            x("mrp.production", "create", [{"product_id": jv[0], "product_qty": 100,
                                            "bom_id": bom[0], "origin": "KJ-DEMO"}])
            log("created: draft MO - 100x Orange Booster (central kitchen batch)")
        else:
            log("exists : demo MO (or BoM missing)")
    except Exception as e:
        log(f"skipped MO: {e}")

print("\nDone. Open Odoo and review: Products, BoMs, Contacts, CRM pipeline,")
print("draft PO/SO/MO tagged KJ-DEMO. Confirm them live during the demo to show the flow.")
