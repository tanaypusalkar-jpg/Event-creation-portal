# Fix notes

Copy the files in this zip over the same paths in your project (backend/ only; nothing in frontend/ changed).

New:     backend/app/routers/{__init__,auth,events,admin}.py, app/deps.py, app/services.py, app/limiter.py, tests/test_api.py
Changed: backend/app/main.py  (routers registered, /api/health/db added, CORS allows localhost AND 127.0.0.1)

Then, in backend/:
  1. Set a real JWT_SECRET in .env (uv run python -c "import secrets; print(secrets.token_urlsafe(48))")
  2. uv run alembic upgrade head
  3. uv run python -m app.seed_admin
  4. uv run uvicorn app.main:app --reload
  5. Check http://127.0.0.1:8000/docs and http://127.0.0.1:8000/api/health/db
Frontend: npm run dev, then sign in and create an event from the Admin workspace (the demo cards are read-only).
