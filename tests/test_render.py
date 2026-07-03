import pytest

from cv_renderer.render import render


def test_render_general_creates_html():
    out = render("general")
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "Professional Experience" in html
    assert "Your Name" in html


def test_render_ai_engineer_skill_category_order():
    out = render("ai-engineer")
    html = out.read_text(encoding="utf-8")
    expected_order = [
        "AI and LLM Systems",
        "ML and Evaluation",
        "Backend and API",
        "Infra and DevOps",
    ]
    positions = [html.index(cat) for cat in expected_order]
    assert positions == sorted(positions)
    assert "Data Engineering" not in html


def test_render_lang_override_uses_turkish_labels():
    out = render("general", lang="tr")
    html = out.read_text(encoding="utf-8")
    assert 'lang="tr"' in html
    assert "Profesyonel Deneyim" in html


def test_render_missing_profile_raises():
    with pytest.raises(FileNotFoundError):
        render("nonexistent-profile")
