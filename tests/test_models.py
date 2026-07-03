import pytest
from pydantic import ValidationError

from cv_renderer.loader import load_cv
from cv_renderer.models import ExperienceEntry, Profile, SkillCategory


def test_cv_data_validates_against_example():
    cv = load_cv("en")
    assert cv.meta.name
    assert cv.experience
    assert cv.skills


def test_normalize_items_comma_string():
    cat = SkillCategory(category="Backend", tags=["backend"], items="Python, FastAPI, Redis")
    assert [item.text for item in cat.items] == ["Python", "FastAPI", "Redis"]
    assert all(item.tags == [] for item in cat.items)


def test_normalize_items_mixed_list():
    cat = SkillCategory(
        category="AI",
        tags=["ai"],
        items=["LangChain", {"text": "LangGraph", "tags": ["ai"]}],
    )
    assert cat.items[0].text == "LangChain"
    assert cat.items[0].tags == []
    assert cat.items[1].text == "LangGraph"
    assert cat.items[1].tags == ["ai"]


def test_normalize_items_pure_dict_list():
    cat = SkillCategory(
        category="AI",
        tags=["ai"],
        items=[{"text": "LangChain", "tags": ["ai"]}, {"text": "LangGraph", "tags": ["ai"]}],
    )
    assert [item.text for item in cat.items] == ["LangChain", "LangGraph"]


def test_experience_entry_missing_company_raises():
    with pytest.raises(ValidationError):
        ExperienceEntry(
            title={"default": "Engineer"},
            location="City",
            start="2024",
            end="present",
            tags=["ai"],
            bullets=[],
        )


def test_profile_defaults():
    profile = Profile(name="Minimal")
    assert profile.lang == "en"
    assert profile.variant == "default"
    assert profile.max_bullets_per_job == 10
    assert profile.sections == ["experience", "projects", "skills", "education", "additional"]
    assert profile.skill_categories is None
    assert profile.focus_tags == []
    assert profile.deprioritize_tags == []


def test_profile_with_overrides_validates():
    profile = Profile(
        name="Custom",
        title_override="Backend Engineer",
        about_override="Summary text.",
        experience_overrides={"Company Name": ["Rewritten bullet."]},
        project_overrides={"Project Name": ["Rewritten project bullet."]},
        project_order=["Project Name"],
        skill_overrides={"Custom Category": ["Item A", "Item B"]},
        focus_tags=["data", "backend"],
        deprioritize_tags=["ai"],
    )
    assert profile.title_override == "Backend Engineer"
    assert profile.experience_overrides["Company Name"] == ["Rewritten bullet."]
    assert profile.skill_overrides["Custom Category"] == ["Item A", "Item B"]
