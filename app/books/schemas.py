from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class StorySettings(BaseModel):
    language: str = "es"
    opening_style: Literal["hook", "gradual", "prologue", "mystery"] = "hook"
    pacing: Literal["fast", "moderate", "slow"] = "moderate"
    character_depth: Literal["shallow", "moderate", "deep"] = "moderate"
    perspective: Literal["first_person", "third_limited", "third_omniscient"] = "third_limited"
    tone: Literal["dark", "hopeful", "neutral", "humorous", "suspenseful"] = "neutral"
    world_building: Literal["minimal", "standard", "rich"] = "standard"
    prose_style: Literal["literary", "commercial", "minimalist"] = "commercial"
    content_rating: Literal["family", "teen", "adult"] = "teen"
    words_per_chapter: Literal["short", "medium", "long"] = "medium"


class InitBookRequest(BaseModel):
    genre: str
    user_prompt: Optional[str] = None
    title: Optional[str] = None
    total_chapters: int = 20
    settings: StorySettings = StorySettings()


class BookResponse(BaseModel):
    id: str
    genre: str
    title: Optional[str]
    total_chapters: int
    current_chapter: int
    reading_chapter: int
    status: str
    blueprint: dict
    state: dict
    settings: StorySettings
    user_prompt: Optional[str]
    created_at: datetime
    updated_at: datetime


class ChapterResponse(BaseModel):
    id: str
    book_id: str
    chapter_number: int
    title: Optional[str]
    text: str
    summary: str
    created_at: datetime


class ChapterListResponse(BaseModel):
    chapters: list[ChapterResponse]
    total_generated: int
    limit: int
    offset: int


class UpdateReadingChapterRequest(BaseModel):
    chapter_number: int
