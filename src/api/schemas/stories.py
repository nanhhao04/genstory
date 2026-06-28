from pydantic import BaseModel, Field, field_validator

from src.core.guardrails import ALLOWED_ART_STYLES, ALLOWED_GENRES


class StoryStartRequest(BaseModel):
    description: str = Field(..., min_length=20, max_length=2500)
    genre: str = Field(default="dark_fantasy")
    art_style: str = Field(default="anime")
    protagonist_name: str = Field(default="Kael", max_length=60)
    protagonist_description: str = Field(default="", max_length=400)
    target_chapters: int = Field(default=8, ge=4, le=20)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 20:
            raise ValueError("Description must be at least 20 characters")
        return normalized

    @field_validator("protagonist_name", mode="before")
    @classmethod
    def normalize_protagonist_name(cls, value: str) -> str:
        normalized = (value or "").strip()
        return normalized or "Kael"

    @field_validator("protagonist_description", mode="before")
    @classmethod
    def normalize_protagonist_description(cls, value: str) -> str:
        return (value or "").strip()

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, value: str) -> str:
        if value not in ALLOWED_GENRES:
            raise ValueError("Unsupported genre")
        return value

    @field_validator("art_style")
    @classmethod
    def validate_art_style(cls, value: str) -> str:
        if value not in ALLOWED_ART_STYLES:
            raise ValueError("Unsupported art style")
        return value


class StoryNextRequest(BaseModel):
    story_id: str
    chosen_option_text: str = Field(..., min_length=2, max_length=120)
