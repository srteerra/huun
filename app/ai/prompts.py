from pydantic import BaseModel, Field

from app.books.schemas import StorySettings

WORDS_PER_CHAPTER = {"short": 800, "medium": 2000, "long": 4000}
MAX_TOKENS_PER_CHAPTER = {"short": 4000, "medium": 8000, "long": 16000}

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
_CHARACTER_INTRO_PACE = {
    "immediate": "other characters appear or are mentioned from the very first scene of chapter one — the protagonist is never truly alone even at the opening",
    "gradual": "introduce secondary characters progressively across the whole story — a few are mentioned early, more appear as chapters advance",
    "after_first": "chapter one belongs entirely to the protagonist with no other characters present or mentioned; from chapter two onward, one or two characters begin to appear as the plot requires",
    "late": "keep the protagonist isolated throughout most of the story — secondary characters only begin to appear or are referenced in the final quarter of the book",
    "solo": "the protagonist is completely alone for the entire story — no other characters appear or are mentioned at any point; a true solitary narrative",
}


class CharacterBlueprint(BaseModel):
    name: str
    role: str = Field(description="protagonist, antagonist, supporting, etc.")
    description: str
    initialState: str = Field(description="character's mental/emotional state at story start")


class PlotPoint(BaseModel):
    chapter: int
    title: str
    summary: str
    keyEvents: list[str]


class BlueprintResult(BaseModel):
    title: str
    synopsis: str = Field(description="2-3 sentence story overview")
    themes: list[str]
    characters: list[CharacterBlueprint]
    worldBuilding: str = Field(description="setting, geography, rules of the world")
    plotOutline: list[PlotPoint] = Field(description="one entry per chapter, in order")


class ChapterResult(BaseModel):
    chapterTitle: str = Field(description="chapter title without the chapter number")
    chapterText: str = Field(description="full chapter prose")
    chapterSummary: str = Field(description="2-3 sentence summary of key events")
    characterStateUpdates: dict[str, str] = Field(
        description="map of character name to updated state description"
    )


class ValidationResult(BaseModel):
    hasContradiction: bool
    contradictions: list[str] = Field(description="list of specific contradictions found, if any")


BLUEPRINT_SYSTEM = "You are a creative fiction writer. Generate detailed and compelling story blueprints."

CHAPTER_SYSTEM = (
    "You are a skilled fiction writer. Write engaging story chapters consistent with the "
    "provided blueprint and current story state."
)


def settings_block(s: StorySettings) -> str:
    min_words = WORDS_PER_CHAPTER[s.words_per_chapter]
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
- Chapter length: minimum {min_words} words per chapter
- Character introduction pace: {_CHARACTER_INTRO_PACE[s.character_intro_pace]}"""


def blueprint_user(settings: str, genre: str, total_chapters: int, user_prompt: str | None) -> str:
    extra = f"Additional requirements: {user_prompt}" if user_prompt else ""
    return f"""{settings}

Create a complete story blueprint for a {genre} novel with exactly {total_chapters} chapters.
The plotOutline must contain exactly {total_chapters} entries, one per chapter, in order.
{extra}"""


def chapter_blueprint(blueprint_json: str, settings: str) -> str:
    return f"""STORY BLUEPRINT: {blueprint_json} {settings}"""


def chapter_instruction(
        state_json: str,
        chapter_number: int,
        min_words: int,
        contradictions: list[str] | None = None,
) -> str:
    contradiction_block = ""
    if contradictions:
        items = "\n".join(f"- {c}" for c in contradictions)
        contradiction_block = f"\nThe previous attempt had these contradictions — fix all of them:\n{items}\n"
    return f"""CURRENT STATE:
{state_json}
{contradiction_block}
Write chapter {chapter_number}. The chapterText must be at least {min_words} words."""


def validate(state_json: str, chapter_text: str) -> str:
    return f"""Check the following story chapter for contradictions with the current story state.

CURRENT STATE:
{state_json}

CHAPTER TEXT:
{chapter_text}"""
