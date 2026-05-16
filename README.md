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
| POST | /register | ❌ | Register new user |
| POST | /login | ❌ | Login, get JWT token |
| GET | /notes | ✅ | Get all notes (paginated, searchable) |
| GET | /notes/{id} | ✅ | Get one note |
| POST | /notes | ✅ | Create a note |
| PUT | /notes/{id} | ✅ | Update a note |
| DELETE | /notes/{id} | ✅ | Delete a note |
| POST | /notes/{id}/share | ✅ | Share note with another user |
| PATCH | /notes/{id}/pin | ✅ | Pin/unpin a note (custom feature) |
| GET | /notes?q=keyword | ✅ | Full-text search |
| GET | /notes?page=1&page_size=20 | ✅ | Paginated notes |
| GET | /about | ❌ | About the developer |
| GET | /openapi.json | ❌ | OpenAPI spec |

---

## Custom Feature: Pin Notes 📌

`PATCH /notes/{id}/pin` with body `{"is_pinned": true}`

Pinned notes always appear at the top of `GET /notes`, just like Google Keep. Only the note owner can pin/unpin.

---

## Deploying to Render (Step by Step)

### Step 1 – Push to GitHub
```bash
git init
git add .
git commit -m "initial commit"
# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/notes-app.git
git push -u origin main
```

### Step 2 – Deploy on Render
1. Go to https://render.com and sign up (free)
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repo
4. Render reads `render.yaml` and auto-creates:
   - A web service (your FastAPI app)
   - A free PostgreSQL database
5. Click **Deploy** — done!

### Step 3 – Get your URL
Your app will be live at: `https://notes-app-XXXX.onrender.com`

> **Note:** The free Render plan spins down after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up. This is normal.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | DB connection string | `sqlite:///./notes.db` |
| SECRET_KEY | JWT signing secret | (set in .env) |
| ALGORITHM | JWT algorithm | `HS256` |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token TTL | `60` |

On Render, `DATABASE_URL` and `SECRET_KEY` are set automatically via `render.yaml`.
