from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.books.dependencies import get_book_service
from app.books.repository import BookRepository
from app.books.schemas import (
    InitBookRequest, BookResponse, ChapterResponse,
    ChapterListResponse, UpdateReadingChapterRequest,
)
from app.books.service import BookService
from app.database import AsyncSessionLocal

router = APIRouter(prefix="/api/books", tags=["books"])


async def _run_blueprint_in_background(book_id: str, genre: str, user_prompt):
    async with AsyncSessionLocal() as session:
        service = BookService(BookRepository(session))
        await service.build_blueprint(book_id, genre, user_prompt)


@router.post("/init", response_model=BookResponse, status_code=202)
async def init_book(
        body: InitBookRequest,
        background_tasks: BackgroundTasks,
        service: BookService = Depends(get_book_service),
):
    book = await service.create_book(body.genre, body.user_prompt, body.total_chapters, body.settings, body.title)
    background_tasks.add_task(
        _run_blueprint_in_background, book.id, body.genre, body.user_prompt
    )
    return BookResponse(**book.model_dump())


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
        book_id: str,
        service: BookService = Depends(get_book_service),
):
    book = await service.repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookResponse(**book.model_dump())


@router.post("/{book_id}/chapter", response_model=ChapterResponse)
async def generate_chapter(
        book_id: str,
        service: BookService = Depends(get_book_service),
):
    try:
        chapter = await service.generate_next_chapter(book_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ChapterResponse(**chapter.model_dump())


@router.get("/{book_id}/chapters", response_model=ChapterListResponse)
async def get_chapters(
        book_id: str,
        limit: int = Query(default=20, ge=1, le=50),
        offset: int = Query(default=0, ge=0),
        service: BookService = Depends(get_book_service),
):
    book = await service.repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    chapters = await service.get_chapters(book_id, limit, offset)
    return ChapterListResponse(
        chapters=[ChapterResponse(**c.model_dump()) for c in chapters],
        total_generated=book.current_chapter,
        limit=limit,
        offset=offset,
    )


@router.get("/{book_id}/chapters/{chapter_number}", response_model=ChapterResponse)
async def get_chapter(
        book_id: str,
        chapter_number: int,
        service: BookService = Depends(get_book_service),
):
    chapter = await service.get_chapter(book_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=404, detail=f"Capítulo {chapter_number} no existe aún")
    return ChapterResponse(**chapter.model_dump())


@router.patch("/{book_id}/reading-position", status_code=204)
async def update_reading_position(
        book_id: str,
        body: UpdateReadingChapterRequest,
        service: BookService = Depends(get_book_service),
):
    try:
        await service.update_reading_chapter(book_id, body.chapter_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
