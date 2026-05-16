# Notes App API

A multi-user notes backend built with **FastAPI + SQLAlchemy**, supporting JWT authentication, note sharing, pinning, pagination, and full-text search.

---

## Project Structure

```
notes-app/
├── app/
│   ├── main.py          # FastAPI app, /about endpoint
│   ├── database.py      # DB connection (SQLite local / PostgreSQL on Render)
│   ├── auth.py          # JWT helpers, password hashing, get_current_user
│   ├── models/
│   │   ├── models.py    # SQLAlchemy table definitions
│   │   └── schemas.py   # Pydantic request/response schemas
│   └── routers/
│       ├── auth.py      # POST /register, POST /login
│       └── notes.py     # All /notes endpoints
├── requirements.txt
├── render.yaml          # One-click Render deployment config
└── .env.example         # Copy to .env for local dev
```

---

## Local Setup

### 1. Clone and enter the project
```bash
cd notes-app
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Open .env and set your SECRET_KEY (or leave default for local dev)
```

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000
Interactive docs at: http://localhost:8000/docs

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /register | Not Required | Register new user |
| POST | /login | Not Required | Login, get JWT token |
| GET | /notes | Auth Required | Get all notes (paginated, searchable) |
| GET | /notes/{id} | Auth Required | Get one note |
| POST | /notes | Auth Required | Create a note |
| PUT | /notes/{id} | Auth Required | Update a note |
| DELETE | /notes/{id} | Auth Required | Delete a note |
| POST | /notes/{id}/share | Auth Required | Share note with another user |
| PATCH | /notes/{id}/pin | Auth Required | Pin/unpin a note (custom feature) |
| GET | /notes?q=keyword | Auth Required | Full-text search |
| GET | /notes?page=1&page_size=20 | Auth Required | Paginated notes |
| GET | /about | Not Required | About the developer |
| GET | /openapi.json | Not Required | OpenAPI spec |

---

## Custom Feature: Pin Notes 📌

`PATCH /notes/{id}/pin` with body `{"is_pinned": true}`

Pinned notes always appear at the top of `GET /notes`, just like Google Keep. Only the note owner can pin/unpin.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | DB connection string | `sqlite:///./notes.db` |
| SECRET_KEY | JWT signing secret | (set in .env) |
| ALGORITHM | JWT algorithm | `HS256` |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token TTL | `60` |
