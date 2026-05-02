# Prompt Lab — Development Log

Date: 2026-05-02

## Overview

Built a complete prompt management web application from scratch in a single session. The application supports CRUD operations, full-text search, template library, AI-powered optimization, and resource collection.

## Key Decisions

### Why Flask over FastAPI?
User has Flask already installed, and the app is primarily server-rendered HTML with HTMX. FastAPI's async advantage mainly matters for AI streaming endpoints, which Flask handles fine with generators and SSE.

### Why HTMX over React/Vue?
User is not a frontend specialist. HTMX requires zero build tooling — no npm, no webpack, no node_modules. Write HTML attributes, get interactivity.

### Why no OpenAI SDK?
Both Zhipu GLM and Xiaomi MIMO expose OpenAI-compatible HTTP endpoints. Using `httpx` directly means zero SDK version conflicts and easy support for any future provider by just entering a new base_url.

### Why SQLite FTS5?
Built into Python's sqlite3 module. Handles full-text search and ranking. For a single-user local app, eliminates the need for Elasticsearch or any external process.

### Why AI configs in SQLite (not just .env)?
The UI settings page lets users add multiple providers, change keys, toggle providers on/off. More flexible than editing .env and restarting.

## Implementation Phases

### Phase 1 — Skeleton
- Created project structure, config, Flask app factory
- Implemented all models (Prompt, Tag, Category, Resource, OptimizationLog, AIConfig)
- Built CRUD API for prompts with HTMX partial support
- Created base template with sidebar navigation (HTMX + Alpine.js + Tailwind CDN)
- Seeded default categories from JSON

**Key issue:** SQLite path was relative, causing `unable to open database file`. Fixed by making path absolute in config.py.

### Phase 2 — Core Features
- Tag and Category CRUD APIs
- FTS5 full-text search with LIKE fallback
- JSON and Markdown import/export

**Key issue:** FTS5 query via SQLAlchemy subquery failed (`rowid` not accessible). Fixed by using raw SQL for FTS5 queries.

### Phase 3 — Template Library
- Created Template model with many-to-many tag relationship
- Seeded 10 built-in templates covering general, coding, education, writing, analysis use cases
- Template browsing page with "Use Template" flow (creates new prompt from template)

**Key issue:** `get_json()` failed on HTMX POST without Content-Type. Fixed with `get_json(silent=True)`.

### Phase 4 — AI Integration
- Abstract AI provider layer (OpenAICompatibleProvider)
- PromptOptimizer with 5 optimization types (improve, simplify, rephrase, translate, expand)
- SSE streaming for real-time optimization output
- AI config CRUD and test connection endpoint
- Optimization workbench page with side-by-side comparison

### Phase 5 — Resource Collection
- Resource model with status workflow (pending_review → approved/rejected → imported)
- Resource CRUD, review, and import-as-prompt endpoints
- Resource collection page with modal form

### Phase 6 — Polish & Testing
- 35 tests covering models, API endpoints, and services
- All tests passing with `respx` mocking for AI API calls

## Test Results

```
35 passed, 1 warning in 32.80s
```

- Models: 9 tests (CRUD, relationships, constraints, cascade delete)
- API: 19 tests (prompts, tags, categories, search, export/import, HTMX)
- Services: 7 tests (AI provider, optimizer, streaming)

## Files Created

```
prompt-lab/
├── run.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models/ (6 files)
│   ├── api/ (7 files)
│   ├── services/ (3 files)
│   ├── pages/ (6 files)
│   ├── templates/ (10 HTML files)
│   └── static/css/custom.css
├── data/seed/ (2 JSON files)
├── tests/ (4 test files)
└── docs/dev-log.md
```

## Dependencies Added

```
flask-migrate, python-dotenv, flask-cors, beautifulsoup4, markdown,
pytest-flask, pytest-cov, respx
```

All other dependencies (flask, sqlalchemy, pydantic, httpx, jinja2, pytest) were already installed.

## UX Improvements (2026-05-02 continued)

### Problem
- Settings page could not add new API configs (form data not handled by API)
- No interaction feedback anywhere in the app — users had no idea if operations succeeded

### Changes

1. **Settings page rewrite**: Alpine.js form with connection testing before save. API `create_config` now handles both JSON and form data, tests connectivity before persisting.

2. **Global toast notification system**: Added to `base.html` — success/error/info/warning toasts with auto-dismiss. HTMX `afterRequest` event hook automatically shows feedback for all API operations.

