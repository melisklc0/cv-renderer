from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from cv_renderer import loader

JsonDict = dict[str, Any]
# (text, line, context) — one free-text field worth checking against wording rules.
TextItem = tuple[Any, "int | None", str]
# (tags, line, context, is_bullet) — one tag-bearing object. is_bullet marks bullets
# specifically, since only bullets are required to carry at least one tag.
TaggedItem = tuple["list[str] | None", "int | None", str, bool]

_LEVEL_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}

_BACKED_RE = re.compile(r"\b(\w+)-backed\b", re.IGNORECASE)
_PASSIVE_RE = re.compile(r"\b(was|were|been|being)\s+\w+ed\b", re.IGNORECASE)
_PRONOUN_RE = {
    "en": re.compile(r"\b(I|we|my|our|me|us)\b", re.IGNORECASE),
    "tr": re.compile(r"\b(ben|biz|benim|bizim)\b", re.IGNORECASE),
}
_WEAK_LEADS = {"helped", "worked", "responsible", "involved", "assisted"}


@dataclass
class Finding:
    level: str  # ERROR | WARNING | INFO
    file: str
    line: int | None
    rule: str
    message: str

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line if self.line is not None else '?'}"
        return f"{loc}: {self.level} [{self.rule}] {self.message}"


# --- line-tracking YAML load --------------------------------------------------
# Every mapping gets a '__line__' sentinel key so rules can report exact source
# lines. Plain scalar list items (e.g. comma-shorthand skill items) have no
# line of their own — only the enclosing mapping's line is available for those.


class _LineLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader_: yaml.SafeLoader, node: yaml.MappingNode) -> JsonDict:
    loader_.flatten_mapping(node)
    mapping = dict(loader_.construct_pairs(node))
    mapping["__line__"] = node.start_mark.line + 1
    return mapping


_LineLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml_with_lines(path: Path) -> JsonDict:
    with open(path, encoding="utf-8") as f:
        data: JsonDict = yaml.load(f, Loader=_LineLoader)
    return data


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(loader._user_data_root()))
    except ValueError:
        return path.name


# --- collecting checkable content ----------------------------------------------
# Every rule below operates on plain (value, line, context) tuples gathered by the
# functions in this section, instead of walking the raw YAML tree itself. This
# keeps each rule a single flat loop and means a rule written for base CV data
# automatically also applies to profile override content.


def _iter_tagged_items(raw: JsonDict) -> list[TaggedItem]:
    items: list[TaggedItem] = []

    for job in raw.get("experience", []):
        company = job.get("company")
        items.append((job.get("tags", []), job.get("__line__"), f"experience[{company}]", False))
        for bullet in job.get("bullets", []):
            items.append(
                (
                    bullet.get("tags", []),
                    bullet.get("__line__"),
                    f"bullet in experience[{company}]",
                    True,
                )
            )

    for edu in raw.get("education", []):
        items.append(
            (
                edu.get("tags", []),
                edu.get("__line__"),
                f"education[{edu.get('institution')}]",
                False,
            )
        )

    for cat in raw.get("skills", []):
        category = cat.get("category")
        items.append(
            (cat.get("tags", []), cat.get("__line__"), f"skill category '{category}'", False)
        )
        skill_items = cat.get("items")
        if isinstance(skill_items, list):
            for item in skill_items:
                if isinstance(item, dict):
                    items.append(
                        (
                            item.get("tags", []),
                            item.get("__line__"),
                            f"skill item '{item.get('text')}' in '{category}'",
                            False,
                        )
                    )

    for proj in raw.get("projects", []):
        name = proj.get("name")
        items.append((proj.get("tags", []), proj.get("__line__"), f"project '{name}'", False))
        for bullet in proj.get("bullets", []):
            items.append(
                (
                    bullet.get("tags", []),
                    bullet.get("__line__"),
                    f"bullet in project '{name}'",
                    True,
                )
            )

    return items


