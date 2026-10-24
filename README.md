# Gather — Event & Workshop Portal

Full-stack event and workshop portal built with React + Vite, FastAPI, SQLAlchemy, Alembic, MySQL, and `uv`.

## Requirements

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Node.js 20 or newer
- MySQL 8.x (MySQL Server running locally)

## 1. Create the MySQL database

Open MySQL Workbench or the MySQL command line and run the following SQL. Replace the example password with your own strong password.

```sql
CREATE DATABASE IF NOT EXISTS event_portal
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'event_portal'@'localhost'
  IDENTIFIED BY 'REPLACE_WITH_YOUR_PASSWORD';

GRANT ALL PRIVILEGES ON event_portal.* TO 'event_portal'@'localhost';
FLUSH PRIVILEGES;
```

If your MySQL user connects through `127.0.0.1` rather than `localhost`, create/grant the matching host account too, or use a MySQL account configured to permit that connection. Do not use your MySQL root account in the app.

## 2. Configure and run the backend

Run these commands in **PowerShell** from the project folder:

```powershell
cd backend
Copy-Item .env.example .env
```

Open `backend/.env` and set `DATABASE_URL` to your actual MySQL username, password, host, port, and database name. For example:

```dotenv
DATABASE_URL=mysql+pymysql://event_portal:YOUR_PASSWORD@127.0.0.1:3306/event_portal
```

If your password contains URL-reserved characters such as `@`, `:`, `/`, `#`, or `%`, URL-encode those characters in `DATABASE_URL`. Keep `.env` private; do not commit it.

Generate a JWT secret and paste the result into `JWT_SECRET`:

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Then install dependencies, apply the schema, create the admin account, and start the API:

```powershell
uv sync
uv run alembic upgrade head
uv run python -m app.seed_admin
uv run uvicorn app.main:app --reload
```

The backend should be available at `http://127.0.0.1:8000`. API docs are at `http://127.0.0.1:8000/docs`.

### Verify the database connection

Open `http://127.0.0.1:8000/api/health/db`. A working connection returns:

```json
{"status":"ok","database":"connected"}
```

A `503` response means the API started but could not execute a query. Check that MySQL is running, the database exists, and the values in `backend/.env` match the MySQL account and permissions.

## 3. Configure and run the frontend

Open a **second PowerShell terminal** from the project folder:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The frontend API URL is configured in `frontend/.env` as `VITE_API_BASE_URL=http://127.0.0.1:8000`.

If you use a different frontend port, add that exact origin to `FRONTEND_ORIGINS` in `backend/.env`, then restart the backend.

## 4. Tests

```powershell
cd backend
uv run pytest
```

Set `TEST_DATABASE_URL` to a dedicated test database before adding integration tests. Never run tests against production data.

## Troubleshooting

- **`Access denied for user`**: check the username/password and the MySQL user's host grants.
- **`Unknown database 'event_portal'`**: create the database or correct the database name in `DATABASE_URL`.
- **`Can't connect to MySQL server` / error 2003**: start MySQL Server and confirm the host/port (default `127.0.0.1:3306`).
- **`No module named pymysql`**: run `uv sync` from `backend`.
- **`DATABASE_URL is invalid`**: use the `mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE` format and URL-encode special characters in the password.
- **Frontend says API offline**: keep the backend running and confirm `VITE_API_BASE_URL` points to `http://127.0.0.1:8000`.

## Security notes

- `.env` files contain local secrets and should never be committed.
- The admin account is created with `uv run python -m app.seed_admin`; there is no public admin signup endpoint.
- For production, use HTTPS, `COOKIE_SECURE=true`, a deliberate CSRF strategy, backups, monitoring, and a production threat-model review.
