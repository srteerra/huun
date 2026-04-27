# Huun

AI-powered story generation API. Give it a genre and a prompt — it builds a complete novel blueprint and writes every
chapter, keeping characters and plot consistent from start to finish.

## How it works

```
Your prompt ──► Blueprint ──► Chapter 1 ──► Chapter 2 ──► ... ──► Chapter N
                  (AI)          (AI)          (AI)
                   │              │
                   └── story state kept in sync (characters, plot, closing lines)
```

1. **Blueprint** — Huun plans the full story before writing a word: title, synopsis, themes, characters, world-building,
   and a chapter-by-chapter plot outline.
2. **Generation** — chapters are written one at a time against that blueprint. Each call receives the current story
   state so continuity is preserved.
3. **Validation** — after each chapter is written, a second AI pass checks for contradictions. If one is found, the
   chapter is regenerated.
4. **State tracking** — after every accepted chapter the state is updated: new plot facts recorded, character states
   patched, and the closing text saved as context for the next chapter.

---

## Requirements

- Docker & Docker Compose
- Python **3.13+** (only needed for local/non-Docker development)
- An [Anthropic API key](https://console.anthropic.com/)

## Installation

```bash
# 1. Fork & clone
git clone https://github.com/<your-username>/huun.git
cd huun

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY and ENVIRONMENT

# 3. Start services
docker compose up --build -d

# 4. Run migrations
docker compose exec api alembic upgrade head
```

API → `http://localhost:8000`  
Interactive docs → `http://localhost:8000/docs`

### Local development (without Docker)

```bash
pip install poetry
poetry install
poetry run uvicorn app.main:app --reload
```

> Make sure `DATABASE_URL` in `.env` points to a running PostgreSQL 16 instance.

---

## API at a glance

| Method  | Endpoint                                | What it does                               |
|---------|-----------------------------------------|--------------------------------------------|
| `POST`  | `/api/books/init`                       | Create a book & start blueprint generation |
| `GET`   | `/api/books/{book_id}`                  | Check book status & metadata               |
| `POST`  | `/api/books/{book_id}/chapter`          | Generate the next chapter                  |
| `GET`   | `/api/books/{book_id}/chapters`         | List all chapters (paginated)              |
| `GET`   | `/api/books/{book_id}/chapters/{n}`     | Get a specific chapter                     |
| `PATCH` | `/api/books/{book_id}/reading-position` | Update reading progress                    |

### Typical flow

```
1. POST /api/books/init          → get back book_id (202, async)
2. GET  /api/books/{book_id}     → poll until status = "ready"
3. POST /api/books/{book_id}/chapter   ─┐
4. POST /api/books/{book_id}/chapter   ─┤  repeat until all chapters done
   ...                                  ─┘
5. GET  /api/books/{book_id}/chapters  → read them all
```

---

## Endpoints

### `POST /api/books/init` — Create a book

```json
{
  "genre": "fantasy",
  "user_prompt": "A blind cartographer who can map places she has never visited",
  "title": "The Uncharted Dark",
  "total_chapters": 20,
  "settings": {
    "language": "en",
    "opening_style": "hook",
    "pacing": "moderate",
    "character_depth": "deep",
    "perspective": "third_limited",
    "tone": "dark",
    "world_building": "rich",
    "prose_style": "literary",
    "content_rating": "teen",
    "words_per_chapter": "long"
  }
}
```

- `title` is optional — generated from the blueprint if omitted.
- `settings` is optional — all fields have defaults (see table below).
- Returns `202` immediately; blueprint generation runs in the background.

---

### `GET /api/books/{book_id}` — Poll book status

Status lifecycle:

```
initializing ──► ready ──► generating ──► completed
                                 └──────────► error
```

Wait for `ready` before calling the chapter endpoint.

---

### `POST /api/books/{book_id}/chapter` — Generate next chapter

Call once per chapter, in order. Returns:

```json
{
  "chapter_number": 1,
  "title": "The Shape of Darkness",
  "text": "...",
  "summary": "..."
}
```

---

### `GET /api/books/{book_id}/chapters` — List chapters

```
GET /api/books/{book_id}/chapters?limit=20&offset=0
```

---

### `GET /api/books/{book_id}/chapters/{n}` — Get a specific chapter

```
GET /api/books/{book_id}/chapters/3
```

---

### `PATCH /api/books/{book_id}/reading-position` — Update progress

```json
{ "chapter_number": 5 }
```

Returns `204 No Content`.

---

## Story settings

| Field               | Options                                             | Default         | Description                               |
|---------------------|-----------------------------------------------------|-----------------|-------------------------------------------|
| `language`          | any BCP-47 tag                                      | `es`            | Language the story is written in          |
| `opening_style`     | `hook` `gradual` `prologue` `mystery`               | `hook`          | How the first chapter opens               |
| `pacing`            | `fast` `moderate` `slow`                            | `moderate`      | Scene and plot pacing                     |
| `character_depth`   | `shallow` `moderate` `deep`                         | `moderate`      | Psychological complexity                  |
| `perspective`       | `first_person` `third_limited` `third_omniscient`   | `third_limited` | Narrative POV                             |
| `tone`              | `dark` `hopeful` `neutral` `humorous` `suspenseful` | `neutral`       | Emotional register                        |
| `world_building`    | `minimal` `standard` `rich`                         | `standard`      | Amount of world detail                    |
| `prose_style`       | `literary` `commercial` `minimalist`                | `commercial`    | Writing style                             |
| `content_rating`    | `family` `teen` `adult`                             | `teen`          | Content restrictions                      |
| `words_per_chapter` | `short` `medium` `long`                             | `medium`        | Target length (800 / 2,000 / 4,000 words) |

---

## Environment variables

| Variable            | Required | Default                 | Description                                                                       |
|---------------------|----------|-------------------------|-----------------------------------------------------------------------------------|
| `ANTHROPIC_API_KEY` | yes      | —                       | Anthropic API key                                                                 |
| `DATABASE_URL`      | yes      | —                       | PostgreSQL async URL — e.g. `postgresql+asyncpg://postgres:password@db:5432/huun` |
| `ENVIRONMENT`       | no       | `development`           | Runtime environment (`development` \| `production`)                               |
| `CORS_ORIGINS`      | no       | `http://localhost:5173` | Comma-separated list of allowed origins                                           |

---

## Tech stack

|                        | Version       |
|------------------------|---------------|
| **Python**             | 3.13+         |
| **FastAPI**            | 0.136         |
| **SQLModel + asyncpg** | 0.0.38 / 0.31 |
| **Alembic**            | 1.18          |
| **Anthropic SDK**      | 0.97          |
| **PostgreSQL**         | 16            |

---

## License

AGPL-3.0 — see [LICENSE](LICENSE).