3. **HX-Redirect toast persistence**: Since HX-Redirect causes full page navigation (wiping any toast), added `sessionStorage`-based toast persistence — toast message is saved before redirect and shown on the destination page.

4. **HTMX form pattern**: All create/update/delete endpoints return `HX-Redirect` header for proper page navigation after form submission. Templates: prompt form, detail page, resources list, import form.

5. **Fixed `export_import.py` bug**: `result[0].json` was wrong — `result` is a Response object, not a tuple. Fixed to `result.get_json()`.

### Key files modified
- `app/templates/base.html` — toast system + HTMX hooks
- `app/templates/settings.html` — Alpine.js form for AI providers
- `app/templates/resources/list.html` — modal form + HTMX integration
- `app/templates/resources/_resource_list.html` — HTMX partial (new)
- `app/api/ai.py` — `create_config` handles form data + connection test
- `app/api/resources.py` — form data support + HX-Redirect
- `app/api/export_import.py` — HTMX-friendly import responses + bug fix

## Bug Fixes Round 2 (2026-05-02 continued)

### Toast JS rendered as plain text
`x-init` attribute on `<body>` contained JS with `<i>` and `</span>` HTML tags. Browser HTML parser treated them as real DOM elements, breaking the JS and rendering it as visible text on the page.

**Fix:** Moved all JS from `x-init` attribute to `<script>` tag. Used `document.createElement` instead of innerHTML for toast elements.

### AI Optimization not working (3 root causes)
1. `max_tokens=2048` too small for reasoning models (MIMO) — reasoning tokens consume budget, leaving `content` empty
2. `chat_stream` yielded `None` values — `delta.get("content")` returns `None` for reasoning deltas, not missing key
3. SSE `event:` prefix non-standard for `fetch` ReadableStream

**Fix:**
- `max_tokens` default: 2048 → 8192
- `chat_stream`: `if "content" in delta` → `content = delta.get("content"); if content:`
- SSE: removed `event:` lines, added `Cache-Control: no-cache` + `X-Accel-Buffering: no` headers

### Search doesn't support Chinese
SQLite FTS5 default `unicode61` tokenizer splits on whitespace — Chinese has no spaces, so no tokens generated.

**Fix:** Recreated FTS5 table with `tokenize='trigram'` (requires SQLite ≥ 3.34). Trigram does character-level substring matching, works for any language. Short queries (<3 chars) fall back to LIKE.

### Optimize page doesn't load prompt content
Detail page linked to `/optimize?prompt_id=X` but the route and template ignored this parameter.

**Fix:** Route reads `prompt_id` from URL, passes Prompt to template. Template `init()` loads content via API + Jinja injection.

### Resources Collect button not working
`@click.away` (Alpine.js) fires immediately when modal transitions from hidden to visible — opens and closes in same frame.

**Fix:** Replaced with vanilla `onclick="if(event.target===this)"` on overlay div. API returns updated list partial instead of HX-Redirect for in-place updates.

## Current State (as of 2026-05-03)

### Working Features
- Prompt CRUD with tags, categories, ratings, notes
- Full-text search (FTS5 trigram + LIKE fallback, supports Chinese)
- Template library (10 built-in templates)
- AI optimization (5 modes, SSE streaming, works with MIMO reasoning model)
- Multi-model comparison
- Resource collection (collect → review → import workflow)
- Import/Export (JSON + Markdown)
- Global toast notifications
- Settings page with AI provider management and connection testing

### Known Limitations & Future Work
1. **AI Optimization**: Only 5 basic modes. Could add: custom system prompts, few-shot examples, chain-of-thought optimization, A/B testing with metrics
2. **Resource Collection**: Manual paste only. Could add: URL auto-fetch with BeautifulSoup, AI-powered summary and tag suggestion, batch import
3. **Search**: Trigram tokenizer doesn't rank by relevance well (no BM25). Could add: search history, saved searches, advanced filters UI
4. **UI/UX**: No drag-and-drop, no keyboard shortcuts, no dark mode, no mobile responsive layout, no prompt versioning
5. **Data**: No backup/restore, no prompt usage tracking, no prompt sharing/explore

### Architecture Notes
- Reasoning models (MIMO, DeepSeek R1): `reasoning_content` is separate from `content` in API response. Streaming yields both — need to filter for non-null `content` only
- HTMX pattern: use `HX-Redirect` for page navigation (create/delete), use partial returns for in-place updates (review, search)
- Toast system: `sessionStorage` bridge for cross-redirect feedback

### GitHub
Repository: https://github.com/ntbrq/prompt-lab
Branch: master
Tests: 35 passing
