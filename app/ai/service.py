import json
from typing import Optional

from app.ai.client import get_client

MODEL = "claude-sonnet-4-6"


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
        total_partitions: int,
) -> dict:
    client = get_client()

    system = (
        "You are a creative fiction writer. Generate detailed story blueprints as valid JSON "
        "with no additional commentary."
    )

    prompt = f"""Create a complete story blueprint for a {genre} novel with exactly {total_partitions} partitions (chapters).
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
    {{"partition": 1, "title": "string", "summary": "string", "keyEvents": ["string"]}},
    ...one entry per partition up to {total_partitions}
  ]
}}"""

    response = await client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.content[0].text)


async def generate_partition(
        partition_number: int,
        blueprint: dict,
        state: dict,
) -> dict:
    client = get_client()

    system = (
        "You are a skilled fiction writer. Write engaging story chapters consistent with the "
        "provided blueprint and current story state. Return only valid JSON, no commentary."
    )

    blueprint_block = {
        "type": "text",
        "text": f"STORY BLUEPRINT:\n{json.dumps(blueprint, ensure_ascii=False)}",
        "cache_control": {"type": "ephemeral"},
    }

    instruction_block = {
        "type": "text",
        "text": f"""CURRENT STATE:
{json.dumps(state, ensure_ascii=False)}

Write partition {partition_number}. Return only this JSON:
{{
  "partitionText": "full chapter prose (minimum 800 words)",
  "partitionSummary": "2-3 sentence summary of key events",
  "characterStateUpdates": {{"characterName": "updated state description"}}
}}""",
    }

    response = await client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": [blueprint_block, instruction_block]}],
    )
    return _extract_json(response.content[0].text)


async def validate_partition(text: str, state: dict) -> dict:
    client = get_client()

    prompt = f"""Check the following story partition for contradictions with the current story state.

CURRENT STATE:
{json.dumps(state, ensure_ascii=False)}

PARTITION TEXT:
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
