"""
CEO Dashboard data extractor
============================
Connects to Odoo over XML-RPC (same env vars as kjuice_demo_seed.py) and prints
one JSON document with company-wide KPIs between marker lines, so a CI job log
can be parsed to build the dashboard.
"""

import http.client
import json
import os
import ssl
import sys
import xmlrpc.client
from datetime import date, timedelta
from urllib.parse import urlparse

URL = os.environ.get("ODOO_URL", "").rstrip("/")
if URL.endswith("/odoo"):
    URL = URL[: -len("/odoo")]
DB = os.environ.get("ODOO_DB", "")
USER = os.environ.get("ODOO_USER", "")
KEY = os.environ.get("ODOO_API_KEY", "")
if URL and not DB and URL.endswith(".odoo.com"):
    DB = urlparse(URL).hostname.split(".")[0]
if not all([URL, DB, USER, KEY]):
    sys.exit("Set ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY first.")


class ProxiedSafeTransport(xmlrpc.client.SafeTransport):
    def __init__(self, proxy_url):
        cafile = (os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
                  or os.environ.get("CURL_CA_BUNDLE"))
        super().__init__(context=ssl.create_default_context(cafile=cafile))
        p = urlparse(proxy_url)
        self.proxy_host, self.proxy_port = p.hostname, p.port or 3128

    def make_connection(self, host):
        if self._connection and host == self._connection[0]:
            return self._connection[1]
        chost, self._extra_headers, _ = self.get_host_info(host)
        conn = http.client.HTTPSConnection(self.proxy_host, self.proxy_port, context=self.context)
        conn.set_tunnel(chost)
        self._connection = host, conn
        return conn


def _proxy(endpoint):
    purl = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if purl and endpoint.startswith("https://"):
        return xmlrpc.client.ServerProxy(endpoint, transport=ProxiedSafeTransport(purl))
    return xmlrpc.client.ServerProxy(endpoint)


uid = _proxy(f"{URL}/xmlrpc/2/common").authenticate(DB, USER, KEY, {})
if not uid:
    sys.exit("Authentication failed.")
models = _proxy(f"{URL}/xmlrpc/2/object")


def x(model, method, args=None, **kw):
    return models.execute_kw(DB, uid, KEY, model, method, args or [], kw)


today = date.today()
data = {"generated": str(today), "errors": {}}


def safe(key, fn):
    try:
        data[key] = fn()
    except Exception as e:
        data[key] = None
        data["errors"][key] = str(e)[:200]


# ---- invoices / bills: monthly revenue & spend, receivables -----------------
def invoices():
    recs = x("account.move", "search_read",
             [[("move_type", "in", ["out_invoice", "in_invoice"]), ("state", "=", "posted")]],
             fields=["move_type", "invoice_date", "amount_total", "amount_residual", "partner_id"])
    monthly, recv, cust = {}, 0.0, {}
    for r in recs:
        month = (r["invoice_date"] or str(today))[:7]
        b = monthly.setdefault(month, {"revenue": 0.0, "spend": 0.0})
        if r["move_type"] == "out_invoice":
            b["revenue"] += r["amount_total"]
            recv += r["amount_residual"]
            pname = r["partner_id"][1] if r["partner_id"] else "?"
            cust[pname] = cust.get(pname, 0.0) + r["amount_total"]
        else:
            b["spend"] += r["amount_total"]
    return {"monthly": [{"month": m, **v} for m, v in sorted(monthly.items())],
            "receivables": recv,
            "top_customers": sorted(cust.items(), key=lambda kv: -kv[1])[:5]}


safe("invoicing", invoices)


# ---- brand analytics ---------------------------------------------------------
def brands():
    lines = x("account.analytic.line", "search_read", [[]], fields=["account_id", "amount"])
    out = {}
    for l in lines:
        name = l["account_id"][1] if l["account_id"] else "?"
        b = out.setdefault(name, {"revenue": 0.0, "cost": 0.0})
        if l["amount"] >= 0:
            b["revenue"] += l["amount"]
        else:
            b["cost"] += -l["amount"]
    return [{"brand": k, **v, "net": v["revenue"] - v["cost"]} for k, v in out.items()]


safe("brands", brands)


