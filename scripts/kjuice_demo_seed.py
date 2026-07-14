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
import json
import os
import re
import ssl
import sys
import urllib.request
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
try:
    uid = common.authenticate(DB, USER, KEY, {})
except xmlrpc.client.Fault as e:
    sys.exit(f"Authentication error from server (db={DB!r}, user={USER!r}): {e.faultString}")
if not uid:
    print(f"Authentication failed (db={DB!r}, user={USER!r}).")
    try:
        print("Server version:", common.version().get("server_version"))
    except Exception as e:
        print("Could not read server version:", e)
    try:
        dbs = _server_proxy(f"{URL}/xmlrpc/2/db").list()
        print("Databases visible on this server:", dbs)
    except Exception:
        print("Database listing is disabled on this server (normal for Odoo Online).")
    sys.exit("Check that the login email matches the Odoo user the API key belongs to, "
             "and that the key was created on this database.")
models = _server_proxy(f"{URL}/xmlrpc/2/object")


def jx(model, method, args=None):
    """Like x() but over JSON-RPC: needed for methods that return None,
    which XML-RPC refuses to marshal (e.g. stock.quant.action_apply_inventory)."""
    cafile = (os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
              or os.environ.get("CURL_CA_BUNDLE"))
    payload = {"jsonrpc": "2.0", "method": "call", "id": 1,
               "params": {"service": "object", "method": "execute_kw",
                          "args": [DB, uid, KEY, model, method, args or []]}}
    req = urllib.request.Request(f"{URL}/jsonrpc", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ssl.create_default_context(cafile=cafile)) as resp:
        body = json.loads(resp.read())
    if body.get("error"):
        raise RuntimeError(body["error"].get("data", {}).get("message") or str(body["error"]))
    return body.get("result")


def x(model, method, args=None, **kw):
    # callers pass the positional-args list directly (Odoo execute_kw convention);
    # wrapping it again would double-nest search domains, which Odoo 19 rejects
    return models.execute_kw(DB, uid, KEY, model, method, args or [], kw)


def module_installed(name):
    return bool(x("ir.module.module", "search",
                  [[("name", "=", name), ("state", "=", "installed")]], limit=1))


def get_or_create(model, domain, vals):
    ids = x(model, "search", [domain], limit=1)
    if ids:
        return ids[0], False
    # fields differ between Odoo versions/installed apps: drop any field the
    # server rejects as invalid and retry, instead of failing the whole seed
    vals = dict(vals)
    for _ in range(10):
        try:
            return x(model, "create", [vals]), True
        except xmlrpc.client.Fault as e:
            m = re.search(r"Invalid field '([^']+)'", e.faultString)
            if m and m.group(1) in vals:
                print(f"    note: field {m.group(1)!r} not available on {model}, skipped")
                del vals[m.group(1)]
                continue
            raise
    raise RuntimeError(f"could not create {model} record after dropping invalid fields")


def log(msg):
    print(f"  {msg}")


print(f"Connected to {URL} as uid {uid}\n")

# Install apps the demo story needs (safe to re-run; skips installed ones)
for app in ("crm",):
    try:
        if not module_installed(app):
            mid = x("ir.module.module", "search", [[("name", "=", app)]], limit=1)
            if mid:
                print(f"Installing app: {app} (takes a moment)...")
                x("ir.module.module", "button_immediate_install", [mid])
                print(f"  installed: {app}")
    except Exception as e:
        print(f"  could not install {app}: {e}")

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

# ---------------------------------------------------------------- 0. Settings
print("0. Settings (lots, expiration dates, analytic accounting)")
try:
    vals = {"group_stock_production_lot": True, "group_analytic_accounting": True}
    if not module_installed("product_expiry"):
        vals["module_product_expiry"] = True
    sid = x("res.config.settings", "create", [vals])
    x("res.config.settings", "execute", [[sid]])
    log("enabled: Lots & Serial Numbers, Expiration Dates, Analytic Accounting")
except Exception as e:
    log(f"skipped settings (enable 'Expiration Dates' / 'Analytic Accounting' manually): {e}")

