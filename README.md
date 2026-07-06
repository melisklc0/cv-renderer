# CV Renderer

> One YAML file. Multiple tailored CVs. One command per application.

[![CI](https://github.com/melisklc0/cv-renderer/actions/workflows/ci.yml/badge.svg)](https://github.com/melisklc0/cv-renderer/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=astral&logoColor=white)](https://github.com/astral-sh/uv)
[![Jinja2](https://img.shields.io/badge/templates-Jinja2-B41717?logo=jinja&logoColor=white)](https://jinja.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/PDF%20export-Playwright-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/)

All your CV content lives once in a YAML file. A **profile** defines what to show and what to emphasize for each application. The render engine produces a clean HTML and optionally a print-ready PDF — one command per role.


## Quickstart

```bash
uv sync

# One-time: download the Chromium binary for PDF export
uv run playwright install chromium

# Bootstrap your personal data directory
uv run python render.py init
```

Then fill in `user-data/data/base_en.yaml` with your own content.


## Usage

```bash
# Render to HTML
uv run python render.py --profile ai-engineer

# Render and export to PDF
uv run python render.py --profile ai-engineer --export pdf

# Render in Turkish
uv run python render.py --profile ai-engineer --lang tr

# List available profiles
uv run python render.py --list

# Validate your CV data before rendering — tag typos, EN/TR parity,
# wording issues, broken profile references
uv run python render.py --lint
uv run python render.py --lint --profile ai-engineer
```

Output lands in `out/`.


## How It Works

**Single source of truth** — `user-data/data/base_en.yaml` holds all your CV content, with every bullet tagged:

```yaml
bullets:
  - text: "Shipped multi-agent HR analytics features using LangGraph..."
    tags: [ai, llm, backend]
  - text: "Modeled 56 mart tables through a 109-model dbt Core layer..."
    tags: [data]
```

**Profiles** control what surfaces — `user-data/profiles/ai-engineer.yaml`:

```yaml
focus_tags: [ai, llm, ml]
deprioritize_tags: [data]
max_bullets_per_job: 4
```

The render engine merges the two, feeds the result into a Jinja2 template, and produces the output. The visual design never changes — only the content does.

A profile can also override the headline title and summary paragraph without touching the base data file — useful for a one-off application pitch that doesn't belong in the single source of truth:

```yaml
title_override: Veri Mühendisi
about_override: |
  A summary written for this specific application.
```

When omitted, the title/summary fall back to the `variant` lookup in `base_<lang>.yaml` as usual.

Tag filtering can only pick among bullets that already exist, and can only include or exclude a whole job/project by its tags — it can't reframe a real accomplishment around a different angle, and it can't partially include something whose tags don't match. `experience_overrides` / `project_overrides` replace one entry's bullets outright, keyed by `company` / project `name`:

```yaml
project_overrides:
  Agentic RAG:
    - "Isolated SQL access behind an MCP subprocess so agent code never touches database credentials directly."
```

An override also forces that job/project into the CV even if its tags would normally get it filtered out entirely — useful when a project's primary tag is `ai` but one real piece of it (e.g. a security boundary around a database) is genuinely relevant to a data-focused application. If nothing in an entry is honestly relevant, skip the override and let tag filtering drop it as usual — don't force it in.

`project_order` reorders the rendered projects by name, the same way `skill_categories` reorders skill categories — useful when the most relevant project for an application isn't the first one in the base data:

```yaml
project_order: [Analytics Copilot, Agentic RAG]
```

`skill_categories` can only select and reorder categories that already exist in the base data — it can't reshape them. `skill_overrides` regroups skill items into new, per-application category labels (e.g. splitting one base category into two), pulling item text from anywhere in the base data's skills regardless of original category, without touching the base file — so `general` and every other profile still see the base data's original grouping:

```yaml
skill_overrides:
  Data Warehousing: [Data Modeling, ETL/ELT, Data Profiling]
  Data Tools: [dbt Core, PostgreSQL, Apache Superset]
```

When set, `skill_overrides` replaces the skills section entirely — it ignores `skill_categories` and tag-based filtering.


## Tag System

The tag vocabulary lives in `user-data/tags.yaml` (falls back to `examples/tags.yaml` if you haven't created one), not hardcoded anywhere — `render.py --lint` validates every tag in your data and profiles against it:

| Tag | Covers |
|---|---|
| `ai` | LLM systems, agentic workflows, RAG, evaluation |
| `llm` | Prompt engineering, tool use, LLM-as-judge |
| `ml` | Training, distillation, PyTorch, model deployment |
| `data` | dbt, SQL, warehouse, BI dashboards, ETL/ELT |
| `backend` | FastAPI, API design, Redis |
| `devops` | Docker, CI/CD, OTEL |
| `always` | Appears in every profile regardless of focus |

Add a legitimate new tag by adding one line to `user-data/tags.yaml` — no code change needed, and `--lint` still catches genuine typos.

Tags are the only interface between data and profiles. A bullet that covers both FastAPI and PostgreSQL gets `[backend, data]`, not one or the other.

Skill categories can be filtered the same way at two levels — which categories show (`skill_categories` in the profile, or the category's own `tags`), and which items inside a shown category show:

```yaml
- category: AI and LLM Systems
  tags: [ai, llm]
  items:
    - text: LangChain
      tags: [ai]
    - text: Prompt Engineering
      tags: [ai, llm]
```

An item with no `tags` is generic and always shown once its category is included. An item whose tags are entirely inside `deprioritize_tags` is dropped; a category left with zero items after filtering is dropped too. The legacy shorthand — `items: "Python, FastAPI, ..."` — still works and treats every item as untagged.


## Profiles

The examples ship two archetypes and one sample company profile — add as many of each as you need:

| Profile | Purpose |
|---|---|
| `general` | Full CV, no filtering |
| `ai-engineer` | AI/LLM work foregrounded |
| `companies/spotify` | Per-application, typically agent-generated |


## Languages

The data directory holds one file per language: `base_en.yaml` for English, `base_tr.yaml` for Turkish. Both share the same structure — only the text differs. Tags, field names, and all structural keys stay in English across all files.

Add any language by creating `base_<lang>.yaml` and selecting it with `--lang <lang>`.


## Agentic Workflow

The profile schema is small and structured — an agent can generate a company-specific profile directly from a job description. It reads `user-data/data/base_en.yaml` to see the available tags and bullets, then produces `user-data/profiles/companies/<company>.yaml`. Lint it before rendering — it catches tag typos, wording mistakes, and broken references an agent can introduce:

```bash
uv run python render.py --lint --profile companies/spotify
uv run python render.py --profile companies/spotify --export pdf
```

Writing rules for bullet generation and profile creation are in [`AGENTS.md`](AGENTS.md).


## Project Structure

```
cv-renderer/
├── user-data/                    ← your personal data (gitignored)
│   ├── data/
│   │   ├── base_en.yaml          ← CV content in English
│   │   ├── base_tr.yaml          ← same structure, Turkish text
│   │   └── base_<lang>.yaml      ← add more languages as needed
│   └── profiles/
├── templates/main.html.j2        ← Jinja2 template (visual design only)
├── src/cv_renderer/              ← render engine (filter, loader, lint, render)
├── examples/                     ← scaffold used by `init`
├── docs/references/              ← Harvard OCS and XYZ writing guides
├── tests/                        ← pytest suite (runs against examples/, never user-data/)
└── out/                          ← rendered outputs (gitignored)
```


## Development

```bash
uv sync --dev

uv run ruff check .
uv run ruff format --check .
uv run mypy src/cv_renderer/
uv run pytest
```

CI runs all four on every push and pull request — see [`.github/workflows/ci.yml`](.github/workflows/ci.yml).


## License

[Apache 2.0](LICENSE)
