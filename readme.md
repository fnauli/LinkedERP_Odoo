# LinkedERP_Odoo

Integration project for an Odoo instance via the [Odoo External API](https://www.odoo.com/documentation/latest/developer/reference/external_api.html) (XML-RPC).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your credentials
```

`.env` holds the connection settings and is gitignored — never commit real credentials.

| Variable | Description |
|---|---|
| `ODOO_URL` | Instance base URL, e.g. `https://demo-skr.odoo.com` |
| `ODOO_DB` | Database name, e.g. `demo-skr` |
| `ODOO_USERNAME` | The Odoo login (email) the API key belongs to |
| `ODOO_API_KEY` | API key from Settings → Users & Companies → Users → API Keys |

## Verify the connection

```bash
python test_connection.py
```

This prints the server version, authenticates with the API key, and lists a few partner records.

## Usage

```python
from odoo_client import OdooClient

client = OdooClient.from_env()
partners = client.search_read("res.partner", [["is_company", "=", True]],
                              fields=["name", "email"], limit=10)
new_id = client.create("res.partner", {"name": "New Partner"})
```

`client.execute(model, method, *args, **kwargs)` exposes any model method for calls beyond the CRUD helpers.
