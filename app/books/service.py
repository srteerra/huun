import asyncio

from app.ai.service import generate_chapter, validate_chapter
from app.books.models import Book, BookStatus, Chapter
from app.books.repository import BookRepository
from app.books.schemas import StorySettings, TokenUsage

_locks: dict[str, asyncio.Lock] = {}


def _get_lock(book_id: str) -> asyncio.Lock:
    if book_id not in _locks:
        _locks[book_id] = asyncio.Lock()
    return _locks[book_id]


class BookService:
    def __init__(self, repo: BookRepository):
        self.repo = repo

    async def create_book(
            self,
            genre: str,
            user_prompt: str | None,
            total_chapters: int,
            settings: StorySettings,
            title: str | None = None,
    ) -> Book:
        return await self.repo.create(genre, user_prompt, total_chapters, settings.model_dump(), title)

    async def build_blueprint(self, book_id: str, genre: str, user_prompt: str | None) -> None:
        from app.ai.service import generate_blueprint

        try:
            book = await self.repo.get_by_id(book_id)
            blueprint, usage = await generate_blueprint(
                genre, user_prompt, book.total_chapters, book.settings
            )
            await self.repo.save_blueprint(book_id, blueprint.model_dump())
            await self.repo.save_state(
                book_id,
                {
                    "plotFacts": [],
                    "characterStates": {},
                    "runningContext": [],
                    "currentChapter": 0,
                },
            )
            print(
                f"[blueprint] book={book_id} "
                f"in={usage.input_tokens} out={usage.output_tokens} "
                f"cache_read={usage.cache_read_input_tokens} cache_write={usage.cache_creation_input_tokens}"
            )
        except Exception as e:
            print(f"[ERROR] Blueprint generation failed for book {book_id}: {e}")
            await self.repo.mark_error(book_id)

    async def generate_next_chapter(self, book_id: str) -> tuple[Chapter, TokenUsage]:
        async with _get_lock(book_id):
            return await self._generate_next_chapter_locked(book_id)

    async def _generate_next_chapter_locked(self, book_id: str) -> tuple[Chapter, TokenUsage]:
        book = await self.repo.get_by_id(book_id)

        if book.status not in (BookStatus.ready, BookStatus.generating, BookStatus.completed):
            raise ValueError(f"El libro no está listo (status: {book.status})")

        next_num = book.current_chapter + 1
        if next_num > book.total_chapters:
            raise ValueError("El libro ya está completo")

        existing = await self.repo.get_chapter(book_id, next_num)
        if existing:
            return existing, TokenUsage()

        await self.repo.update_status(book_id, BookStatus.generating)

        result, usage = await generate_chapter(next_num, book.blueprint, book.state, book.settings)

        validation, val_usage = await validate_chapter(result.chapterText, book.state)
        usage = usage + val_usage

        if validation.hasContradiction:
            result, retry_usage = await generate_chapter(
                next_num,
                book.blueprint,
                book.state,
                book.settings,
                contradictions=validation.contradictions,
            )
            usage = usage + retry_usage

        title = result.chapterTitle
        text = result.chapterText
        summary = result.chapterSummary
        char_updates = result.characterStateUpdates

        chapter = await self.repo.save_chapter(book_id, next_num, title, text, summary)

        new_state = dict(book.state)
        new_state["plotFacts"] = book.state.get("plotFacts", []) + [{"chapter": next_num, "fact": summary}]
        new_state["runningContext"] = book.state.get("runningContext", []) + [
            {"chapter": next_num, "summary": summary}
        ]
        new_state["characterStates"] = {
            **book.state.get("characterStates", {}),
            **char_updates,
        }
        new_state["currentChapter"] = next_num
        new_state["lastClosingText"] = text[-200:]
        await self.repo.save_state(book_id, new_state)

        final_status = BookStatus.completed if next_num >= book.total_chapters else BookStatus.generating
        await self.repo.update_status(book_id, final_status)

        return chapter, usage

    async def get_chapter(self, book_id: str, number: int) -> Chapter | None:
        return await self.repo.get_chapter(book_id, number)

    async def get_chapters(self, book_id: str, limit: int, offset: int) -> list[Chapter]:
        return await self.repo.get_chapters(book_id, limit, offset)

    async def update_reading_chapter(self, book_id: str, number: int) -> None:
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise ValueError("Libro no encontrado")
        if number < 1 or number > book.current_chapter:
            raise ValueError(f"Capítulo {number} no existe aún")
        await self.repo.update_reading_chapter(book_id, number)
