from cv_renderer.filter import apply_profile
from cv_renderer.models import (
    Additional,
    Bullet,
    CVData,
    ExperienceEntry,
    Links,
    Meta,
    Profile,
    Project,
    SkillCategory,
)

LABELS = {"months": ["Jan"], "present": "Present"}


def make_meta(**overrides):
    defaults = dict(
        name="Test Person",
        title={"default": "Engineer", "ai": "AI Engineer"},
        location="City",
        email="test@example.com",
        phone="+1 555",
        links=Links(),
    )
    defaults.update(overrides)
    return Meta(**defaults)


def make_job(company="Acme", tags=None, bullets=None, **overrides):
    defaults = dict(
        company=company,
        title={"default": "Engineer"},
        location="City",
        start="2024",
        end="present",
        tags=tags or ["ai"],
        bullets=bullets or [Bullet(text="Did a thing", tags=["ai"])],
    )
    defaults.update(overrides)
    return ExperienceEntry(**defaults)


def make_project(name="Widget", tags=None, bullets=None, **overrides):
    defaults = dict(
        name=name,
        tags=tags or ["ai"],
        bullets=bullets or [Bullet(text="Built a thing", tags=["ai"])],
    )
    defaults.update(overrides)
    return Project(**defaults)


def make_skill_category(category="AI Tools", tags=None, items=None):
    return SkillCategory(category=category, tags=tags or ["ai"], items=items or "Item A, Item B")


def make_cv(experience=None, skills=None, projects=None, about=None, education=None):
    return CVData(
        meta=make_meta(),
        about=about or {"default": "Default about.", "ai": "AI about."},
        experience=experience if experience is not None else [make_job()],
        education=education if education is not None else [],
        skills=skills if skills is not None else [],
        projects=projects if projects is not None else [],
        additional=Additional(languages=[], certifications=[]),
    )


def make_profile(**overrides):
    return Profile(name="Test Profile", **overrides)


# --- focus / deprioritize ---------------------------------------------------


def test_empty_focus_shows_all_bullets():
    job = make_job(
        bullets=[
            Bullet(text="A", tags=["ai"]),
            Bullet(text="B", tags=["data"]),
        ]
    )
    cv = make_cv(experience=[job])
    out = apply_profile(cv, make_profile(), LABELS)
    assert out["experience"][0]["bullets"] == ["A", "B"]


def test_focus_bullet_wins_even_with_deprioritized_tag():
    job = make_job(
        bullets=[Bullet(text="Focused", tags=["ai", "data"])],
    )
    cv = make_cv(experience=[job])
    profile = make_profile(focus_tags=["ai"], deprioritize_tags=["data"])
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"][0]["bullets"] == ["Focused"]


def test_bullet_subset_of_deprio_is_dropped():
    job = make_job(
        bullets=[
            Bullet(text="Keep", tags=["ai"]),
            Bullet(text="Drop", tags=["data"]),
        ]
    )
    cv = make_cv(experience=[job])
    profile = make_profile(focus_tags=["ai"], deprioritize_tags=["data"])
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"][0]["bullets"] == ["Keep"]


def test_bullet_with_tag_outside_deprio_survives_as_neutral():
    job = make_job(
        bullets=[
            Bullet(text="Focused", tags=["ai"]),
            Bullet(text="Neutral", tags=["devops"]),
        ]
    )
    cv = make_cv(experience=[job])
    profile = make_profile(focus_tags=["ai"], deprioritize_tags=["data"])
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"][0]["bullets"] == ["Focused", "Neutral"]


# --- max_bullets_per_job -----------------------------------------------------


def test_max_bullets_caps_output_focused_first():
    job = make_job(
        bullets=[
            Bullet(text="Neutral1", tags=["devops"]),
            Bullet(text="Focused", tags=["ai"]),
            Bullet(text="Neutral2", tags=["devops"]),
        ]
    )
    cv = make_cv(experience=[job])
    profile = make_profile(focus_tags=["ai"], max_bullets_per_job=2)
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"][0]["bullets"] == ["Focused", "Neutral1"]


def test_max_bullets_zero_drops_job():
    cv = make_cv(experience=[make_job()])
    profile = make_profile(max_bullets_per_job=0)
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"] == []


# --- experience_overrides -----------------------------------------------------


def test_experience_override_replaces_bullets():
    cv = make_cv(experience=[make_job(company="Acme")])
    profile = make_profile(experience_overrides={"Acme": ["Rewritten bullet."]})
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"][0]["bullets"] == ["Rewritten bullet."]


def test_experience_override_empty_list_drops_job():
    cv = make_cv(experience=[make_job(company="Acme")])
    profile = make_profile(experience_overrides={"Acme": []})
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"] == []


def test_experience_override_forces_job_to_appear():
    job = make_job(company="Acme", tags=["ml"], bullets=[Bullet(text="Orig", tags=["ml"])])
    cv = make_cv(experience=[job])
    profile = make_profile(focus_tags=["data"], experience_overrides={"Acme": ["Forced in."]})
    out = apply_profile(cv, profile, LABELS)
    assert len(out["experience"]) == 1
    assert out["experience"][0]["bullets"] == ["Forced in."]


def test_experience_location_override_replaces_only_that_job():
    cv = make_cv(experience=[make_job(company="Acme"), make_job(company="Globex")])
    profile = make_profile(experience_location_overrides={"Acme": "Turkey"})
    out = apply_profile(cv, profile, LABELS)
    assert out["experience"][0]["location"] == "Turkey"
    assert out["experience"][1]["location"] == "City"


