"""Minimal Odoo External API client (XML-RPC).

Reads connection settings from environment variables (see .env.example):
    ODOO_URL       e.g. https://demo-skr.odoo.com
    ODOO_DB        e.g. demo-skr
    ODOO_USERNAME  the Odoo login (email) the API key belongs to
    ODOO_API_KEY   an API key created under Settings > Users > API Keys

Odoo API keys are used in place of the password with the standard
XML-RPC endpoints (/xmlrpc/2/common and /xmlrpc/2/object).
"""

from __future__ import annotations

import os
import xmlrpc.client
from dataclasses import dataclass, field


class OdooConfigError(RuntimeError):
    """Raised when required connection settings are missing."""


@dataclass
class OdooClient:
    url: str
    db: str
    username: str
    api_key: str
    _uid: int | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_env(cls) -> "OdooClient":
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass  # dotenv is optional; plain env vars work too

        missing = [
            name
            for name in ("ODOO_URL", "ODOO_DB", "ODOO_USERNAME", "ODOO_API_KEY")
            if not os.environ.get(name)
        ]
        if missing:
            raise OdooConfigError(
                f"Missing environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in the values."
            )
        return cls(
            url=os.environ["ODOO_URL"].rstrip("/"),
            db=os.environ["ODOO_DB"],
            username=os.environ["ODOO_USERNAME"],
            api_key=os.environ["ODOO_API_KEY"],
        )

    @property
    def common(self) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")

    @property
    def models(self) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def version(self) -> dict:
        """Server version info; works without authentication."""
        return self.common.version()

    @property
    def uid(self) -> int:
        if self._uid is None:
            uid = self.common.authenticate(self.db, self.username, self.api_key, {})
            if not uid:
                raise PermissionError(
                    "Odoo authentication failed: check ODOO_DB, ODOO_USERNAME "
                    "and ODOO_API_KEY."
                )
            self._uid = uid
        return self._uid

    def execute(self, model: str, method: str, *args, **kwargs):
        """Call any model method, e.g. execute('res.partner', 'search_read', [[]], limit=5)."""
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, method, list(args), kwargs
        )

    # Convenience wrappers for the common CRUD verbs -------------------------

    def search_read(self, model: str, domain=None, fields=None, limit=0, offset=0):
        return self.execute(
            model,
            "search_read",
            domain or [],
            fields=fields or [],
            limit=limit,
            offset=offset,
        )

    def create(self, model: str, values: dict) -> int:
        return self.execute(model, "create", [values])

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        return self.execute(model, "write", [ids, values])

    def unlink(self, model: str, ids: list[int]) -> bool:
        return self.execute(model, "unlink", [ids])
