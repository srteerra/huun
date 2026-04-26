from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InitBookRequest(BaseModel):
    genre: str
    user_prompt: Optional[str] = None
    total_partitions: int = 20


class BookResponse(BaseModel):
    id: str
    genre: str
    total_partitions: int
    current_partition: int
    reading_partition: int
    status: str
    blueprint: dict
    state: dict
    user_prompt: Optional[str]
    created_at: datetime
    updated_at: datetime


class PartitionResponse(BaseModel):
    id: str
    book_id: str
    partition_number: int
    text: str
    summary: str
    created_at: datetime


class PartitionListResponse(BaseModel):
    partitions: list[PartitionResponse]
    total_generated: int
    limit: int
    offset: int


class UpdateReadingPartitionRequest(BaseModel):
    partition_number: int
