from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.models import User, Note
from app.models.schemas import NoteCreate, NoteUpdate, NoteResponse, ShareNote, PinNote
from app.auth import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/notes", tags=["Notes"])


def get_accessible_note(note_id: str, current_user: User, db: Session) -> Note:
    """Return a note if the user owns it OR it was shared with them."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    is_owner = note.owner_id == current_user.id
    is_shared = any(u.id == current_user.id for u in note.shared_with)

    if not is_owner and not is_shared:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return note


@router.get("", response_model=List[NoteResponse])
def get_all_notes(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Notes per page"),
    q: Optional[str] = Query(default=None, description="Search keyword in title or content"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all notes owned by or shared with the current user. Supports pagination and search."""
    # Combine owned + shared notes
    query = db.query(Note).filter(
        or_(
            Note.owner_id == current_user.id,
            Note.shared_with.any(User.id == current_user.id),
        )
    )

    # Full-text search (stretch goal built-in)
    if q:
        keyword = f"%{q}%"
        query = query.filter(
            or_(Note.title.ilike(keyword), Note.content.ilike(keyword))
        )

    # Pinned notes first, then by updated_at
    query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())

    # Pagination
    total = query.count()
    notes = query.offset((page - 1) * page_size).limit(page_size).all()

    return notes


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_accessible_note(note_id, current_user, db)


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = Note(
        title=payload.title,
        content=payload.content,
        owner_id=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: str,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_accessible_note(note_id, current_user, db)

    # Only owner can edit content
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can edit this note")

    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content

    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you are not the owner",
        )
    db.delete(note)
    db.commit()


@router.post("/{note_id}/share")
def share_note(
    note_id: str,
    payload: ShareNote,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you are not the owner",
        )

    if payload.share_with_email == current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot share a note with yourself")

    target_user = db.query(User).filter(User.email == payload.share_with_email).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that email not found")

    # Avoid duplicate shares
    if any(u.id == target_user.id for u in note.shared_with):
        return {"message": f"Note already shared with {payload.share_with_email}"}

    note.shared_with.append(target_user)
    db.commit()

    return {"message": f"Note successfully shared with {payload.share_with_email}"}


# ── Custom Feature: Pin / Unpin a Note ────────────────────────────────────────

@router.patch("/{note_id}/pin", response_model=NoteResponse)
def pin_note(
    note_id: str,
    payload: PinNote,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pin or unpin a note. Pinned notes always appear at the top of GET /notes.
    Only the owner can pin/unpin.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found or you are not the owner")

    note.is_pinned = "true" if payload.is_pinned else "false"
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note