# ---------------------------------------------------------------- 1. Product categories
print("\n1. Product categories")
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

# ---------------------------------------------------------------- helpers (phase 2)
def variant_of(tmpl_id):
    v = x("product.product", "search", [[("product_tmpl_id", "=", tmpl_id)]], limit=1)
    return v[0] if v else False


def analytic_id(name):
    ids = x("account.analytic.account", "search", [[("name", "=", name)]], limit=1)
    return ids[0] if ids else False


# ---------------------------------------------------------------- 10. Stock on hand (lots + expiry)
print("\n10. Stock on hand with lots & expiry dates")
try:
    wh = x("stock.warehouse", "search_read", [[]], fields=["lot_stock_id"], limit=1)
    stock_loc = wh[0]["lot_stock_id"][0]
    lot_plans = {
        "Orange (Sunkist)": [("LOT-ORG-A", 40, 6), ("LOT-ORG-B", 15, 2)],
        "Mango (Harum Manis)": [("LOT-MGO-A", 35, 5), ("LOT-MGO-B", 10, 1)],
        "Watermelon": [("LOT-WML-A", 60, 6)],
        "Strawberry": [("LOT-STB-A", 20, 4), ("LOT-STB-B", 8, 2)],
        "Pineapple": [("LOT-PNA-A", 30, 5)],
        "Green Apple": [("LOT-APL-A", 25, 7)],
        "Carrot": [("LOT-CRT-A", 30, 7)],
        "Celery": [("LOT-CLY-A", 12, 3)],
        "Dragon Fruit": [("LOT-DGF-A", 18, 5)],
        "Banana (Cavendish)": [("LOT-BNN-A", 25, 4)],
    }
    for fruit, lots in lot_plans.items():
        pv = variant_of(fruit_ids[fruit])
        for lot_name, qty, days_left in lots:
            if x("stock.lot", "search", [[("name", "=", lot_name)]], limit=1):
                log(f"exists : lot {lot_name}")
                continue
            exp = (today + timedelta(days=days_left)).strftime("%Y-%m-%d 12:00:00")
            lot = x("stock.lot", "create", [{"name": lot_name, "product_id": pv,
                                             "expiration_date": exp}])
            q = x("stock.quant", "create", [{"product_id": pv, "location_id": stock_loc,
                                             "lot_id": lot, "inventory_quantity": qty}])
            jx("stock.quant", "action_apply_inventory", [[q]])
            log(f"created: {qty} kg {fruit} in {lot_name} (expires in {days_left}d)")
    for pack, qty in [("Cup 16oz (K-Juice branded)", 2500), ("Dome Lid", 2500), ("Paper Straw", 3000)]:
        pv = variant_of(pack_ids[pack])
        if x("stock.quant", "search",
             [[("product_id", "=", pv), ("location_id", "=", stock_loc), ("quantity", ">", 0)]], limit=1):
            log(f"exists : stock for {pack}")
            continue
        q = x("stock.quant", "create", [{"product_id": pv, "location_id": stock_loc,
                                         "inventory_quantity": qty}])
        jx("stock.quant", "action_apply_inventory", [[q]])
        log(f"created: {qty} pcs {pack}")
except Exception as e:
    log(f"skipped stock: {e}")

# ---------------------------------------------------------------- 11. Juice standard costs (from BoM)
print("\n11. Juice production costs (standard price from recipe + packaging)")
fruit_cost = dict(fruits)
pack_cost = sum(c for _, c in packaging)
for name, price, recipe in juices:
    try:
        cost = round(sum(fruit_cost[f] * q for f, q in recipe) + pack_cost)
        x("product.template", "write", [[juice_ids[name][0]], {"standard_price": cost}])
        log(f"set    : {name} cost Rp {cost:,} (sale Rp {price:,}, margin Rp {price - cost:,})")
    except Exception as e:
        log(f"skipped cost for {name}: {e}")

