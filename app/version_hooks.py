"""
version_hooks.py
----------------
Registers a SQLAlchemy Session-level `before_flush` event that automatically
creates a NoteVersion snapshot whenever a Note's title or content is about to
be overwritten.

This module must be imported ONCE after the FastAPI app is created so that the
event listener is registered for the shared Session factory.  See main.py.
"""

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session


def register_version_hooks() -> None:
    """
    Call this once at application start-up (e.g. in main.py) to attach the
    before_flush listener to every SQLAlchemy Session in this process.
    """
    # Lazy import to avoid circular dependencies at module load time.
    from app.models.models import Note, NoteVersion  # noqa: F401

    @event.listens_for(Session, "before_flush")
    def _capture_note_version(session, flush_context, instances):  # noqa: ANN001
        """
        Fires before every session.flush() / session.commit().
        For every dirty Note whose title or content changed, persist the
        *old* values as a new NoteVersion row.

        Notes that set  `_skip_version_hook = True`  (e.g. the restore
        endpoint, which manually controls snapshot creation) are skipped so
        we never end up with duplicate snapshots.
        """
        for obj in list(session.dirty):
            if not isinstance(obj, Note):
                continue

            # Let restore endpoint opt out of auto-snapshot
            if getattr(obj, "_skip_version_hook", False):
                continue

            state = inspect(obj)
            title_hist = state.attrs.title.history
            content_hist = state.attrs.content.history

            # Only snapshot when the actual text fields changed
            title_changed = bool(title_hist.deleted)
            content_changed = bool(content_hist.deleted)
            if not (title_changed or content_changed):
                continue

            # Recover the previous values (fallback to current if unchanged)
            old_title = title_hist.deleted[0] if title_changed else obj.title
            old_content = content_hist.deleted[0] if content_changed else obj.content

            # Determine the next sequential version number
            existing_count = (
                session.query(NoteVersion)
                .filter(NoteVersion.note_id == obj.id)
                .count()
            )

            snapshot = NoteVersion(
                note_id=obj.id,
                version_number=existing_count + 1,
                title=old_title,
                content=old_content,
            )
            session.add(snapshot)
