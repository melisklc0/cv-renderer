from __future__ import annotations

from pydantic import BaseModel, field_validator


class Links(BaseModel):
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class Meta(BaseModel):
    name: str
    title: dict[str, str]
    location: str
    email: str
    phone: str
    links: Links


class Bullet(BaseModel):
    text: str
    tags: list[str]


class ExperienceEntry(BaseModel):
    company: str
    title: dict[str, str]
    location: str
    start: str
    end: str
    tags: list[str]
    description: str = ""
    bullets: list[Bullet]


class EducationEntry(BaseModel):
    institution: str
    degree: str
    location: str | None = None
    start: int | str
    end: int | str
    tags: list[str]


class SkillCategory(BaseModel):
    category: str
    tags: list[str]
    items: list[Bullet]

    @field_validator("items", mode="before")
    @classmethod
    def normalize_items(cls, v: str | list) -> list:
        # Legacy shorthand: a comma-separated string, all items untagged (always shown).
        if isinstance(v, str):
            return [{"text": item.strip(), "tags": []} for item in v.split(",")]
        # Mixed list: plain strings (untagged) alongside {text, tags} dicts.
        normalized = []
        for item in v:
            normalized.append({"text": item, "tags": []} if isinstance(item, str) else item)
        return normalized


class Project(BaseModel):
    name: str
    subtitle: str = ""
    year: int | None = None
    start: int | str | None = None
    end: int | str | None = None
    tags: list[str]
    bullets: list[Bullet]


class Additional(BaseModel):
    languages: list[str]
    certifications: list[str]


class CVData(BaseModel):
    meta: Meta
    about: dict[str, str]
    experience: list[ExperienceEntry]
    education: list[EducationEntry]
    skills: list[SkillCategory]
    projects: list[Project]
    additional: Additional


class FontSizes(BaseModel):
    name: int = 16
    section: int = 12
    body: int = 9


class Profile(BaseModel):
    name: str
    description: str = ""
    variant: str = "default"
    lang: str = "en"

    # Per-application content overrides — take priority over base-data content and
    # tag-based selection. See filter.py::apply_profile for how each is applied.
    title_override: str | None = None
    about_override: str | None = None
    experience_overrides: dict[str, list[str]] = {}  # keyed by ExperienceEntry.company
    project_overrides: dict[str, list[str]] = {}  # keyed by Project.name

    # Tag-based selection, used wherever the above overrides don't apply.
    focus_tags: list[str] = []
    deprioritize_tags: list[str] = []
    max_bullets_per_job: int = 10
    sections: list[str] = ["experience", "projects", "skills", "education", "additional"]
    skill_categories: list[str] | None = None  # None = include all

    # Presentation.
    font_family: str = "Arial, Helvetica, sans-serif"
    font_sizes: FontSizes = FontSizes()
    template: str = "main"
