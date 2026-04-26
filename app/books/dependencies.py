from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.repository import BookRepository
from app.books.service import BookService
from app.database import get_session


def get_book_service(session: AsyncSession = Depends(get_session)) -> BookService:
    return BookService(BookRepository(session))


async def get_book_or_404(
        book_id: str,
        service: BookService = Depends(get_book_service),
):
    book = await service.repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
