<p align="center">
  <img src="app/static/img/logo.svg" width="120" alt="Prompt Lab Logo">
</p>

<h1 align="center">Prompt Lab</h1>

<p align="center">
  <strong>Local-first prompt management for AI power users</strong>
</p>

<p align="center">
  Store · Search · Optimize · Reuse
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/flask-3.x-green" alt="Flask 3.x">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT License">
  <img src="https://img.shields.io/badge/tests-35%20passed-brightgreen" alt="Tests">
</p>

---

## Why Prompt Lab?

You've accumulated hundreds of great prompts across different AI platforms — Zhipu GLM, Xiaomi MIMO, ChatGPT, Claude — but they're scattered in chat histories, never to be found again. Prompt Lab is a **local web app** that keeps all your prompts in one place, makes them searchable, and helps you improve them with AI.

## Features

| Feature | Description |
|---------|-------------|
| **Prompt CRUD** | Create, edit, delete prompts with tags, categories, ratings, and notes |
| **Full-text Search** | SQLite FTS5 powered — instant search across all content |
| **Template Library** | 10 built-in templates for common tasks (coding, writing, education, analysis) |
| **AI Optimization** | 5 modes: improve, simplify, rephrase, translate, expand — with SSE streaming output |
| **Multi-model Testing** | Run the same prompt against multiple providers side by side |
| **Resource Collection** | Save prompt resources from the web → human review → import as prompt |
| **Import/Export** | JSON and Markdown formats for backup and sharing |
| **Toast Notifications** | Every operation gives clear feedback — no more guessing if it worked |

## Quick Start

```bash
# Clone
git clone https://github.com/your-username/prompt-lab.git
cd prompt-lab

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env → add your AI provider API keys (optional)

# Run
python run.py
```

Open **http://localhost:5000** in your browser.

## Tech Stack

```
Backend:   Flask + SQLAlchemy + Pydantic
Frontend:  HTMX + Alpine.js + Tailwind CSS (CDN, zero build step)
Database:  SQLite + FTS5 full-text search
AI:        httpx → OpenAI-compatible APIs (Zhipu, MIMO, custom)
Testing:   pytest + respx
```

No npm, no webpack, no node_modules. Just Python.

## AI Providers

Works with any OpenAI-compatible API. Add providers in the **Settings page** — the app tests connectivity before saving.

| Provider | Base URL |
|----------|----------|
| Zhipu GLM | `https://open.bigmodel.cn/api/paas/v4/` |
| Xiaomi MIMO | `https://api.mimo.xiaomi.com/v1` |
| Custom | Any OpenAI-compatible endpoint |

## Screenshots

> Add screenshots here after running the app locally.

## Project Structure

```
prompt-lab/
├── run.py                    # Entry point
├── config.py                 # Configuration
├── app/
│   ├── __init__.py           # App factory + FTS5 triggers
│   ├── extensions.py         # SQLAlchemy instance
│   ├── models/               # Prompt, Tag, Category, Resource, AIConfig, Template
│   ├── api/                  # REST endpoints (prompts, search, tags, ai, resources, export)
│   ├── services/             # AI provider, optimizer, search service
│   ├── pages/                # HTML page routes
│   └── templates/            # Jinja2 templates (base + pages)
├── data/seed/                # Built-in templates and categories
├── tests/                    # 35 tests — models, API, services
└── docs/                     # Dev log, API docs
```

## Testing

```bash
pytest tests/ -v
```

```
35 passed in 24.66s
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/prompts` | List / Create prompts |
| GET/PUT/DELETE | `/api/prompts/<id>` | Get / Update / Delete prompt |
| POST | `/api/prompts/<id>/favorite` | Toggle favorite |
| GET | `/api/search?q=` | Full-text search |
| GET/POST | `/api/tags` | List / Create tags |
| GET/POST | `/api/categories` | List / Create categories |
| GET | `/api/templates` | List templates |
| POST | `/api/templates/<id>/use` | Create prompt from template |
| POST | `/api/ai/optimize` | Optimize prompt (SSE stream) |
| POST | `/api/ai/compare` | Multi-model comparison |
| POST | `/api/resources` | Collect resource |
| PUT | `/api/resources/<id>/review` | Approve / Reject resource |
| POST | `/api/resources/<id>/import` | Import resource as prompt |
| GET | `/api/export?format=json\|markdown` | Export prompts |
| POST | `/api/import` | Import from file |

## License

MIT
