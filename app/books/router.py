from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.books.dependencies import get_book_service
from app.books.repository import BookRepository
from app.books.schemas import (
    InitBookRequest, BookResponse, PartitionResponse,
    PartitionListResponse, UpdateReadingPartitionRequest,
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
    book = await service.create_book(body.genre, body.user_prompt, body.total_partitions)
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


@router.post("/{book_id}/partition", response_model=PartitionResponse)
async def generate_partition(
        book_id: str,
        service: BookService = Depends(get_book_service),
):
    try:
        partition = await service.generate_next_partition(book_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PartitionResponse(**partition.model_dump())


@router.get("/{book_id}/partitions", response_model=PartitionListResponse)
async def get_partitions(
        book_id: str,
        limit: int = Query(default=20, ge=1, le=50),
        offset: int = Query(default=0, ge=0),
        service: BookService = Depends(get_book_service),
):
    book = await service.repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    partitions = await service.get_partitions(book_id, limit, offset)
    return PartitionListResponse(
        partitions=[PartitionResponse(**p.model_dump()) for p in partitions],
        total_generated=book.current_partition,
        limit=limit,
        offset=offset,
    )


@router.get("/{book_id}/partitions/{partition_number}", response_model=PartitionResponse)
async def get_partition(
        book_id: str,
        partition_number: int,
        service: BookService = Depends(get_book_service),
):
    partition = await service.get_partition(book_id, partition_number)
    if not partition:
        raise HTTPException(status_code=404, detail=f"Partición {partition_number} no existe aún")
    return PartitionResponse(**partition.model_dump())


@router.patch("/{book_id}/reading-position", status_code=204)
async def update_reading_position(
        book_id: str,
        body: UpdateReadingPartitionRequest,
        service: BookService = Depends(get_book_service),
):
    try:
        await service.update_reading_partition(book_id, body.partition_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
