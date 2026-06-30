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
    items: list[str]

    @field_validator("items", mode="before")
    @classmethod
    def split_items(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v


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
    focus_tags: list[str] = []
    deprioritize_tags: list[str] = []
    max_bullets_per_job: int = 10
    sections: list[str] = ["experience", "projects", "skills", "education", "additional"]
    skill_categories: list[str] | None = None  # None = include all
    font_family: str = "Arial, Helvetica, sans-serif"
    font_sizes: FontSizes = FontSizes()
    template: str = "main"
