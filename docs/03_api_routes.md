# API ROUTES


Auth
- `GET /` -> `login.html` (if session exists, redirect to `/dashboard`)
- `POST /login` -> validate credentials, set session, redirect `/dashboard`
- `GET /logout` -> clear session, redirect `/`

Dashboard
- `GET /dashboard` -> `dashboard.html` 

Expenses
- `GET /expenses` -> `expenses.html` 
- `POST /expenses/new` -> create transaction, save receipt, redirect `/expenses` or `/dashboard`

Inventory
- `GET /inventory` -> `inventory.html` 
- `POST /inventory/new` -> create asset , redirect `/inventory`
- `POST /inventory/update/<id>` -> update asset, redirect `/inventory`

Documents
- `GET /documents` -> `documents.html` 
- `POST /documents/upload` -> upload file, attach to transaction or store standalone, redirect `/documents`
- `GET /documents/download/<filename>` -> serve file securely

Settings
- `GET /settings` -> `settings.html` 
- `POST /settings/update` -> apply changes, redirect `/settings`

