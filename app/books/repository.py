from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select as sm_select

from app.books.models import Book, Partition


class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, genre: str, user_prompt: Optional[str], total_partitions: int) -> Book:
        book = Book(genre=genre, user_prompt=user_prompt, total_partitions=total_partitions)
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def get_by_id(self, book_id: str) -> Optional[Book]:
        result = await self.session.execute(sm_select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()

    async def save_blueprint(self, book_id: str, blueprint: dict) -> None:
        book = await self.get_by_id(book_id)
        book.blueprint = blueprint
        book.status = "ready"
        await self.session.commit()

    async def save_state(self, book_id: str, state: dict) -> None:
        book = await self.get_by_id(book_id)
        book.state = state
        await self.session.commit()

    async def update_status(self, book_id: str, status: str) -> None:
        book = await self.get_by_id(book_id)
        book.status = status
        await self.session.commit()

    async def save_partition(
            self, book_id: str, number: int, text: str, summary: str
    ) -> Partition:
        partition = Partition(
            book_id=book_id, partition_number=number, text=text, summary=summary
        )
        self.session.add(partition)
        book = await self.get_by_id(book_id)
        book.current_partition = number
        await self.session.commit()
        await self.session.refresh(partition)
        return partition

    async def get_partition(self, book_id: str, number: int) -> Optional[Partition]:
        result = await self.session.execute(
            sm_select(Partition).where(
                Partition.book_id == book_id,
                Partition.partition_number == number
            )
        )
        return result.scalar_one_or_none()

    async def get_partitions(self, book_id: str, limit: int, offset: int) -> list[Partition]:
        result = await self.session.execute(
            sm_select(Partition)
            .where(Partition.book_id == book_id)
            .order_by(Partition.partition_number)
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def update_reading_partition(self, book_id: str, number: int) -> None:
        book = await self.get_by_id(book_id)
        book.reading_partition = number
        await self.session.commit()

    async def mark_error(self, book_id: str) -> None:
        await self.update_status(book_id, "error")
