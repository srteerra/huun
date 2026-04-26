from typing import Optional

from app.ai.service import generate_blueprint, generate_partition, validate_partition
from app.books.models import Book, Partition
from app.books.repository import BookRepository

BUFFER_SIZE = 2
_generating: set[str] = set()


class BookService:
    def __init__(self, repo: BookRepository):
        self.repo = repo

    async def create_book(
            self, genre: str, user_prompt: Optional[str], total_partitions: int
    ) -> Book:
        return await self.repo.create(genre, user_prompt, total_partitions)

    async def build_blueprint(self, book_id: str, genre: str, user_prompt: Optional[str]) -> None:
        try:
            book = await self.repo.get_by_id(book_id)
            blueprint = await generate_blueprint(genre, user_prompt, book.total_partitions)
            await self.repo.save_blueprint(book_id, blueprint)
            await self.repo.save_state(book_id, {
                "plotFacts": [],
                "characterStates": {},
                "runningContext": [],
                "currentPartition": 0,
            })
        except Exception as e:
            print(f"[ERROR] Blueprint generation failed for book {book_id}: {e}")
            await self.repo.mark_error(book_id)

    async def generate_next_partition(self, book_id: str) -> Partition:
        book = await self.repo.get_by_id(book_id)

        if book.status not in ("ready", "generating", "completed"):
            raise ValueError(f"El libro no está listo (status: {book.status})")

        next_num = book.current_partition + 1
        if next_num > book.total_partitions:
            raise ValueError("El libro ya está completo")

        existing = await self.repo.get_partition(book_id, next_num)
        if existing:
            return existing

        await self.repo.update_status(book_id, "generating")

        result = await generate_partition(next_num, book.blueprint, book.state)
        text = result["partitionText"]
        summary = result["partitionSummary"]
        char_updates = result.get("characterStateUpdates", {})

        validation = await validate_partition(text, book.state)
        if validation.get("hasContradiction"):
            result = await generate_partition(next_num, book.blueprint, book.state)
            text = result["partitionText"]
            summary = result["partitionSummary"]
            char_updates = result.get("characterStateUpdates", {})

        partition = await self.repo.save_partition(book_id, next_num, text, summary)

        new_state = dict(book.state)
        new_state["plotFacts"] = book.state.get("plotFacts", []) + [
            {"partition": next_num, "fact": summary}
        ]
        new_state["runningContext"] = book.state.get("runningContext", []) + [
            {"partition": next_num, "summary": summary}
        ]
        new_state["characterStates"] = {**book.state.get("characterStates", {}), **char_updates}
        new_state["currentPartition"] = next_num
        new_state["lastClosingText"] = text[-200:]
        await self.repo.save_state(book_id, new_state)

        final_status = "completed" if next_num >= book.total_partitions else "generating"
        await self.repo.update_status(book_id, final_status)

        return partition

    async def get_partition(self, book_id: str, number: int) -> Optional[Partition]:
        return await self.repo.get_partition(book_id, number)

    async def get_partitions(self, book_id: str, limit: int, offset: int) -> list[Partition]:
        return await self.repo.get_partitions(book_id, limit, offset)

    async def update_reading_partition(self, book_id: str, number: int) -> None:
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise ValueError("Libro no encontrado")
        if number < 1 or number > book.current_partition:
            raise ValueError(f"Partición {number} no existe aún")
        await self.repo.update_reading_partition(book_id, number)
