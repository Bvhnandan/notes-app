import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# Association table for note sharing (many-to-many: notes <-> users)
note_shares = Table(
    "note_shares",
    Base.metadata,
    Column("note_id", String, ForeignKey("notes.id"), primary_key=True),
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Notes owned by this user
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    # Notes shared with this user
    shared_notes = relationship("Note", secondary=note_shares, back_populates="shared_with")


class Note(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_pinned = Column(String, default="false")  # Custom feature: pin notes
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="notes")
    shared_with = relationship("User", secondary=note_shares, back_populates="shared_notes")
    versions = relationship(
        "NoteVersion",
        back_populates="note",
        cascade="all, delete-orphan",
        order_by="NoteVersion.version_number",
    )


class NoteVersion(Base):
    __tablename__ = "note_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(
        String, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number = Column(Integer, nullable=False)  # 1 = oldest snapshot
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    saved_at = Column(DateTime(timezone=True), default=utcnow)

    note = relationship("Note", back_populates="versions")