# ---------------------------------------------------------------- 12. Posted bills & invoices per brand
print("\n12. Posted vendor bills & customer invoices with brand analytics")
kjuice_aa = analytic_id("K-Juice Booster")
bakmie_aa = analytic_id("Bakmie Booster")


def make_move(ref, move_type, partner_id, inv_date, lines):
    if x("account.move", "search", [[("ref", "=", ref)]], limit=1):
        log(f"exists : {ref}")
        return
    mid = x("account.move", "create", [{
        "move_type": move_type, "partner_id": partner_id, "ref": ref,
        "invoice_date": inv_date.strftime("%Y-%m-%d"),
        "invoice_line_ids": [(0, 0, l) for l in lines]}])
    x("account.move", "action_post", [[mid]])
    log(f"posted : {ref}")


def acct(acct_type):
    ids = x("account.account", "search", [[("account_type", "=", acct_type)]], limit=1)
    return ids[0] if ids else False


try:
    dist_kj = {str(kjuice_aa): 100} if kjuice_aa else False
    dist_bb = {str(bakmie_aa): 100} if bakmie_aa else False

    # K-Juice: fruit & packaging purchases (COGS side of the brand report)
    for i, (days_ago, flines) in enumerate([
        (60, [("Orange (Sunkist)", 120, 28000), ("Mango (Harum Manis)", 90, 32000)]),
        (30, [("Strawberry", 40, 65000), ("Pineapple", 80, 15000), ("Watermelon", 100, 12000)]),
        (7,  [("Orange (Sunkist)", 100, 28500), ("Green Apple", 50, 42000), ("Celery", 20, 25000)]),
    ], 1):
        lines = [{"product_id": variant_of(fruit_ids[f]), "quantity": q, "price_unit": p,
                  "analytic_distribution": dist_kj} for f, q, p in flines]
        make_move(f"KJ-DEMO-BILL-{i}", "in_invoice",
                  vendor_ids["CV Segar Buah Nusantara"], today - timedelta(days=days_ago), lines)
    lines = [{"product_id": variant_of(pack_ids[p]), "quantity": q, "price_unit": pu,
              "analytic_distribution": dist_kj}
             for p, q, pu in [("Cup 16oz (K-Juice branded)", 5000, 900),
                              ("Dome Lid", 5000, 300), ("Paper Straw", 5000, 150)]]
    make_move("KJ-DEMO-BILL-4", "in_invoice",
              vendor_ids["UD Tani Makmur (packaging)"], today - timedelta(days=20), lines)

    # K-Juice: weekly juice sales invoices to franchisee outlets
    inv_no = 1
    for days_ago in (56, 42, 28, 14, 7, 2):
        for outlet in ["K-Juice Neo Soho Mall", "K-Juice Mall Kelapa Gading 3", "K-Juice Central Park"]:
            lines = [{"product_id": variant_of(juice_ids[j][0]), "quantity": qty, "price_unit": pr,
                      "analytic_distribution": dist_kj}
                     for j, qty, pr in [("Orange Booster 16oz", 60, 35000),
                                        ("Mango Booster 16oz", 45, 38000),
                                        ("Green Detox 16oz", 30, 42000)]]
            make_move(f"KJ-DEMO-INV-{inv_no}", "out_invoice",
                      outlet_ids[outlet], today - timedelta(days=days_ago), lines)
            inv_no += 1

    # Bakmie Booster: second brand so per-brand comparison has data
    bb_vendor, _ = get_or_create("res.partner", [("name", "=", "CV Mie Sejahtera")],
                                 {"name": "CV Mie Sejahtera", "is_company": True, "supplier_rank": 1})
    bb_customer, _ = get_or_create("res.partner", [("name", "=", "Bakmie Booster PIK Outlet")],
                                   {"name": "Bakmie Booster PIK Outlet", "is_company": True,
                                    "customer_rank": 1})
    exp_acc, inc_acc = acct("expense"), acct("income")
    for i, (days_ago, amount) in enumerate([(45, 4000000), (15, 3500000)], 1):
        make_move(f"BB-DEMO-BILL-{i}", "in_invoice", bb_vendor, today - timedelta(days=days_ago),
                  [{"name": "Noodle & ingredient supplies", "quantity": 1, "price_unit": amount,
                    "account_id": exp_acc, "analytic_distribution": dist_bb}])
    for i, (days_ago, amount) in enumerate([(40, 6500000), (10, 7200000)], 1):
        make_move(f"BB-DEMO-INV-{i}", "out_invoice", bb_customer, today - timedelta(days=days_ago),
                  [{"name": "Weekly bakmie sales", "quantity": 1, "price_unit": amount,
                    "account_id": inc_acc, "analytic_distribution": dist_bb}])
