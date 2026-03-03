# Admin Backend

FastAPI backend for API Key application flow and APISIX Consumer sync.

## Directory structure

```
admin-backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, lifespan, init_db
│   ├── config.py         # Settings from env (DATABASE_URL, APISIX_*, ADMIN_API_KEY)
│   ├── database.py       # Engine, SessionLocal, get_db, init_db
│   ├── models/           # SQLAlchemy: User, ApiKeyApplication, ApiCredential
│   ├── schemas/          # Pydantic: ApplicationCreate/Response, CredentialResponse, etc.
│   ├── services/         # application.py, credential.py, apisix.py (APISIX client)
│   └── api/
│       ├── deps.py       # get_db_session, require_admin (X-Admin-Key)
│       └── routes/       # applications.py, credentials.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

## Environment

Copy `.env.example` to `.env` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No | Default `sqlite:///./admin.db` |
| `APISIX_ADMIN_URL` | Yes* | APISIX Admin API base URL (e.g. `http://127.0.0.1:9180`) |
| `APISIX_ADMIN_KEY` | Yes* | APISIX Admin API key (X-API-KEY). Required for approve/quota/disable/enable. |
| `ADMIN_API_KEY` | No | If set, admin endpoints require header `X-Admin-Key: <value>`. |

\* Required when using approve, quota update, disable, or enable (APISIX sync).

## Run

```bash
# From project root
cd admin-backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

## API Summary

- `POST /api/v1/applications` — Submit application (user).
- `GET /api/v1/applications` — List applications (admin; optional `?status=pending`).
- `POST /api/v1/applications/{id}/approve` — Approve and create Key + APISIX Consumer (admin).
- `POST /api/v1/applications/{id}/reject` — Reject (admin).
- `GET /api/v1/credentials` — List credentials (admin).
- `PATCH /api/v1/credentials/{id}/quota` — Update quota (admin); body: `{"quota_per_minute": 30}`.
- `PATCH /api/v1/credentials/{id}/disable` — Disable key (admin).
- `PATCH /api/v1/credentials/{id}/enable` — Enable key (admin).

Admin endpoints require `X-Admin-Key` header when `ADMIN_API_KEY` is set.

## Docker

```bash
docker build -t admin-backend .
docker run -p 8000:8000 --env-file .env admin-backend
```
