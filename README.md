# Expense Tracker (BFF Architecture)

This project uses a **BFF (Backend-for-Frontend)** architecture:

- **Backend**: Django API that stores transfers, expenses, bills, and headless-import profiles.
- **Frontend**: React app that consumes the Django API.
- **Worker**: A placeholder headless browser worker stub for scraping store apps (Auchan, Lidl Plus).

## Backend (Django)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

API endpoints:

- `GET /api/summary/<month>/`
- `GET|POST /api/categories/`
- `GET|POST /api/transfers/`
- `GET|POST /api/expenses/`
- `GET|POST /api/bills/`
- `GET|POST /api/imports/`
- `POST /api/imports/<id>/queue/`

## Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Headless browser worker

`worker/headless_stub.py` is a placeholder. Replace with Playwright/Selenium logic to log in
and pull digital bills from retailer apps, then POST them into the Django API.
