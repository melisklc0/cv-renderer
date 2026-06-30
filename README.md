# CV Renderer

> One YAML file. Multiple tailored CVs. One command per application.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-orange)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

All your CV content lives once in a YAML file. A **profile** defines what to show and what to emphasize for each application. The render engine produces a clean HTML and optionally a print-ready PDF — one command per role.

---

## Quickstart

```bash
uv sync

# One-time: download the Chromium binary for PDF export
uv run playwright install chromium

# Bootstrap your personal data directory
uv run python render.py init
```

Then fill in `user-data/data/base_en.yaml` with your own content.

---

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
```

Output lands in `out/`.

---

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

---

## Tag System

| Tag | Covers |
|---|---|
| `ai` | LLM systems, agentic workflows, RAG, evaluation |
| `llm` | Prompt engineering, tool use, LLM-as-judge |
| `ml` | Training, distillation, PyTorch, model deployment |
| `data` | dbt, SQL, warehouse, BI dashboards, ETL/ELT |
| `backend` | FastAPI, API design, Redis |
| `devops` | Docker, CI/CD, OTEL |
| `always` | Appears in every profile regardless of focus |

Tags are the only interface between data and profiles. A bullet that covers both FastAPI and PostgreSQL gets `[backend, data]`, not one or the other.

---

## Profiles

| Profile | Purpose |
|---|---|
| `general` | Full CV, no filtering |
| `ai-engineer` | AI/LLM work foregrounded |
| `data-engineer` | dbt/SQL/pipeline work foregrounded |
| `companies/spotify` | Per-application, typically agent-generated |

---

## Languages

The data directory holds one file per language: `base_en.yaml` for English, `base_tr.yaml` for Turkish. Both share the same structure — only the text differs. Tags, field names, and all structural keys stay in English across all files.

Add any language by creating `base_<lang>.yaml` and selecting it with `--lang <lang>`.

---

## Agentic Workflow

The profile schema is small and structured — an agent can generate a company-specific profile directly from a job description. It reads `user-data/data/base_en.yaml` to see the available tags and bullets, then produces `user-data/profiles/companies/<company>.yaml`. You render it:

```bash
uv run python render.py --profile companies/spotify --export pdf
```

Writing rules for bullet generation and profile creation are in [`AGENTS.md`](AGENTS.md).

---

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
├── src/cv_renderer/              ← render engine
├── examples/                     ← scaffold used by `init`
├── docs/references/              ← Harvard OCS and XYZ writing guides
└── out/                          ← rendered outputs (gitignored)
```

---

## License

[Apache 2.0](LICENSE)
