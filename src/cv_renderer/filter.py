from cv_renderer.models import Bullet, CVData, Profile


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


def apply_profile(cv: CVData, profile: Profile, labels: dict[str, str]) -> dict:
    variant = profile.variant
    focus = set(profile.focus_tags)
    deprio = set(profile.deprioritize_tags)
    max_b = profile.max_bullets_per_job
    include_all = not focus

    meta = {
        "name": cv.meta.name,
        "title": _resolve(cv.meta.title, variant),
        "location": cv.meta.location,
        "email": cv.meta.email,
        "phone": cv.meta.phone,
        "links": cv.meta.links.model_dump(),
    }

    experience = []
    for job in cv.experience:
        bullets = _filter_bullets(job.bullets, focus, deprio, max_b)
        if not bullets:
            continue
        experience.append({
            "company": job.company,
            "title": _resolve(job.title, variant),
            "location": job.location,
            "start": job.start,
            "end": job.end,
            "description": job.description,
            "bullets": bullets,
        })

    include_tags = focus | {"always"}
    skills = []
    for cat in cv.skills:
        if profile.skill_categories is not None:
            if cat.category not in profile.skill_categories:
                continue
        elif not include_all and not (set(cat.tags) & include_tags):
            continue
        skills.append({"category": cat.category, "entries": cat.items})

    if profile.skill_categories is not None:
        order = {name: i for i, name in enumerate(profile.skill_categories)}
        skills.sort(key=lambda s: order.get(s["category"], 999))

    projects = []
    for proj in cv.projects:
        if not include_all and not (set(proj.tags) & focus):
            continue
        bullets = _filter_bullets(proj.bullets, focus, deprio, max_b)
        if not bullets:
            continue
        projects.append({
            "name": proj.name,
            "subtitle": proj.subtitle,
            "year": proj.year,
            "start": proj.start,
            "end": proj.end,
            "bullets": bullets,
        })

    education = [
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
        "about": _resolve(cv.about, variant),
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