except Exception as e:
    log(f"skipped bills/invoices: {e}")

# ---------------------------------------------------------------- 13. Confirm demo documents
print("\n13. Confirm demo PO / SO")
try:
    po = x("purchase.order", "search", [[("origin", "=", "KJ-DEMO"), ("state", "=", "draft")]])
    if po:
        x("purchase.order", "button_confirm", [po])
        log("confirmed: fruit PO (receipt now waiting in Inventory)")
    so = x("sale.order", "search", [[("origin", "=", "KJ-DEMO"), ("state", "=", "draft")]])
    if so:
        x("sale.order", "action_confirm", [so])
        log(f"confirmed: {len(so)} outlet SO(s) (deliveries now waiting)")
    if not po and not so:
        log("exists : documents already confirmed")
except Exception as e:
    log(f"skipped confirmations: {e}")

# ---------------------------------------------------------------- 14. Manufacturing with cost data
if HAS_MRP:
    print("\n14. Manufacturing orders (production cost demo)")
    try:
        mo_rec = x("mrp.production", "search_read",
                   [[("origin", "=", "KJ-DEMO"),
                     ("state", "in", ["draft", "confirmed", "progress", "to_close"])]],
                   fields=["state"], limit=1)
        if mo_rec:
            mo = [mo_rec[0]["id"]]
            try:
                x("mrp.production", "write", [mo, {"analytic_distribution": {str(kjuice_aa): 100}}])
            except Exception:
                pass
            if mo_rec[0]["state"] == "draft":
                jx("mrp.production", "action_confirm", [mo])
            jx("mrp.production", "action_assign", [mo])
            x("mrp.production", "write", [mo, {"qty_producing": 100}])
            res = jx("mrp.production", "button_mark_done", [mo])
            if isinstance(res, dict):
                log(f"MO reserved but needs a click to finish live in the demo ({res.get('res_model', 'wizard')})")
            else:
                log("done   : 100x Orange Booster produced (see MO > Cost Analysis)")
        else:
            log("exists : Orange Booster MO already processed")
        # a second MO left in progress for the pipeline view
        if not x("mrp.production", "search", [[("origin", "=", "KJ-DEMO-2")]], limit=1):
            jv = variant_of(juice_ids["Mango Booster 16oz"][0])
            bom = x("mrp.bom", "search", [[("product_tmpl_id", "=", juice_ids["Mango Booster 16oz"][0])]], limit=1)
            mo2 = x("mrp.production", "create", [{"product_id": jv, "product_qty": 80,
                                                  "bom_id": bom[0], "origin": "KJ-DEMO-2"}])
            x("mrp.production", "action_confirm", [[mo2]])
            log("created: 80x Mango Booster MO (confirmed, in progress)")
        else:
            log("exists : Mango Booster MO")
    except Exception as e:
        log(f"skipped manufacturing: {e}")

print("\nDone. Demo tour suggestions:")
print(" - Inventory > Products / Lots: fruit lots with expiry alerts")
print(" - Manufacturing > Orders: completed Orange MO (Cost Analysis) + Mango MO in progress")
print(" - Accounting > Customer Invoices / Vendor Bills: 2 months of posted history")
print(" - Accounting > Reporting > Analytic Report (or P&L filtered by plan 'Brand'):")
print("   K-Juice Booster vs Bakmie Booster revenue & costs")
print(" - CRM: franchise pipeline from the ICE BSD expo")
