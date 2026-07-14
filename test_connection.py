"""Smoke test for the Odoo connection.

Usage:
    cp .env.example .env   # fill in credentials
    python test_connection.py
"""

import sys

from odoo_client import OdooClient, OdooConfigError


def main() -> int:
    try:
        client = OdooClient.from_env()
    except OdooConfigError as exc:
        print(f"Configuration error: {exc}")
        return 1

    print(f"Connecting to {client.url} (db: {client.db}) ...")

    info = client.version()
    print(f"Server version: {info.get('server_version')}")

    uid = client.uid
    print(f"Authenticated as {client.username} (uid={uid})")

    partners = client.search_read(
        "res.partner", fields=["name", "email"], limit=5
    )
    print(f"Sample partners ({len(partners)}):")
    for p in partners:
        print(f"  - {p['name']} <{p.get('email') or 'no email'}>")

    print("Connection OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