# ---- POS outlet performance --------------------------------------------------
def pos():
    sessions = x("pos.session", "search_read", [[]], fields=["config_id", "state"])
    smap = {s["id"]: (s["config_id"][1] if s["config_id"] else "?", s["state"]) for s in sessions}
    orders = x("pos.order", "search_read", [[]], fields=["amount_total", "session_id"])
    outlets = {}
    for o in orders:
        name, state = smap.get(o["session_id"][0], ("?", "?")) if o["session_id"] else ("?", "?")
        b = outlets.setdefault(name, {"orders": 0, "revenue": 0.0, "session_state": state})
        b["orders"] += 1
        b["revenue"] += o["amount_total"]
    lines = x("pos.order.line", "search_read", [[]], fields=["product_id", "qty", "price_subtotal_incl"])
    mix = {}
    for l in lines:
        pname = l["product_id"][1] if l["product_id"] else "?"
        m = mix.setdefault(pname, {"qty": 0.0, "revenue": 0.0})
        m["qty"] += l["qty"]
        m["revenue"] += l["price_subtotal_incl"]
    return {"outlets": [{"outlet": k, **v} for k, v in sorted(outlets.items(), key=lambda kv: -kv[1]["revenue"])],
            "product_mix": sorted(({"product": k, **v} for k, v in mix.items()),
                                  key=lambda d: -d["revenue"])}


safe("pos", pos)


# ---- top products from posted customer invoices -------------------------------
def top_products():
    aml = x("account.move.line", "search_read",
            [[("move_id.move_type", "=", "out_invoice"), ("parent_state", "=", "posted"),
              ("product_id", "!=", False)]],
            fields=["product_id", "price_subtotal", "quantity"])
    agg = {}
    for l in aml:
        p = l["product_id"][1]
        a = agg.setdefault(p, {"revenue": 0.0, "qty": 0.0})
        a["revenue"] += l["price_subtotal"]
        a["qty"] += l["quantity"]
    return sorted(({"product": k, **v} for k, v in agg.items()), key=lambda d: -d["revenue"])[:6]


safe("top_products", top_products)


# ---- inventory: value + expiry risk -------------------------------------------
def inventory():
    quants = x("stock.quant", "search_read", [[("location_id.usage", "=", "internal")]],
               fields=["product_id", "quantity", "lot_id"])
    pids = list({q["product_id"][0] for q in quants})
    prods = {p["id"]: p for p in x("product.product", "read",
                                   [pids, ["standard_price", "name"]])} if pids else {}
    value = sum(q["quantity"] * prods.get(q["product_id"][0], {}).get("standard_price", 0)
                for q in quants)
    lots = x("stock.lot", "search_read", [[("expiration_date", "!=", False)]],
             fields=["name", "product_id", "expiration_date", "product_qty"])
    soon = []
    for l in lots:
        exp = l["expiration_date"][:10]
        days = (date.fromisoformat(exp) - today).days
        if days <= 3 and l["product_qty"] > 0:
            soon.append({"lot": l["name"], "product": l["product_id"][1],
                         "qty": l["product_qty"], "days_left": days})
    return {"stock_value": value, "expiring_lots": sorted(soon, key=lambda d: d["days_left"]),
            "total_lots": len(lots)}


safe("inventory", inventory)


# ---- CRM pipeline --------------------------------------------------------------
def crm():
    leads = x("crm.lead", "search_read", [[("type", "=", "opportunity")]],
              fields=["name", "expected_revenue", "stage_id", "probability"])
    return {"count": len(leads),
            "expected_total": sum(l["expected_revenue"] or 0 for l in leads),
            "leads": [{"name": l["name"], "expected": l["expected_revenue"],
                       "stage": l["stage_id"][1] if l["stage_id"] else "?"} for l in leads]}


safe("crm", crm)


# ---- operations status ----------------------------------------------------------
def operations():
    mos = x("mrp.production", "search_read", [[]], fields=["state", "product_qty", "product_id"])
    sos = x("sale.order", "search_read", [[]], fields=["state", "amount_total"])
    pos_ = x("purchase.order", "search_read", [[]], fields=["state", "amount_total"])

    def by_state(recs):
        out = {}
        for r in recs:
            out[r["state"]] = out.get(r["state"], 0) + 1
        return out

    return {"mo": by_state(mos), "so": by_state(sos), "po": by_state(pos_),
            "so_value": sum(s["amount_total"] for s in sos if s["state"] in ("sale", "done")),
            "po_value": sum(p["amount_total"] for p in pos_ if p["state"] in ("purchase", "done"))}


safe("operations", operations)

print("===DASHBOARD_JSON_BEGIN===")
print(json.dumps(data, default=str))
print("===DASHBOARD_JSON_END===")
