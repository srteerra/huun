import json
from typing import Optional

from app.ai.client import get_client

MODEL = "claude-sonnet-4-6"

_OPENING_STYLE = {
    "hook": "Start in medias res — drop the reader into action or high tension immediately",
    "gradual": "Open with a slow build — establish world and characters before introducing conflict",
    "prologue": "Begin with a prologue that provides backstory or future foreshadowing",
    "mystery": "Open with an unresolved question or unexplained event that creates intrigue",
}
_PACING = {
    "fast": "fast-paced with short scenes, snappy dialogue, and rapid plot progression",
    "moderate": "balanced pacing with room for both action and character moments",
    "slow": "leisurely paced with rich description and extended character reflection",
}
_CHARACTER_DEPTH = {
    "shallow": "characters are archetypal and functional — focus on plot over psychology",
    "moderate": "characters have clear motivations and some backstory but stay plot-focused",
    "deep": "characters have rich inner lives, contradictions, trauma, and psychological complexity",
}
_PERSPECTIVE = {
    "first_person": "first person (I/me)",
    "third_limited": "third person limited (single POV character per scene)",
    "third_omniscient": "third person omniscient (multiple POVs, narrator can access any mind)",
}
_TONE = {
    "dark": "dark and gritty — don't shy away from moral ambiguity or suffering",
    "hopeful": "hopeful and uplifting — even hardship leads toward growth",
    "neutral": "tonally balanced — neither romanticized nor gratuitously dark",
    "humorous": "light with humor — find levity even in tense moments",
    "suspenseful": "tense and suspenseful — maintain a constant undercurrent of dread or urgency",
}
_WORLD_BUILDING = {
    "minimal": "minimal world-building — only what's strictly needed for the plot",
    "standard": "standard world-building — enough detail to ground the story",
    "rich": "rich world-building — immersive detail about culture, history, geography, and environment",
}
_PROSE_STYLE = {
    "literary": "literary prose — lyrical, metaphor-rich, and introspective",
    "commercial": "commercial prose — clean, direct, and dialogue-driven",
    "minimalist": "minimalist prose — sparse and precise, let subtext do the work",
}
_CONTENT_RATING = {
    "family": "family-friendly — no violence, sexual content, or heavy themes",
    "teen": "teen-appropriate — mild violence and mature themes permitted, no explicit content",
    "adult": "adult content permitted — mature themes, violence, and sexuality as the story demands",
}
_WORDS_PER_CHAPTER = {
    "short": 800,
    "medium": 2000,
    "long": 4000,
}
_MAX_TOKENS_PER_CHAPTER = {
    "short": 4000,
    "medium": 8000,
    "long": 16000,
}


def _format_settings(settings: dict) -> str:
    from app.books.schemas import StorySettings
    s = StorySettings(**settings)
    min_words = _WORDS_PER_CHAPTER[s.words_per_chapter]
    return f"""WRITING SETTINGS (follow these strictly):
- Language: Write the entire story in {s.language}
- Opening style: {_OPENING_STYLE[s.opening_style]}
- Pacing: {_PACING[s.pacing]}
- Characters: {_CHARACTER_DEPTH[s.character_depth]}
- Narrative perspective: {_PERSPECTIVE[s.perspective]}
- Tone: {_TONE[s.tone]}
- World-building: {_WORLD_BUILDING[s.world_building]}
- Prose style: {_PROSE_STYLE[s.prose_style]}
- Content rating: {_CONTENT_RATING[s.content_rating]}
- Chapter length: minimum {min_words} words per chapter"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = inner.strip()
    return json.loads(text)


async def generate_blueprint(
        genre: str,
        user_prompt: Optional[str],
        total_chapters: int,
        settings: dict,
) -> dict:
    client = get_client()

    system = (
        "You are a creative fiction writer. Generate detailed story blueprints as valid JSON "
        "with no additional commentary."
    )

    prompt = f"""{_format_settings(settings)}

Create a complete story blueprint for a {genre} novel with exactly {total_chapters} chapters.
{f"Additional requirements: {user_prompt}" if user_prompt else ""}

Return only this JSON structure:
{{
  "title": "string",
  "synopsis": "string",
  "themes": ["string"],
  "characters": [
    {{"name": "string", "role": "string", "description": "string", "initialState": "string"}}
  ],
  "worldBuilding": "string",
  "plotOutline": [
    {{"chapter": 1, "title": "string", "summary": "string", "keyEvents": ["string"]}},
    ...one entry per chapter up to {total_chapters}
  ]
}}"""

    response = await client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.content[0].text)


async def generate_chapter(
        chapter_number: int,
        blueprint: dict,
        state: dict,
        settings: dict,
) -> dict:
    client = get_client()

    from app.books.schemas import StorySettings
    wpc = StorySettings(**settings).words_per_chapter
    min_words = _WORDS_PER_CHAPTER[wpc]
    max_tokens = _MAX_TOKENS_PER_CHAPTER[wpc]

    system = (
        "You are a skilled fiction writer. Write engaging story chapters consistent with the "
        "provided blueprint and current story state. Return only valid JSON, no commentary."
    )

    blueprint_block = {
        "type": "text",
        "text": (
            f"STORY BLUEPRINT:\n{json.dumps(blueprint, ensure_ascii=False)}\n\n"
            f"{_format_settings(settings)}"
        ),
        "cache_control": {"type": "ephemeral"},
    }

    instruction_block = {
        "type": "text",
        "text": f"""CURRENT STATE:
{json.dumps(state, ensure_ascii=False)}

Write chapter {chapter_number}. Return only this JSON:
{{
  "chapterTitle": "chapter title (no number, just the title)",
  "chapterText": "full chapter prose (minimum {min_words} words)",
  "chapterSummary": "2-3 sentence summary of key events",
  "characterStateUpdates": {{"characterName": "updated state description"}}
}}""",
    }

    response = await client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": [blueprint_block, instruction_block]}],
    )
    return _extract_json(response.content[0].text)


async def validate_chapter(text: str, state: dict) -> dict:
    client = get_client()

    prompt = f"""Check the following story chapter for contradictions with the current story state.

CURRENT STATE:
{json.dumps(state, ensure_ascii=False)}

CHAPTER TEXT:
{text}

Return only this JSON:
{{
  "hasContradiction": false,
  "contradictions": []
}}"""

    response = await client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.content[0].text)
