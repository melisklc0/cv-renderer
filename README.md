# CV Renderer

All your CV content lives once in a YAML file. A profile defines what to show and what to emphasize. The render engine produces a clean HTML and optionally a print-ready PDF — one command per application.

---

## Setup

```bash
uv sync

# Playwright installs the Python package via uv sync,
# but the browser binary needs a separate one-time download:
uv run playwright install chromium

# Bootstrap your data directory from the example scaffold
uv run python render.py init
```

Then fill in `user-data/data/base_en.yaml` with your own content.

---

## Usage

```bash
uv run python render.py --profile ai-engineer
uv run python render.py --profile ai-engineer --export pdf
uv run python render.py --profile ai-engineer --lang tr
uv run python render.py --list
```

Output lands in `out/`.

---

## How it works

**`user-data/data/base_en.yaml`** — all your CV content in English, tagged per bullet:

```yaml
bullets:
  - text: "Shipped multi-agent HR analytics features using LangGraph..."
    tags: [ai, llm, backend]
  - text: "Modeled 56 mart tables through a 109-model dbt Core layer..."
    tags: [data]
```

**`user-data/profiles/ai-engineer.yaml`** — which tags to surface and which to suppress:

```yaml
focus_tags: [ai, llm, ml]
deprioritize_tags: [data]
max_bullets_per_job: 4
```

The render engine merges the two, feeds the result into a Jinja2 template, and produces the output. The visual design never changes — only the content does.

---

## Languages

The data directory holds one file per language: `base_en.yaml` for English, `base_tr.yaml` for Turkish. Both share the same structure — only the text differs. Tags, field names, and all structural keys stay in English across all files.

You can add any language by creating `base_<lang>.yaml` and selecting it in your profile (`lang: <lang>`) or at the CLI (`--lang <lang>`).

---

## Tag system

Tags connect bullets and skill categories to profiles. A bullet can carry multiple tags — a bullet covering both FastAPI and PostgreSQL is `[backend, data]`, not one or the other.

The list below is the default starting point. You can add your own tags by using them in `base_en.yaml` and referencing them in a profile's `focus_tags`.

| Tag | Covers |
|---|---|
| `ai` | LLM systems, agentic workflows, RAG, evaluation |
| `llm` | Prompt engineering, tool use, LLM-as-judge |
| `ml` | Training, distillation, PyTorch, model deployment |
| `data` | dbt, SQL, warehouse, BI dashboards, ETL/ELT |
| `backend` | FastAPI, API design, Redis |
| `devops` | Docker, CI/CD, OTEL |
| `always` | Appears in every profile regardless of focus |

---

## Profiles

| Profile | Purpose |
|---|---|
| `general` | Full CV, no filtering |
| `ai-engineer` | AI/LLM work foregrounded |
| `data-engineer` | dbt/SQL/pipeline work foregrounded |
| `companies/spotify` | Per-application, typically agent-generated |

---

## Agentic workflow

The profile schema is small and structured, so an agent can generate a company-specific profile directly from a job description. It reads `user-data/data/base_en.yaml` to see the available tags and bullets, then produces `user-data/profiles/companies/<company>.yaml`. You render it:

```bash
uv run python render.py --profile companies/spotify --export pdf
```

Writing rules for bullet generation and profile creation are in `AGENTS.md`.

---

## Structure

```
cv-renderer/
├── user-data/
│   ├── data/
│   │   ├── base_en.yaml   ← your CV content in English
│   │   ├── base_tr.yaml   ← same structure, Turkish text
│   │   └── base_<lang>.yaml  ← add more languages as needed
│   └── profiles/
├── templates/main.html.j2  ← Jinja2 template (visual design)
├── src/cv_renderer/        ← render engine
├── examples/               ← scaffold for init
├── docs/references/        ← Harvard OCS and XYZ writing guides
└── out/                    ← rendered outputs (gitignored)
```

# License
Apache 2.0