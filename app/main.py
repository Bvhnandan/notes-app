from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, notes

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notes App API",
    description="A multi-user notes service with JWT authentication",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(notes.router)
from app.routers import history                        # noqa: E402
from app.version_hooks import register_version_hooks   # noqa: E402
app.include_router(history.router)
register_version_hooks()


@app.get("/about")
def about():
    return {
        "name": "Venkata Harsha Nandan Billala",
        "email": "harshanandan022@gmail.com",
        "my_features": {
            "Pin Notes": (
                "PATCH /notes/{id}/pin — Users can pin important notes so they "
                "always appear at the top of GET /notes. Only the owner can pin/unpin. "
                "Chosen because it's a real productivity feature in Google Keep and Apple Notes."
            ),
            "Pagination": (
                "GET /notes supports ?page=1&page_size=20 so large note lists "
                "don't overload the response."
            ),
            "Full-text Search": (
                "GET /notes?q=keyword searches across note titles and content "
                "for fast retrieval."
            ),
        },
    }


@app.get("/search")
def search_notes(q: str, db=None):
    """Redirect: use GET /notes?q=keyword for search."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/notes?q={q}")
