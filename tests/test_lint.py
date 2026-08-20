import textwrap

from cv_renderer import lint


def write_yaml(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


# --- load_yaml_with_lines -----------------------------------------------------


def test_load_yaml_with_lines_tracks_bullet_line(tmp_path):
    path = write_yaml(
        tmp_path,
        "base_en.yaml",
        """\
        experience:
          - company: Acme
            bullets:
              - text: "Did a thing"
                tags: [ai]
        """,
    )
    raw = lint.load_yaml_with_lines(path)
    bullet = raw["experience"][0]["bullets"][0]
    assert bullet["__line__"] == 4


# --- TAG-UNKNOWN / TAG-EMPTY ---------------------------------------------------


def test_check_tags_flags_unknown_tag(tmp_path):
    path = write_yaml(
        tmp_path,
        "base_en.yaml",
        """\
        experience:
          - company: Acme
            tags: [ai]
            bullets:
              - text: "Did a thing"
                tags: [totally-made-up]
        """,
    )
    raw = lint.load_yaml_with_lines(path)
    findings = lint._check_tags(raw, "base_en.yaml", vocab={"ai", "always"})
    unknown = [f for f in findings if f.rule == "TAG-UNKNOWN"]
    assert len(unknown) == 1
    assert "totally-made-up" in unknown[0].message


def test_check_tags_flags_empty_bullet_tags(tmp_path):
    path = write_yaml(
        tmp_path,
        "base_en.yaml",
        """\
        experience:
          - company: Acme
            tags: [ai]
            bullets:
              - text: "Did a thing"
                tags: []
        """,
    )
    raw = lint.load_yaml_with_lines(path)
    findings = lint._check_tags(raw, "base_en.yaml", vocab={"ai"})
    assert any(f.rule == "TAG-EMPTY" for f in findings)


def test_check_tags_allows_empty_skill_item_tags(tmp_path):
    path = write_yaml(
        tmp_path,
        "base_en.yaml",
        """\
        skills:
          - category: Tools
            tags: [backend]
            items:
              - text: Generic Tool
                tags: []
        """,
    )
    raw = lint.load_yaml_with_lines(path)
    findings = lint._check_tags(raw, "base_en.yaml", vocab={"backend"})
    assert not any(f.rule == "TAG-EMPTY" for f in findings)


# --- DATE-ORDER -----------------------------------------------------------------


def test_check_date_order_flags_start_after_end(tmp_path):
    path = write_yaml(
        tmp_path,
        "base_en.yaml",
        """\
        experience:
          - company: Acme
            start: "2024-06"
            end: "2023-01"
        """,
    )
    raw = lint.load_yaml_with_lines(path)
    findings = lint._check_date_order(raw, "base_en.yaml")
    assert len(findings) == 1
    assert findings[0].rule == "DATE-ORDER"


def test_check_date_order_allows_present():
    raw = {"experience": [{"company": "Acme", "start": "2024-01", "end": "present", "__line__": 1}]}
    findings = lint._check_date_order(raw, "base_en.yaml")
    assert findings == []


# --- profile focus/deprio ---------------------------------------------------


def test_check_profile_focus_tags_flags_unknown_and_overlap():
    raw_profile = {
        "focus_tags": ["ai", "bogus"],
        "deprioritize_tags": ["ai"],
        "__line__": 1,
    }
    findings = lint._check_profile_focus_tags(raw_profile, "profile.yaml", vocab={"ai", "data"})
    assert any(f.rule == "TAG-UNKNOWN" for f in findings)
    assert any(f.rule == "PROF-OVERLAP" for f in findings)


# --- profile overrides -------------------------------------------------------


def test_check_profile_overrides_flags_unknown_company_and_project():
    raw_profile = {
        "experience_overrides": {"Nonexistent Co": ["bullet"]},
        "project_overrides": {"Nonexistent Project": ["bullet"]},
        "project_order": ["Also Nonexistent"],
        "__line__": 1,
    }
    findings = lint._check_profile_overrides(
        raw_profile, "profile.yaml", companies={"Real Co"}, project_names={"Real Project"}
    )
    assert sum(f.rule == "PROF-COMPANY" for f in findings) == 1
    assert sum(f.rule == "PROF-PROJECT" for f in findings) == 2


def test_check_profile_overrides_flags_unknown_experience_location_company():
    raw_profile = {
        "experience_location_overrides": {"Nonexistent Co": "Turkey"},
        "__line__": 1,
    }
    findings = lint._check_profile_overrides(
        raw_profile, "profile.yaml", companies={"Real Co"}, project_names=set()
    )
    assert sum(f.rule == "PROF-COMPANY" for f in findings) == 1


def test_check_profile_overrides_allows_known_keys():
    raw_profile = {
        "experience_overrides": {"Real Co": ["bullet"]},
        "experience_location_overrides": {"Real Co": "Turkey"},
        "project_overrides": {"Real Project": ["bullet"]},
        "__line__": 1,
    }
    findings = lint._check_profile_overrides(
        raw_profile, "profile.yaml", companies={"Real Co"}, project_names={"Real Project"}
    )
    assert findings == []


def test_check_profile_style_scans_project_overrides():
    raw_profile = {
        "__line__": 1,
        "project_overrides": {"Widget": ["Helped the team ship a feature."]},
    }
    findings = lint._check_profile_style(raw_profile, "profile.yaml", "en")
    assert any(f.rule == "STYLE-WEAK-LEAD" for f in findings)


# --- NO-COMPANY-NAME ----------------------------------------------------------


def test_check_profile_company_name_flags_leak():
    raw_profile = {
        "__line__": 1,
        "name": "Spotify - Backend Engineer",
        "about_override": "Backend Engineer excited to join Spotify's platform team.",
    }
    findings = lint._check_profile_company_name(raw_profile, "profile.yaml")
    assert len(findings) == 1
    assert findings[0].rule == "NO-COMPANY-NAME"
    assert "Spotify" in findings[0].message


def test_check_profile_company_name_ignores_when_absent():
    raw_profile = {
        "__line__": 1,
        "name": "Spotify - Backend Engineer",
        "about_override": "Backend Engineer with production FastAPI experience.",
    }
    findings = lint._check_profile_company_name(raw_profile, "profile.yaml")
    assert findings == []


def test_check_profile_company_name_respects_word_boundary():
    raw_profile = {
        "__line__": 1,
        "name": "One - Data Engineer",
        "about_override": "Helped someone build data pipelines.",
    }
    findings = lint._check_profile_company_name(raw_profile, "profile.yaml")
    assert findings == []


def test_check_profile_company_name_skips_short_or_missing_name():
    raw_profile = {"__line__": 1, "name": "", "about_override": "Anything goes here."}
    assert lint._check_profile_company_name(raw_profile, "profile.yaml") == []


def test_lint_company_name_leak_only_applies_to_companies_dir(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    base = """\
        meta:
          name: Test
          title: {default: Engineer}
          location: City
          email: a@b.com
          phone: "+1"
          links: {}
        about: {default: "About."}
        experience: []
        education: []
        skills: []
        projects: []
        additional: {languages: [], certifications: []}
        """
    write_yaml(data_dir, "base_en.yaml", base)
    write_yaml(data_dir, "base_tr.yaml", base)

    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "companies").mkdir()
    write_yaml(
        profiles_dir / "companies",
        "acme.yaml",
        """\
        name: Acme - Engineer
        lang: en
        about_override: "Excited to join Acme."
        """,
    )
    write_yaml(
        profiles_dir,
        "acme.yaml",
        """\
        name: Acme - Engineer
        lang: en
        about_override: "Excited to join Acme."
        """,
    )

    monkeypatch.setattr("cv_renderer.loader._USER_DATA", tmp_path)

    company_findings = lint.lint("companies/acme")
    assert any(f.rule == "NO-COMPANY-NAME" for f in company_findings)

    archetype_findings = lint.lint("acme")
    assert not any(f.rule == "NO-COMPANY-NAME" for f in archetype_findings)


# --- PARITY --------------------------------------------------------------------


def test_check_parity_flags_bullet_count_and_tag_mismatch():
    raw_en = {
        "experience": [
            {
                "company": "Acme",
                "tags": ["ai"],
                "bullets": [{"text": "A"}, {"text": "B"}],
                "__line__": 1,
            }
        ],
        "projects": [],
        "skills": [],
    }
    raw_tr = {
        "experience": [
            {
                "company": "Sirket",
                "tags": ["data"],
                "bullets": [{"text": "A"}],
                "__line__": 1,
            }
        ],
        "projects": [],
        "skills": [],
    }
    findings = lint._check_parity(raw_en, raw_tr, "base_en.yaml", "base_tr.yaml")
    assert any(f.rule == "PARITY-BULLET-COUNT" for f in findings)
    assert any(f.rule == "PARITY-TAGS" for f in findings)


def test_check_parity_clean_when_matching():
    raw = {
        "experience": [
            {"company": "Acme", "tags": ["ai"], "bullets": [{"text": "A"}], "__line__": 1}
        ],
        "projects": [],
        "skills": [],
    }
    findings = lint._check_parity(raw, dict(raw), "base_en.yaml", "base_tr.yaml")
    assert findings == []


# --- STYLE (INFO) ------------------------------------------------------------


def test_check_style_flags_passive_pronoun_and_weak_lead():
    raw = {
        "experience": [
            {
                "company": "Acme",
                "bullets": [
                    {"text": "The system was optimized by me.", "__line__": 1},
                    {"text": "Helped the team ship a feature.", "__line__": 2},
                ],
            }
        ],
        "projects": [],
    }
    findings = lint._check_style(raw, "base_en.yaml", "en")
    rules = {f.rule for f in findings}
    assert "STYLE-PASSIVE" in rules
    assert "STYLE-PRONOUN" in rules
    assert "STYLE-WEAK-LEAD" in rules


# --- format_report -------------------------------------------------------------


def test_format_report_summarizes_counts():
    findings = [
        lint.Finding("ERROR", "base_en.yaml", 3, "TAG-UNKNOWN", "bad tag"),
        lint.Finding("WARNING", "base_en.yaml", 5, "NO-COMPANY-NAME", "company named"),
        lint.Finding("INFO", "base_en.yaml", 7, "STYLE-PASSIVE", "passive voice"),
    ]
    report = lint.format_report(findings)
    assert "1 errors, 1 warnings, 1 info" in report
    assert "fix errors before rendering" in report


def test_format_report_no_errors_omits_fix_message():
    findings = [lint.Finding("INFO", "base_en.yaml", 1, "STYLE-PASSIVE", "passive voice")]
    report = lint.format_report(findings)
    assert "fix errors" not in report


# --- end-to-end -----------------------------------------------------------------


def test_lint_runs_clean_against_examples():
    # isolate_cv_data (autouse) points _USER_DATA at examples/, so this exercises
    # the full lint() entrypoint against the checked-in template data.
    findings = lint.lint()
    assert isinstance(findings, list)
    assert not any(f.rule == "TAG-UNKNOWN" for f in findings)


def test_lint_profile_specific_prof_company(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "labels").mkdir()
    base = """\
        meta:
          name: Test
          title: {default: Engineer}
          location: City
          email: a@b.com
          phone: "+1"
          links: {}
        about: {default: "About."}
        experience:
          - company: Real Co
            title: {default: Engineer}
            location: City
            start: "2024"
            end: present
            tags: [ai]
            bullets:
              - text: "Did a thing"
                tags: [ai]
        education: []
        skills: []
        projects: []
        additional: {languages: [], certifications: []}
        """
    write_yaml(data_dir, "base_en.yaml", base)
    write_yaml(data_dir, "base_tr.yaml", base)

    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    write_yaml(
        profiles_dir,
        "broken.yaml",
        """\
        name: Broken
        lang: en
        experience_overrides:
          Nonexistent Co: ["bullet"]
        """,
    )

    monkeypatch.setattr("cv_renderer.loader._USER_DATA", tmp_path)
    findings = lint.lint("broken")
    assert any(f.rule == "PROF-COMPANY" for f in findings)
