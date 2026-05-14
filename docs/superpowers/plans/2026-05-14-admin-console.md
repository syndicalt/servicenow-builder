# Admin Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only browser admin console at `/admin` in the existing FastAPI runtime.

**Architecture:** The console is server-rendered by `jedi_devproject.runtime` and reuses the existing runtime store. It has a separate Basic-auth credential pair for browser users while retaining bearer-token auth for JSON API clients.

**Tech Stack:** FastAPI, Pydantic runtime settings, PostgreSQL-backed runtime store, pytest, mypy, ruff.

---

### Task 1: Runtime Settings

**Files:**
- Modify: `src/jedi_devproject/runtime.py`
- Test: `tests/test_runtime.py`

- [ ] **Step 1: Write failing settings test**

Add a test that writes `JEDI_ADMIN_CONSOLE_USERNAME=admin` and `JEDI_ADMIN_CONSOLE_PASSWORD=secret` to an env file, calls `load_runtime_settings`, and asserts both values are loaded.

- [ ] **Step 2: Run the settings test**

Run: `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_reads_admin_console_credentials -q`

Expected: fail because `RuntimeSettings` has no console credential fields.

- [ ] **Step 3: Implement settings fields**

Add `admin_console_username: str | None = None` and `admin_console_password: str | None = None` to `RuntimeSettings`, then load them from the two environment variables.

- [ ] **Step 4: Re-run the settings test**

Run: `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_reads_admin_console_credentials -q`

Expected: pass.

### Task 2: Console Authentication And HTML

**Files:**
- Modify: `src/jedi_devproject/runtime.py`
- Test: `tests/test_runtime.py`

- [ ] **Step 1: Write failing route tests**

Add tests that assert `/admin` returns `503` when credentials are not configured, `401` without credentials, `401` for wrong Basic credentials, and `200 text/html` for correct credentials.

- [ ] **Step 2: Run the route tests**

Run: `python3 -m pytest tests/test_runtime.py::test_admin_console_requires_configured_credentials tests/test_runtime.py::test_admin_console_requires_basic_auth tests/test_runtime.py::test_admin_console_rejects_wrong_basic_auth tests/test_runtime.py::test_admin_console_renders_jobs_events_and_artifact_links -q`

Expected: fail because `/admin` does not exist.

- [ ] **Step 3: Implement route and helpers**

Add `GET /admin`, a Basic-auth validator using constant-time comparison, and a small HTML renderer. Escape all dynamic text with `html.escape`.

- [ ] **Step 4: Re-run the route tests**

Run the same route test command.

Expected: pass.

### Task 3: Documentation And Verification

**Files:**
- Modify: `docs/operator-guide.md`
- Create: `docs/sprints/sprint-101-change-log.md`

- [ ] **Step 1: Document `/admin`**

Add the console URL, env vars, and read-only limitation to the operator guide.

- [ ] **Step 2: Add sprint changelog**

Create a Sprint 101 changelog with goal, changes, tests, and deployment notes.

- [ ] **Step 3: Run full verification**

Run: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90`

Expected: lint passes, mypy passes, pytest passes, and coverage remains at least 90%.