def _iter_cv_texts(raw_cv: JsonDict) -> list[TextItem]:
    """Every free-text field in a base CV file worth checking against wording rules."""
    texts: list[TextItem] = []

    about = raw_cv.get("about", {}) or {}
    about_line = about.get("__line__")
    for variant, text in about.items():
        if variant != "__line__":
            texts.append((text, about_line, f"about.{variant}"))

    for job in raw_cv.get("experience", []):
        company = job.get("company")
        for variant, text in (job.get("title") or {}).items():
            if variant != "__line__":
                texts.append((text, job.get("__line__"), f"experience[{company}].title.{variant}"))
        texts.append(
            (job.get("description", ""), job.get("__line__"), f"experience[{company}].description")
        )
        for bullet in job.get("bullets", []):
            texts.append(
                (bullet.get("text", ""), bullet.get("__line__"), f"bullet in experience[{company}]")
            )

    for proj in raw_cv.get("projects", []):
        name = proj.get("name")
        for bullet in proj.get("bullets", []):
            texts.append(
                (bullet.get("text", ""), bullet.get("__line__"), f"bullet in project '{name}'")
            )

    return texts


def _iter_cv_bullet_texts(raw_cv: JsonDict) -> list[TextItem]:
    """Just the bullets (experience + projects) — narrower than _iter_cv_texts,
    used by style rules that only apply to accomplishment bullets, not prose."""
    texts: list[TextItem] = []
    for job in raw_cv.get("experience", []):
        for bullet in job.get("bullets", []):
            texts.append(
                (
                    bullet.get("text", ""),
                    bullet.get("__line__"),
                    f"bullet in experience[{job.get('company')}]",
                )
            )
    for proj in raw_cv.get("projects", []):
        for bullet in proj.get("bullets", []):
            texts.append(
                (
                    bullet.get("text", ""),
                    bullet.get("__line__"),
                    f"bullet in project '{proj.get('name')}'",
                )
            )
    return texts


def _iter_profile_texts(raw_profile: JsonDict) -> list[TextItem]:
    """Every piece of real CV content a profile writes itself — overrides are
    hand-written content, not tag-filtered selections, so they're subject to the
    same wording rules as base_en.yaml/base_tr.yaml."""
    line = raw_profile.get("__line__")
    texts: list[TextItem] = []

    if raw_profile.get("about_override") is not None:
        texts.append((raw_profile["about_override"], line, "about_override"))
    if raw_profile.get("title_override") is not None:
        texts.append((raw_profile["title_override"], line, "title_override"))

    for key in ("experience_overrides", "project_overrides"):
        for entry_name, bullets in (raw_profile.get(key) or {}).items():
            if entry_name == "__line__":
                continue
            for bullet_text in bullets or []:
                texts.append((bullet_text, line, f"{key}['{entry_name}']"))

    return texts


# --- rule appliers ---------------------------------------------------------------
# Each of these is the one place a given rule's logic lives, applied uniformly to
# whatever (tags/text, line, context) items the collectors above hand it.


