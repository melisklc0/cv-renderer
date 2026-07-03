from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from cv_renderer import loader

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


def _construct_mapping(loader_: _LineLoader, node: yaml.MappingNode) -> dict:
    loader_.flatten_mapping(node)
    mapping = dict(loader_.construct_pairs(node))
    mapping["__line__"] = node.start_mark.line + 1
    return mapping


_LineLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml_with_lines(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.load(f, Loader=_LineLoader)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(loader._user_data_root()))
    except ValueError:
        return path.name


# --- ERROR rules ---------------------------------------------------------------


def _check_tags(raw: dict, filename: str, vocab: set[str]) -> list[Finding]:
    findings: list[Finding] = []

    def check(tags, line, context):
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

    def check_bullet(bullet, context):
        tags = bullet.get("tags", [])
        line = bullet.get("__line__")
        check(tags, line, context)
        if tags == []:
            findings.append(
                Finding("ERROR", filename, line, "TAG-EMPTY", f"{context} has empty tags: []")
            )

    for job in raw.get("experience", []):
        company = job.get("company")
        check(job.get("tags", []), job.get("__line__"), f"experience[{company}]")
        for bullet in job.get("bullets", []):
            check_bullet(bullet, f"bullet in experience[{company}]")

    for edu in raw.get("education", []):
        check(edu.get("tags", []), edu.get("__line__"), f"education[{edu.get('institution')}]")

    for cat in raw.get("skills", []):
        category = cat.get("category")
        check(cat.get("tags", []), cat.get("__line__"), f"skill category '{category}'")
        items = cat.get("items")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    check(
                        item.get("tags", []),
                        item.get("__line__"),
                        f"skill item '{item.get('text')}' in '{category}'",
                    )

    for proj in raw.get("projects", []):
        name = proj.get("name")
        check(proj.get("tags", []), proj.get("__line__"), f"project '{name}'")
        for bullet in proj.get("bullets", []):
            check_bullet(bullet, f"bullet in project '{name}'")

    return findings


def _parse_date(value) -> tuple[int, int] | None:
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


def _check_date_order(raw: dict, filename: str) -> list[Finding]:
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


def _check_profile_focus_tags(raw_profile: dict, filename: str, vocab: set[str]) -> list[Finding]:
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
    raw_profile: dict, filename: str, companies: set[str], project_names: set[str]
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


# --- WARNING rules ---------------------------------------------------------------


def _check_spelling(raw_en_cv: dict, filename: str) -> list[Finding]:
    findings: list[Finding] = []

    def scan(text, line, context):
        if not isinstance(text, str):
            return
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

    about = raw_en_cv.get("about", {}) or {}
    about_line = about.get("__line__")
    for variant, text in about.items():
        if variant == "__line__":
            continue
        scan(text, about_line, f"about.{variant}")

    for job in raw_en_cv.get("experience", []):
        company = job.get("company")
        for variant, text in (job.get("title") or {}).items():
            if variant == "__line__":
                continue
            scan(text, job.get("__line__"), f"experience[{company}].title.{variant}")
        scan(job.get("description", ""), job.get("__line__"), f"experience[{company}].description")
        for bullet in job.get("bullets", []):
            scan(bullet.get("text", ""), bullet.get("__line__"), f"bullet in experience[{company}]")

    for proj in raw_en_cv.get("projects", []):
        name = proj.get("name")
        for bullet in proj.get("bullets", []):
            scan(bullet.get("text", ""), bullet.get("__line__"), f"bullet in project '{name}'")

    return findings


def _check_parity(raw_en: dict, raw_tr: dict, file_en: str, file_tr: str) -> list[Finding]:
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


# --- INFO rules ------------------------------------------------------------------


def _check_style(raw_cv: dict, filename: str, lang: str) -> list[Finding]:
    findings: list[Finding] = []
    pronoun_re = _PRONOUN_RE.get(lang, _PRONOUN_RE["en"])

    def scan_bullet(bullet, context):
        text = bullet.get("text", "") or ""
        line = bullet.get("__line__")
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

    for job in raw_cv.get("experience", []):
        for bullet in job.get("bullets", []):
            scan_bullet(bullet, f"bullet in experience[{job.get('company')}]")
    for proj in raw_cv.get("projects", []):
        for bullet in proj.get("bullets", []):
            scan_bullet(bullet, f"bullet in project '{proj.get('name')}'")

    return findings


# --- entrypoint ------------------------------------------------------------------


def lint(profile_name: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    vocab = set(loader.load_tags().keys())

    raw_by_lang: dict[str, tuple[dict, str]] = {}
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
