from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select as sm_select

from app.books.models import Book, BookStatus, Chapter, utcnow


class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _touch(self, book: Book) -> None:
        book.updated_at = utcnow()

    async def create(
            self,
            genre: str,
            user_prompt: str | None,
            total_chapters: int,
            settings: dict,
            title: str | None = None,
    ) -> Book:
        book = Book(
            genre=genre,
            user_prompt=user_prompt,
            total_chapters=total_chapters,
            settings=settings,
            title=title,
        )
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def get_by_id(self, book_id: str) -> Book | None:
        result = await self.session.execute(sm_select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()

    async def save_blueprint(self, book_id: str, blueprint: dict) -> None:
        book = await self.get_by_id(book_id)
        book.blueprint = blueprint
        book.status = BookStatus.ready
        if not book.title:
            book.title = blueprint.get("title")
        self._touch(book)
        await self.session.commit()

    async def save_state(self, book_id: str, state: dict) -> None:
        book = await self.get_by_id(book_id)
        book.state = state
        self._touch(book)
        await self.session.commit()

    async def update_status(self, book_id: str, status: str) -> None:
        book = await self.get_by_id(book_id)
        book.status = status
        self._touch(book)
        await self.session.commit()

    async def save_chapter(
            self, book_id: str, number: int, title: str | None, text: str, summary: str
    ) -> Chapter:
        chapter = Chapter(
            book_id=book_id,
            chapter_number=number,
            title=title,
            text=text,
            summary=summary,
        )
        self.session.add(chapter)
        book = await self.get_by_id(book_id)
        book.current_chapter = number
        self._touch(book)
        await self.session.commit()
        await self.session.refresh(chapter)
        return chapter

    async def get_chapter(self, book_id: str, number: int) -> Chapter | None:
        result = await self.session.execute(
            sm_select(Chapter).where(
                Chapter.book_id == book_id,
                Chapter.chapter_number == number,
            )
        )
        return result.scalar_one_or_none()

    async def get_chapters(self, book_id: str, limit: int, offset: int) -> list[Chapter]:
        result = await self.session.execute(
            sm_select(Chapter)
            .where(Chapter.book_id == book_id)
            .order_by(Chapter.chapter_number)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def update_reading_chapter(self, book_id: str, number: int) -> None:
        book = await self.get_by_id(book_id)
        book.reading_chapter = number
        self._touch(book)
        await self.session.commit()

    async def mark_error(self, book_id: str) -> None:
        await self.update_status(book_id, BookStatus.error)
