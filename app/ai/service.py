import json

from app.ai import prompts
from app.ai.client import get_client
from app.ai.prompts import BlueprintResult, ChapterResult, ValidationResult
from app.books.schemas import TokenUsage

MODEL = "claude-sonnet-4-6"
MODEL_HAIKU = "claude-haiku-4-5-20251001"


def _tool(name: str, model: type) -> dict:
    return {"name": name, "input_schema": model.model_json_schema()}


def _extract_usage(response) -> TokenUsage:
    u = response.usage
    return TokenUsage(
        input_tokens=u.input_tokens,
        output_tokens=u.output_tokens,
        cache_creation_input_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        cache_read_input_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
    )


async def generate_blueprint(
        genre: str,
        user_prompt: str | None,
        total_chapters: int,
        settings: dict,
) -> tuple[BlueprintResult, TokenUsage]:
    from app.books.schemas import StorySettings

    client = get_client()
    s = StorySettings(**settings)

    response = await client.messages.create(
        model=MODEL,
        max_tokens=16000,
        tools=[_tool("generate_blueprint", BlueprintResult)],
        tool_choice={"type": "tool", "name": "generate_blueprint"},
        system=[{"type": "text", "text": prompts.BLUEPRINT_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": prompts.blueprint_user(
                    settings=prompts.settings_block(s),
                    genre=genre,
                    total_chapters=total_chapters,
                    user_prompt=user_prompt,
                ),
            }
        ],
    )
    return BlueprintResult(**response.content[0].input), _extract_usage(response)


async def generate_chapter(
        chapter_number: int,
        blueprint: dict,
        state: dict,
        settings: dict,
        contradictions: list[str] | None = None,
) -> tuple[ChapterResult, TokenUsage]:
    from app.books.schemas import StorySettings

    client = get_client()
    s = StorySettings(**settings)
    min_words = prompts.WORDS_PER_CHAPTER[s.words_per_chapter]
    max_tokens = prompts.MAX_TOKENS_PER_CHAPTER[s.words_per_chapter]

    blueprint_block = {
        "type": "text",
        "text": prompts.chapter_blueprint(
            blueprint_json=json.dumps(blueprint, ensure_ascii=False),
            settings=prompts.settings_block(s),
        ),
        "cache_control": {"type": "ephemeral"},
    }

    instruction_block = {
        "type": "text",
        "text": prompts.chapter_instruction(
            state_json=json.dumps(state, ensure_ascii=False),
            chapter_number=chapter_number,
            min_words=min_words,
            contradictions=contradictions,
        ),
    }

    response = await client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        tools=[_tool("write_chapter", prompts.ChapterResult)],
        tool_choice={"type": "tool", "name": "write_chapter"},
        system=[{"type": "text", "text": prompts.CHAPTER_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": [blueprint_block, instruction_block]}],
    )
    return ChapterResult(**response.content[0].input), _extract_usage(response)


async def validate_chapter(text: str, state: dict) -> tuple[ValidationResult, TokenUsage]:
    client = get_client()

    response = await client.messages.create(
        model=MODEL_HAIKU,
        max_tokens=512,
        tools=[_tool("validate_chapter", ValidationResult)],
        tool_choice={"type": "tool", "name": "validate_chapter"},
        messages=[
            {
                "role": "user",
                "content": prompts.validate(
                    state_json=json.dumps(state, ensure_ascii=False),
                    chapter_text=text,
                ),
            }
        ],
    )
    return ValidationResult(**response.content[0].input), _extract_usage(response)