def _apply_tag_rules(items: list[TaggedItem], filename: str, vocab: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for tags, line, context, is_bullet in items:
        for tag in tags or []:
            if tag not in vocab:
                findings.append(
                    Finding(
                        "ERROR",
                        filename,
                        line,
                        "TAG-UNKNOWN",
                        f"Unknown tag '{tag}' in {context} (not in tags vocabulary)",
                    )
                )
        if is_bullet and not tags:
            findings.append(
                Finding("ERROR", filename, line, "TAG-EMPTY", f"{context} has empty tags: []")
            )
    return findings


def _apply_backed_rule(items: list[TextItem], filename: str) -> list[Finding]:
    findings: list[Finding] = []
    for text, line, context in items:
        if not isinstance(text, str):
            continue
        for m in _BACKED_RE.finditer(text):
            findings.append(
                Finding(
                    "WARNING",
                    filename,
                    line,
                    "SPELL-BACKEND",
                    f'"{m.group(0)}" in {context} — use "{m.group(1)}-backend" instead',
                )
            )
    return findings


def _apply_style_rules(items: list[TextItem], filename: str, lang: str) -> list[Finding]:
    findings: list[Finding] = []
    pronoun_re = _PRONOUN_RE.get(lang, _PRONOUN_RE["en"])
    for text, line, context in items:
        if not isinstance(text, str) or not text:
            continue
        if _PASSIVE_RE.search(text):
            findings.append(
                Finding(
                    "INFO",
                    filename,
                    line,
                    "STYLE-PASSIVE",
                    f'Possible passive voice in {context}: "{text}"',
                )
            )
        if pronoun_re.search(text):
            findings.append(
                Finding(
                    "INFO",
                    filename,
                    line,
                    "STYLE-PRONOUN",
                    f'Personal pronoun in {context}: "{text}"',
                )
            )
        first_word = text.strip().split(" ", 1)[0].lower().strip(".,") if text.strip() else ""
        if first_word in _WEAK_LEADS:
            findings.append(
                Finding(
                    "INFO",
                    filename,
                    line,
                    "STYLE-WEAK-LEAD",
                    f"Weak opening verb '{first_word}' in {context}: \"{text}\"",
                )
            )
    return findings


# --- per-file rule entrypoints ----------------------------------------------------
# Thin, named wrappers around the appliers above — kept separate so each rule's
# scope (base CV data vs. profile overrides) stays explicit and independently
# unit-testable, even though the underlying logic is shared.


def _check_tags(raw: JsonDict, filename: str, vocab: set[str]) -> list[Finding]:
    return _apply_tag_rules(_iter_tagged_items(raw), filename, vocab)


def _check_spelling(raw_en_cv: JsonDict, filename: str) -> list[Finding]:
    return _apply_backed_rule(_iter_cv_texts(raw_en_cv), filename)


def _check_profile_spelling(raw_profile: JsonDict, filename: str) -> list[Finding]:
    return _apply_backed_rule(_iter_profile_texts(raw_profile), filename)


def _check_style(raw_cv: JsonDict, filename: str, lang: str) -> list[Finding]:
    return _apply_style_rules(_iter_cv_bullet_texts(raw_cv), filename, lang)


def _check_profile_style(raw_profile: JsonDict, filename: str, lang: str) -> list[Finding]:
    return _apply_style_rules(_iter_profile_texts(raw_profile), filename, lang)


def _check_profile_company_name(raw_profile: JsonDict, filename: str) -> list[Finding]:
    """AGENTS.md CRITICAL rule: a CV outlives one application, so its content must
    stay company-agnostic — the target company may only appear in the profile's own
    name/filename, never in rendered content. Company profiles follow the
    `name: <Company> - <Role>` convention (see examples/profiles/companies/spotify.yaml),
    so the company is whatever precedes the first " - "."""
    company = (raw_profile.get("name") or "").split(" - ", 1)[0].strip()
    if len(company) < 2:
        return []
    pattern = re.compile(r"\b" + re.escape(company) + r"\b", re.IGNORECASE)
    findings: list[Finding] = []
    for text, line, context in _iter_profile_texts(raw_profile):
        if isinstance(text, str) and pattern.search(text):
            findings.append(
                Finding(
                    "WARNING",
                    filename,
                    line,
                    "NO-COMPANY-NAME",
                    f"Target company '{company}' named in {context} — CV content should stay "
                    "reusable; company-specific wording belongs in a cover letter, not here",
                )
            )
    return findings


def _parse_date(value: Any) -> tuple[int, int] | None:
    s = str(value).strip().lower()
    if s == "present":
        return (9999, 12)
    if "-" in s:
        year, month = s.split("-", 1)
        try:
            return (int(year), int(month))
        except ValueError:
            return None
    try:
        return (int(s), 1)
    except ValueError:
        return None


def _check_date_order(raw: JsonDict, filename: str) -> list[Finding]:
    findings: list[Finding] = []
    for section, label_field in (("experience", "company"), ("education", "institution")):
        for entry in raw.get(section, []):
            start = _parse_date(entry.get("start"))
            end = _parse_date(entry.get("end"))
            if start is not None and end is not None and start > end:
                findings.append(
                    Finding(
                        "ERROR",
                        filename,
                        entry.get("__line__"),
                        "DATE-ORDER",
                        f"{section}[{entry.get(label_field)}]: start ({entry.get('start')}) "
                        f"is after end ({entry.get('end')})",
                    )
                )
    return findings


def _check_profile_focus_tags(
    raw_profile: JsonDict, filename: str, vocab: set[str]
) -> list[Finding]:
    findings: list[Finding] = []
    line = raw_profile.get("__line__")
    focus = raw_profile.get("focus_tags") or []
    deprio = raw_profile.get("deprioritize_tags") or []
    for key, tags in (("focus_tags", focus), ("deprioritize_tags", deprio)):
        for tag in tags:
            if tag not in vocab:
                findings.append(
                    Finding(
                        "ERROR",
                        filename,
                        line,
                        "TAG-UNKNOWN",
                        f"Unknown tag '{tag}' in profile's {key}",
                    )
                )
    overlap = set(focus) & set(deprio)
    if overlap:
        findings.append(
            Finding(
                "ERROR",
                filename,
                line,
                "PROF-OVERLAP",
                f"focus_tags and deprioritize_tags overlap: {sorted(overlap)}",
            )
        )
    return findings


def _check_profile_overrides(
    raw_profile: JsonDict, filename: str, companies: set[str], project_names: set[str]
) -> list[Finding]:
    findings: list[Finding] = []
    line = raw_profile.get("__line__")

    for key in raw_profile.get("experience_overrides", {}) or {}:
        if key == "__line__":
            continue
        if key not in companies:
            findings.append(
                Finding(
                    "ERROR",
                    filename,
                    line,
                    "PROF-COMPANY",
                    f"experience_overrides key '{key}' doesn't match any company "
                    "in that profile's language base file",
                )
            )

    project_keys = [k for k in (raw_profile.get("project_overrides", {}) or {}) if k != "__line__"]
    project_keys += list(raw_profile.get("project_order") or [])
    for key in project_keys:
        if key not in project_names:
            findings.append(
                Finding(
                    "ERROR",
                    filename,
                    line,
                    "PROF-PROJECT",
                    f"'{key}' (project_overrides/project_order) doesn't match any project "
                    "name in that profile's language base file",
                )
            )

    return findings


def _check_parity(raw_en: JsonDict, raw_tr: JsonDict, file_en: str, file_tr: str) -> list[Finding]:
    findings: list[Finding] = []

    exp_en, exp_tr = raw_en.get("experience", []), raw_tr.get("experience", [])
    for i in range(max(len(exp_en), len(exp_tr))):
        job_en = exp_en[i] if i < len(exp_en) else None
        job_tr = exp_tr[i] if i < len(exp_tr) else None
        if job_en is None or job_tr is None:
            findings.append(
                Finding(
                    "WARNING",
                    file_tr,
                    None,
                    "PARITY-BULLET-COUNT",
                    f"experience[{i}] exists in one language file but not the other",
                )
            )
            continue
        bullets_en, bullets_tr = len(job_en.get("bullets", [])), len(job_tr.get("bullets", []))
        if bullets_en != bullets_tr:
            findings.append(
                Finding(
                    "WARNING",
                    file_tr,
                    job_tr.get("__line__"),
                    "PARITY-BULLET-COUNT",
                    f"experience[{i}] ('{job_en.get('company')}' / '{job_tr.get('company')}'): "
                    f"{bullets_en} EN bullets vs {bullets_tr} TR bullets",
                )
            )
        tags_en, tags_tr = job_en.get("tags", []), job_tr.get("tags", [])
        if tags_en != tags_tr:
            findings.append(
                Finding(
                    "WARNING",
                    file_tr,
                    job_tr.get("__line__"),
                    "PARITY-TAGS",
                    f"experience[{i}] tags differ between EN {tags_en} and TR {tags_tr} "
                    "(tags are structural and must be identical across languages)",
                )
            )

    projects_en, projects_tr = raw_en.get("projects", []), raw_tr.get("projects", [])
    if len(projects_en) != len(projects_tr):
        findings.append(
            Finding(
                "WARNING",
                file_tr,
                None,
                "PARITY-PROJECT-COUNT",
                f"{len(projects_en)} EN projects vs {len(projects_tr)} TR projects",
            )
        )

    skills_en, skills_tr = raw_en.get("skills", []), raw_tr.get("skills", [])
    if len(skills_en) != len(skills_tr):
        findings.append(
            Finding(
                "WARNING",
                file_tr,
                None,
                "PARITY-SKILL-CAT-COUNT",
                f"{len(skills_en)} EN skill categories vs {len(skills_tr)} TR skill categories",
            )
        )

    return findings


# --- entrypoint ------------------------------------------------------------------


def lint(profile_name: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    vocab = set(loader.load_tags().keys())

    raw_by_lang: dict[str, tuple[JsonDict, str]] = {}
    for lang in ("en", "tr"):
        path = loader._user_data_root() / "data" / f"base_{lang}.yaml"
        raw = load_yaml_with_lines(path)
        raw_by_lang[lang] = (raw, _rel(path))
        findings += _check_tags(raw, _rel(path), vocab)
        findings += _check_date_order(raw, _rel(path))

    raw_en, file_en = raw_by_lang["en"]
    raw_tr, file_tr = raw_by_lang["tr"]
    findings += _check_spelling(raw_en, file_en)
    findings += _check_parity(raw_en, raw_tr, file_en, file_tr)
    findings += _check_style(raw_en, file_en, "en")
    findings += _check_style(raw_tr, file_tr, "tr")

    companies = {
        "en": {j.get("company") for j in raw_en.get("experience", [])},
        "tr": {j.get("company") for j in raw_tr.get("experience", [])},
    }
    project_names = {
        "en": {p.get("name") for p in raw_en.get("projects", [])},
        "tr": {p.get("name") for p in raw_tr.get("projects", [])},
    }

    profiles_dir = loader._user_data_root() / "profiles"
    if profile_name is not None:
        profile_paths = [profiles_dir / f"{profile_name}.yaml"]
    else:
        profile_paths = sorted(profiles_dir.glob("**/*.yaml"))

    for path in profile_paths:
        if not path.exists():
            continue
        raw_profile = load_yaml_with_lines(path)
        profile_lang = raw_profile.get("lang", "en")
        filename = _rel(path)
        findings += _check_profile_focus_tags(raw_profile, filename, vocab)
        findings += _check_profile_overrides(
            raw_profile,
            filename,
            companies.get(profile_lang, set()),
            project_names.get(profile_lang, set()),
        )
        if profile_lang == "en":
            findings += _check_profile_spelling(raw_profile, filename)
        findings += _check_profile_style(raw_profile, filename, profile_lang)
        if path.parent.name == "companies":
            findings += _check_profile_company_name(raw_profile, filename)

    return findings


def format_report(findings: list[Finding]) -> str:
    ordered = sorted(findings, key=lambda f: (f.file, f.line or 0, _LEVEL_ORDER[f.level]))
    lines = [str(f) for f in ordered]
    errors = sum(1 for f in findings if f.level == "ERROR")
    warnings = sum(1 for f in findings if f.level == "WARNING")
    infos = sum(1 for f in findings if f.level == "INFO")
    summary = f"{errors} errors, {warnings} warnings, {infos} info"
    if errors:
        summary += " — fix errors before rendering."
    lines.append("")
    lines.append(summary)
    return "\n".join(lines)


def format_json(findings: list[Finding]) -> str:
    """Machine-readable report for external callers (e.g. job-assistant's bridge)."""
    ordered = sorted(findings, key=lambda f: (f.file, f.line or 0, _LEVEL_ORDER[f.level]))
    payload = {
        "findings": [asdict(f) for f in ordered],
        "summary": {
            "errors": sum(1 for f in findings if f.level == "ERROR"),
            "warnings": sum(1 for f in findings if f.level == "WARNING"),
            "info": sum(1 for f in findings if f.level == "INFO"),
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def exit_code(findings: list[Finding]) -> int:
    """0 = clean, 1 = has errors, 2 = warnings only (info never affects the code)."""
    if any(f.level == "ERROR" for f in findings):
        return 1
    if any(f.level == "WARNING" for f in findings):
        return 2
    return 0
