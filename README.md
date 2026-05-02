# Club Finance & Inventory Tracker

A Flask-based prototype for managing club finances, inventory, documents, and events. 

This project aims to provide a single-pane-of-glass for committee members (e.g. Treasurers, Captains) to manage annual budgets, log expenses with linked receipts, track asset status, and keep an audit log of changes.

## Key Features
- **Budgets by Year:** Create and manage annual budgets. The UI automatically highlights remaining funds.
- **Transactions + Receipts:** Log expenses in multiple currencies. Link them to documents (receipts), events, and assets.
- **Assets & Status:** Manage club inventory, tracking quantity, location, and condition (Fine, Damaged, Lost).
- **Events:** Keep a record of club events and associate related expenses to easily see total event spend.
- **Audit Logging:** Built-in tracker logs changes (creates, updates, deletes) to essential records for accountability.
- **Currency Display:** Switch UI viewing currency easily. Costs are auto-converted via an external exchange rate API.

## Project Structure
- `src/routes/` - Route blueprints (auth, dashboard, expenses, assets, etc.)
- `src/models.py` - SQLAlchemy database schemas
- `src/templates/` - Jinja2 HTML templates using Bootstrap 5
- `src/services/` - External integrations (e.g. exchange rates)
- `src/utils/` - Helpers for uploads, currency, and config
- `src/data/` - SQLite database location (`cmp.db`)
- `src/static/uploads/` - Default directory for uploaded document files

## Quickstart (Local)

1. Ensure Python 3.11+ is installed.
2. We use [`uv`](https://github.com/astral-sh/uv) for fast dependency management. Install it if you haven't.
3. Install dependencies and start the app:

```bash
uv sync
uv run python -m src.app
```

The application will be available at `http://localhost:5000`.

## Quickstart (Docker)

See [README.Docker.md](README.Docker.md) for detailed Docker documentation.

```bash
docker compose up --build
```

## Demo Mode / Admin Reset
As a prototype, this app can be reset at any time to an initial "Demo State".
1. Go to **Settings**.
2. Scroll down to **Admin Options (Prototype)**.
3. Type `RESET` and submit.

**Note:** This is a destructive action. It will drop the database, clear the `uploads/` folder, and recreate everything with seeded demo data (including `Jay` (Treasurer) and `Skipper` (Captain) accounts, demo budgets, assets, and dummy transactions).

## Testing

The project uses `pytest`. Tests run automatically in CI. To run tests locally:
```bash
uv run pytest
```

## Known Limitations (Prototype Scope)
- **Security:** Security is minimal by design. There are no strict role-based access checks blocking routes entirely, and password recovery is not implemented.
- **External Dependency:** The exchange rate feature relies on a public API (`open.er-api.com`). If it goes down, the app falls back to a 1.0 ratio.
- **Documentation:** The `docs/` folder contains *initial planning/design notes* which may not perfectly reflect the finalized prototype implementation. The code is the ultimate source of truth.