# Database Plan

## Tables:

- User(id INTEGER PK, username TEXT, password TEXT, role TEXT)

- Budget(id INTEGER PK, year INTEGER, total_amount REAL)

- Asset(id INTEGER PK, name TEXT, location TEXT, status TEXT)

- Transaction(id INTEGER PK, amount REAL, category TEXT, budget_id INTEGER REFERENCES Budget(id), receipt_path TEXT)



