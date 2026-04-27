import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


def utcnow() -> datetime:
    return datetime.utcnow()

class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    genre: str
    user_prompt: Optional[str] = None
    title: Optional[str] = None
    total_chapters: int = Field(default=20)
    current_chapter: int = Field(default=0)
    reading_chapter: int = Field(default=1)
    status: str = Field(default="initializing")
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
    title: Optional[str] = None
    text: str
    summary: str
    created_at: datetime = Field(default_factory=utcnow)
