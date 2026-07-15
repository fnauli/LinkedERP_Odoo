"""
Publish the CEO dashboard inside Odoo
=====================================
Creates (or updates) a website page at /ceo-dashboard from
scripts/ceo_dashboard_page.html, restricted to signed-in users, and adds a
top-level "CEO Dashboard" menu in the Odoo backend that opens it.
Installs the Website app first if it is missing. Idempotent.
Uses the same env vars as kjuice_demo_seed.py.
"""

import http.client
import os
import ssl
import sys
import xmlrpc.client
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


here = os.path.dirname(os.path.abspath(__file__))
body = open(os.path.join(here, "ceo_dashboard_page.html")).read()
arch = '<t t-name="website.ceo_dashboard">' + body + "</t>"

# 1. Website app
installed = x("ir.module.module", "search",
              [[("name", "=", "website"), ("state", "=", "installed")]], limit=1)
if not installed:
    mid = x("ir.module.module", "search", [[("name", "=", "website")]], limit=1)
    print("Installing Website app (takes a minute)...")
    x("ir.module.module", "button_immediate_install", [mid])
    print("  installed: website")
else:
    print("Website app already installed")

# 2. Page at /ceo-dashboard (signed-in users only)
page = x("website.page", "search", [[("url", "=", "/ceo-dashboard")]], limit=1)
if page:
    view_id = x("website.page", "read", [page, ["view_id"]])[0]["view_id"][0]
    x("ir.ui.view", "write", [[view_id], {"arch_base": arch}])
    print("updated: /ceo-dashboard page content")
else:
    vals = {"name": "CEO Dashboard", "url": "/ceo-dashboard", "type": "qweb",
            "key": "website.ceo_dashboard", "arch_base": arch,
            "is_published": True, "visibility": "connected",
            "website_indexed": False}
    for attempt in range(4):
        try:
            page = [x("website.page", "create", [vals])]
            break
        except xmlrpc.client.Fault as e:
            # tolerate field differences across versions
            dropped = False
            for f in ("visibility", "website_indexed", "is_published"):
                if f in vals and f"'{f}'" in e.faultString:
                    del vals[f]
                    dropped = True
            if not dropped:
                raise
    print("created: /ceo-dashboard page")
    try:
        x("website.page", "write", [page, {"visibility": "connected"}])
    except Exception:
        pass

# 3. Backend menu entry opening the page in a new tab
act = x("ir.actions.act_url", "search", [[("name", "=", "CEO Dashboard")]], limit=1)
if not act:
    act = [x("ir.actions.act_url", "create",
             [{"name": "CEO Dashboard", "url": "/ceo-dashboard", "target": "new"}])]
    print("created: URL action")
menu = x("ir.ui.menu", "search", [[("name", "=", "CEO Dashboard")]], limit=1)
if not menu:
    x("ir.ui.menu", "create",
      [{"name": "CEO Dashboard", "action": f"ir.actions.act_url,{act[0]}", "sequence": 5}])
    print("created: 'CEO Dashboard' app menu in the Odoo backend")
else:
    print("exists : backend menu")

print(f"\nDone. Open {URL}/ceo-dashboard (log in first), or use the 'CEO Dashboard'")
print("entry in the Odoo apps menu.")
