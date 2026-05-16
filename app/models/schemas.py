from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Notes ─────────────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    title: str
    content: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        return v.strip()

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Title cannot be empty")
            if len(v) > 255:
                raise ValueError("Title cannot exceed 255 characters")
            return v.strip()
        return v


class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    is_pinned: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShareNote(BaseModel):
    share_with_email: EmailStr


# ── Pin Feature ───────────────────────────────────────────────────────────────

class PinNote(BaseModel):
    is_pinned: bool


# ── Note Version History ──────────────────────────────────────────────────────

class NoteVersionResponse(BaseModel):
    id: str
    note_id: str
    version_number: int
    title: str
    content: str
    saved_at: datetime

    model_config = {"from_attributes": True}
