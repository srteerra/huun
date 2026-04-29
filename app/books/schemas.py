from datetime import datetime
from typing import Literal

from pydantic import BaseModel, computed_field


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


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @computed_field
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_creation_input_tokens=self.cache_creation_input_tokens + other.cache_creation_input_tokens,
            cache_read_input_tokens=self.cache_read_input_tokens + other.cache_read_input_tokens,
        )


class InitBookRequest(BaseModel):
    genre: str
    user_prompt: str | None = None
    title: str | None = None
    total_chapters: int = 20
    settings: StorySettings = StorySettings()


class BookResponse(BaseModel):
    id: str
    genre: str
    title: str | None
    total_chapters: int
    current_chapter: int
    reading_chapter: int
    status: str
    blueprint: dict
    state: dict
    settings: StorySettings
    user_prompt: str | None
    created_at: datetime
    updated_at: datetime


class ChapterResponse(BaseModel):
    id: str
    book_id: str
    chapter_number: int
    title: str | None
    text: str
    summary: str
    created_at: datetime
    usage: TokenUsage | None = None


class ChapterListResponse(BaseModel):
    chapters: list[ChapterResponse]
    total_generated: int
    limit: int
    offset: int


class UpdateReadingChapterRequest(BaseModel):
    chapter_number: int
