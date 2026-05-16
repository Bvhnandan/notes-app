"""
app/routers/history.py
----------------------
Endpoints for Note Version History.

All endpoints are owner-only — shared users cannot view or restore history.

Routes:
    GET  /notes/{note_id}/history
    GET  /notes/{note_id}/history/{version_number}
    POST /notes/{note_id}/history/{version_number}/restore
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.models import Note, NoteVersion, User
from app.models.schemas import NoteResponse, NoteVersionResponse

router = APIRouter(prefix="/notes", tags=["Note History"])


# ── Private helpers ───────────────────────────────────────────────────────────

def _require_owner(note_id: str, current_user: User, db: Session) -> Note:
    """Return the Note only if current_user is the owner; raise otherwise."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the note owner can access version history",
        )
    return note


def _get_version(note_id: str, version_number: int, db: Session) -> NoteVersion:
    """Fetch a specific NoteVersion or raise 404."""
    version = (
        db.query(NoteVersion)
        .filter(
            NoteVersion.note_id == note_id,
            NoteVersion.version_number == version_number,
        )
        .first()
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_number} not found for this note",
        )
    return version


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/{note_id}/history",
    response_model=List[NoteVersionResponse],
    summary="List all previous versions of a note",
)
def get_note_history(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns every saved snapshot for a note in ascending version order.
    Version 1 is the oldest; the highest version is the most recent snapshot.
    The *current* live content is NOT included — it lives in GET /notes/{id}.
    Owner only.
    """
    _require_owner(note_id, current_user, db)

    versions = (
        db.query(NoteVersion)
        .filter(NoteVersion.note_id == note_id)
        .order_by(NoteVersion.version_number.asc())
        .all()
    )
    return versions


@router.get(
    "/{note_id}/history/{version_number}",
    response_model=NoteVersionResponse,
    summary="Get a specific historical version",
)
def get_note_version(
    note_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the full content of one historical version.
    Owner only.
    """
    _require_owner(note_id, current_user, db)
    return _get_version(note_id, version_number, db)


@router.post(
    "/{note_id}/history/{version_number}/restore",
    response_model=NoteResponse,
    summary="Restore note to a previous version",
)
def restore_note_version(
    note_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Restores the note's title and content to those of the requested version.

    Before overwriting, the *current* live content is saved as a new snapshot
    so no data is ever lost.  The version_hooks `before_flush` listener is
    bypassed for this operation (via `_skip_version_hook`) to prevent a
    duplicate snapshot from being created automatically.

    Returns the updated note (same shape as GET /notes/{id}).
    Owner only.
    """
    note = _require_owner(note_id, current_user, db)
    target = _get_version(note_id, version_number, db)

    # 1. Save the current live state as a new snapshot BEFORE restoring.
    existing_count = (
        db.query(NoteVersion)
        .filter(NoteVersion.note_id == note_id)
        .count()
    )
    pre_restore_snapshot = NoteVersion(
        note_id=note.id,
        version_number=existing_count + 1,
        title=note.title,
        content=note.content,
    )
    db.add(pre_restore_snapshot)

    # 2. Tell the before_flush hook to skip this Note so it doesn't create a
    #    second (duplicate) snapshot when it sees the dirty fields below.
    note._skip_version_hook = True  # type: ignore[attr-defined]

    # 3. Overwrite the live note with the restored content.
    note.title = target.title
    note.content = target.content
    note.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(note)

    # 4. Clear the flag so future edits behave normally.
    note._skip_version_hook = False  # type: ignore[attr-defined]

    return note
