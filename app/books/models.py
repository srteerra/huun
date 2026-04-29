import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.utcnow()


class BookStatus(StrEnum):
    initializing = "initializing"
    ready = "ready"
    generating = "generating"
    completed = "completed"
    error = "error"


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    genre: str
    user_prompt: str | None = None
    title: str | None = None
    total_chapters: int = Field(default=20)
    current_chapter: int = Field(default=0)
    reading_chapter: int = Field(default=1)
    status: BookStatus = Field(default=BookStatus.initializing)
    blueprint: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    state: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Chapter(SQLModel, table=True):
    __tablename__ = "chapters"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    book_id: str = Field(foreign_key="books.id", index=True)
    chapter_number: int
    title: str | None = None
    text: str
    summary: str
    created_at: datetime = Field(default_factory=utcnow)
