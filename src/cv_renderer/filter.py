from typing import Any

from cv_renderer.models import Bullet, CVData, Profile, Project


def _resolve(variants: dict[str, str], variant: str) -> str:
    return variants.get(variant) or variants.get("default", "")


def _filter_bullets(
    bullets: list[Bullet],
    focus: set[str],
    deprio: set[str],
    max_n: int,
) -> list[str]:
    focused: list[str] = []
    neutral: list[str] = []
    for b in bullets:
        btags = set(b.tags)
        if btags & focus:
            focused.append(b.text)
        elif not btags.issubset(deprio):
            neutral.append(b.text)
    return (focused + neutral)[:max_n]


def _resolve_bullets(
    override: list[str] | None,
    bullets: list[Bullet],
    focus: set[str],
    deprio: set[str],
    max_n: int,
) -> list[str]:
    if override is not None:
        return override
    return _filter_bullets(bullets, focus, deprio, max_n)


def _select_projects(
    projects: list[Project],
    overrides: dict[str, list[str]],
    focus: set[str],
    deprio: set[str],
    max_n: int,
    include_all: bool,
) -> list[dict[str, Any]]:
    """Tag-select and render a list of projects. Shared by the standalone Projects
    section and by sub-projects nested under a job, so both are keyed by the same
    `project_overrides` namespace and obey the same per-project bullet cap."""
    selected: list[dict[str, Any]] = []
    for proj in projects:
        override = overrides.get(proj.name)
        if override is None and not include_all and not (set(proj.tags) & focus):
            continue
        bullets = _resolve_bullets(override, proj.bullets, focus, deprio, max_n)
        if not bullets:
            continue
        selected.append(
            {
                "name": proj.name,
                "subtitle": proj.subtitle,
                "year": proj.year,
                "start": proj.start,
                "end": proj.end,
                "bullets": bullets,
            }
        )
    return selected


def _filter_skill_items(items: list[Bullet], focus: set[str], deprio: set[str]) -> list[str]:
    # Unlike job/project bullets, skill items are short and untagged-by-default:
    # an item with no tags is generic and always kept, not dropped as "empty subset of deprio".
    focused: list[str] = []
    neutral: list[str] = []
    for item in items:
        tags = set(item.tags)
        if tags & focus:
            focused.append(item.text)
        elif tags and tags.issubset(deprio):
            continue
        else:
            neutral.append(item.text)
    return focused + neutral


def apply_profile(cv: CVData, profile: Profile, labels: dict[str, str]) -> dict[str, Any]:
    variant = profile.variant
    focus = set(profile.focus_tags)
    deprio = set(profile.deprioritize_tags)
    max_b = profile.max_bullets_per_job
    include_all = not focus

    meta: dict[str, Any] = {
        "name": profile.name_override or cv.meta.name,
        "title": profile.title_override or _resolve(cv.meta.title, variant),
        "location": profile.location_override or cv.meta.location,
        "email": cv.meta.email,
        "phone": cv.meta.phone,
        "links": cv.meta.links.model_dump(),
    }

    experience: list[dict[str, Any]] = []
    for job in cv.experience:
        override = profile.experience_overrides.get(job.company)
        # An experience_overrides entry flattens the job: it replaces sub-projects and
        # their bullets with one hand-written list, so a tight one-page profile can
        # collapse a multi-workstream employer without editing the base data.
        if override is not None:
            bullets, sub_projects = override, []
        elif job.projects:
            bullets = []
            sub_projects = _select_projects(
                job.projects, profile.project_overrides, focus, deprio, max_b, include_all
            )
        else:
            bullets = _resolve_bullets(None, job.bullets, focus, deprio, max_b)
            sub_projects = []
        if not bullets and not sub_projects:
            continue
        experience.append(
            {
                "company": job.company,
                "title": _resolve(job.title, variant),
                "location": profile.experience_location_overrides.get(job.company, job.location),
                "start": job.start,
                "end": job.end,
                "description": job.description,
                "bullets": bullets,
                "projects": sub_projects,
            }
        )

    skills: list[dict[str, Any]]
    if profile.skill_overrides is not None:
        skills = [
            {"category": category, "entries": entries}
            for category, entries in profile.skill_overrides.items()
        ]
    else:
        include_tags = focus | {"always"}
        skills = []
        for cat in cv.skills:
            if profile.skill_categories is not None:
                if cat.category not in profile.skill_categories:
                    continue
            elif not include_all and not (set(cat.tags) & include_tags):
                continue
            entries = _filter_skill_items(cat.items, focus, deprio)
            if not entries:
                continue
            skills.append({"category": cat.category, "entries": entries})

        if profile.skill_categories is not None:
            order = {name: i for i, name in enumerate(profile.skill_categories)}
            skills.sort(key=lambda s: order.get(s["category"], 999))

    projects = _select_projects(
        cv.projects, profile.project_overrides, focus, deprio, max_b, include_all
    )

    if profile.project_order is not None:
        order = {name: i for i, name in enumerate(profile.project_order)}
        projects.sort(key=lambda p: order.get(p["name"], 999))

    education: list[dict[str, Any]] = [
        {
            "institution": e.institution,
            "degree": e.degree,
            "location": e.location,
            "start": e.start,
            "end": e.end,
        }
        for e in cv.education
    ]

    return {
        "meta": meta,
        "about": profile.about_override or _resolve(cv.about, variant),
        "experience": experience,
        "skills": skills,
        "projects": projects,
        "education": education,
        "additional": cv.additional.model_dump(),
        "sections": profile.sections,
        "lang": profile.lang,
        "labels": labels,
        "font_family": profile.font_family,
        "font_sizes": profile.font_sizes.model_dump(),
    }