def test_experience_location_falls_back_to_base_data():
    cv = make_cv(experience=[make_job(company="Acme")])
    out = apply_profile(cv, make_profile(), LABELS)
    assert out["experience"][0]["location"] == "City"


# --- skill_categories / skill_overrides --------------------------------------


def test_skill_categories_filters_and_orders():
    cats = [
        make_skill_category(category="B", tags=["data"]),
        make_skill_category(category="A", tags=["ai"]),
        make_skill_category(category="C", tags=["devops"]),
    ]
    cv = make_cv(skills=cats)
    profile = make_profile(skill_categories=["A", "B"])
    out = apply_profile(cv, profile, LABELS)
    assert [s["category"] for s in out["skills"]] == ["A", "B"]


def test_skill_categories_none_includes_all():
    cats = [make_skill_category(category="A"), make_skill_category(category="B")]
    cv = make_cv(skills=cats)
    out = apply_profile(cv, make_profile(), LABELS)
    assert {s["category"] for s in out["skills"]} == {"A", "B"}


def test_skill_overrides_replaces_section_entirely():
    cats = [make_skill_category(category="A", tags=["ai"])]
    cv = make_cv(skills=cats)
    profile = make_profile(
        skill_categories=["Nonexistent"],
        skill_overrides={"Custom": ["X", "Y"]},
    )
    out = apply_profile(cv, profile, LABELS)
    assert out["skills"] == [{"category": "Custom", "entries": ["X", "Y"]}]


# --- skill item filtering -----------------------------------------------------


def test_skill_item_untagged_always_kept():
    # Category tagged "always" so it survives the category-level tag gate
    # regardless of focus/deprioritize — isolates item-level filtering behavior.
    cat = make_skill_category(
        category="Tools",
        tags=["always"],
        items=[{"text": "Generic", "tags": []}, {"text": "AISpecific", "tags": ["ai"]}],
    )
    cv = make_cv(skills=[cat])
    profile = make_profile(focus_tags=["data"], deprioritize_tags=["ai"])
    out = apply_profile(cv, profile, LABELS)
    assert out["skills"][0]["entries"] == ["Generic"]


def test_skill_item_focus_match_included():
    cat = make_skill_category(
        category="Tools",
        tags=["ai"],
        items=[{"text": "AISpecific", "tags": ["ai"]}],
    )
    cv = make_cv(skills=[cat])
    profile = make_profile(focus_tags=["ai"])
    out = apply_profile(cv, profile, LABELS)
    assert out["skills"][0]["entries"] == ["AISpecific"]


# --- projects ------------------------------------------------------------


def test_project_focus_excludes_non_matching():
    projects = [make_project(name="P1", tags=["ai"]), make_project(name="P2", tags=["data"])]
    cv = make_cv(projects=projects)
    profile = make_profile(focus_tags=["ai"])
    out = apply_profile(cv, profile, LABELS)
    assert [p["name"] for p in out["projects"]] == ["P1"]


def test_project_override_forces_inclusion():
    projects = [make_project(name="P1", tags=["data"])]
    cv = make_cv(projects=projects)
    profile = make_profile(focus_tags=["ai"], project_overrides={"P1": ["Forced bullet."]})
    out = apply_profile(cv, profile, LABELS)
    assert out["projects"][0]["bullets"] == ["Forced bullet."]


def test_project_order_resorts_projects():
    projects = [make_project(name="P1"), make_project(name="P2"), make_project(name="P3")]
    cv = make_cv(projects=projects)
    profile = make_profile(project_order=["P3", "P1"])
    out = apply_profile(cv, profile, LABELS)
    assert [p["name"] for p in out["projects"]] == ["P3", "P1", "P2"]


# --- about/title variant resolution ------------------------------------------


def test_variant_resolution_falls_back_to_default():
    cv = make_cv(about={"default": "Default about."})
    profile = make_profile(variant="ai")
    out = apply_profile(cv, profile, LABELS)
    assert out["about"] == "Default about."


def test_variant_resolution_picks_matching_variant():
    cv = make_cv(about={"default": "Default about.", "ai": "AI about."})
    profile = make_profile(variant="ai")
    out = apply_profile(cv, profile, LABELS)
    assert out["about"] == "AI about."


def test_about_override_takes_priority():
    cv = make_cv(about={"default": "Default about.", "ai": "AI about."})
    profile = make_profile(variant="ai", about_override="Overridden about.")
    out = apply_profile(cv, profile, LABELS)
    assert out["about"] == "Overridden about."


def test_title_override_takes_priority():
    job = make_job()
    cv = make_cv(experience=[job])
    profile = make_profile(title_override="Custom Title")
    out = apply_profile(cv, profile, LABELS)
    assert out["meta"]["title"] == "Custom Title"


def test_name_override_takes_priority():
    cv = make_cv(experience=[make_job()])
    profile = make_profile(name_override="Test Person")
    out = apply_profile(cv, profile, LABELS)
    assert out["meta"]["name"] == "Test Person"


def test_location_override_takes_priority():
    cv = make_cv(experience=[make_job()])
    profile = make_profile(location_override="Remote")
    out = apply_profile(cv, profile, LABELS)
    assert out["meta"]["location"] == "Remote"


# --- lang passthrough ---------------------------------------------------------


def test_lang_passthrough():
    cv = make_cv()
    profile = make_profile(lang="tr")
    out = apply_profile(cv, profile, LABELS)
    assert out["lang"] == "tr"
