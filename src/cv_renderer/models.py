from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator, model_validator


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


class Project(BaseModel):
    name: str
    subtitle: str = ""
    year: int | None = None
    start: int | str | None = None
    end: int | str | None = None
    tags: list[str]
    bullets: list[Bullet]


class ExperienceEntry(BaseModel):
    company: str
    title: dict[str, str]
    location: str
    start: str
    end: str
    tags: list[str]
    description: str = ""
    # A job carries either loose bullets or named sub-projects, not both: use
    # `projects` only when one employer hosted distinct workstreams worth naming
    # (rendered as sub-headings), otherwise keep the entry flat with `bullets`.
    bullets: list[Bullet] = []
    projects: list[Project] = []

    @model_validator(mode="after")
    def require_content(self) -> "ExperienceEntry":
        if not self.bullets and not self.projects:
            raise ValueError(f"experience[{self.company}] has neither bullets nor projects")
        if self.bullets and self.projects:
            raise ValueError(
                f"experience[{self.company}] mixes loose bullets with sub-projects — "
                "move the loose bullets into a named project"
            )
        return self


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
    def normalize_items(cls, v: str | list[dict[str, Any] | str]) -> list[dict[str, Any] | str]:
        # Legacy shorthand: a comma-separated string, all items untagged (always shown).
        if isinstance(v, str):
            return [{"text": item.strip(), "tags": []} for item in v.split(",")]
        # Mixed list: plain strings (untagged) alongside {text, tags} dicts.
        normalized: list[dict[str, Any] | str] = []
        for item in v:
            normalized.append({"text": item, "tags": []} if isinstance(item, str) else item)
        return normalized


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
    headline: int | None = None  # the role line under the name; None = same as body
    entry: int | None = None  # job/project/education headings; None = same as body


class Theme(BaseModel):
    """Colour and weight of the CV's furniture — headings, the role line, the
    contact line. Every field defaults to the plain black-on-white look, so a
    profile that sets none of them renders exactly as it did before a theme
    existed.
    """

    heading_color: str = ""  # section headings and the rule under them
    heading_bold: bool = False
    title_color: str = ""  # the role line under the name, and skill category labels
    title_bold: bool = False
    title_italic: bool = False
    muted_color: str = ""  # the contact line


class Profile(BaseModel):
    name: str
    description: str = ""
    variant: str = "default"
    lang: str = "en"

    # Per-application content overrides — take priority over base-data content and
    # tag-based selection. See filter.py::apply_profile for how each is applied.
    title_override: str | None = None
    about_override: str | None = None
    location_override: str | None = None  # header location line, e.g. remote availability
    name_override: str | None = None  # header name, e.g. a transliterated spelling
    # Keyed by ExperienceEntry.company. On a job with sub-projects this flattens the
    # entry: the hand-written bullets replace the sub-project headings entirely.
    experience_overrides: dict[str, list[str]] = {}
    # keyed by ExperienceEntry.company; replaces that entry's location line only
    experience_location_overrides: dict[str, str] = {}
    # Keyed by Project.name, covering both the standalone Projects section and
    # sub-projects nested under a job — one namespace, since names are unique.
    project_overrides: dict[str, list[str]] = {}
    # Reorders the Projects section only; sub-projects follow base-data order.
    project_order: list[str] | None = None
    # Regroups skill items into custom, per-application category labels — keyed by the
    # new category name, valued by a list of item texts pulled from anywhere in the base
    # data's skills (regardless of their original category). Replaces skill_categories
    # entirely when set: this is for reshaping the grouping itself (e.g. splitting one
    # base category into two for this application), which tag-based selection can't do
    # without changing the base data for every profile.
    skill_overrides: dict[str, list[str]] | None = None

    # Tag-based selection, used wherever the above overrides don't apply.
    focus_tags: list[str] = []
    deprioritize_tags: list[str] = []
    max_bullets_per_job: int = 10
    sections: list[str] = ["experience", "projects", "skills", "education", "additional"]
    skill_categories: list[str] | None = None  # None = include all

    # Presentation.
    # Links and section rules. Defaults to the long-standing link blue, so an
    # existing profile renders unchanged; a themed CV sets its own colour here.
    accent_color: str = "#1154CC"
    theme: Theme = Theme()
    # False prints each link's address instead of its label — the form an ATS
    # reading the PDF's text layer can actually use — and drops the link colour
    # and underline. The anchor itself stays either way, carrying the https://
    # the printed address omits.
    contact_links: bool = True
    font_family: str = "Arial, Helvetica, sans-serif"
    font_sizes: FontSizes = FontSizes()
    template: str = "main"


class CoverLetterContent(BaseModel):
    """A cover letter's body — paired with a `Profile` (via `--profile`) for the
    header. Its own small file, versioned the same way a `Profile` is, rather
    than an untracked scratch text file: `paragraphs` is the single source of
    truth `render_cover_letter` reads.
    """

    paragraphs: list[str]
