# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Run the app (venv python directly — avoids needing shell activation to persist)
.venv\Scripts\python.exe main.py

# Install/update dependencies
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

There is no test suite, linter, or build step in this repo. Verification is done by launching the app and exercising the relevant tab.

Python 3.11 in `.venv`. The app is a Tkinter desktop GUI — launching it opens a window and blocks until closed, so run it in the background or with a timeout rather than waiting on it.

## Data safety

`budget_tracker.db` is the user's real financial data and is gitignored. Never delete, recreate, or run destructive migrations against it. To test schema changes, point `DatabaseManager(db_path=...)` at a throwaway file.

Note: `budget_tracker.db.bak` is **tracked in git** — `.gitignore` covers `budget_tracker.db` and `budget_tracker_old.db`, neither of which matches the `.bak` suffix.

## Architecture

### Money is stored as integer cents

Every monetary value in SQLite (`transactions.amount`, `net_worth_entries.value`, `budget_targets.monthly_target`) is an **integer number of cents**. Conversion happens at the boundaries only:

- **In**: `int(Decimal(value) * 100)` — see `utils/csv_importer.py:196`
- **Out**: `Decimal(amount) / 100` for display and charts

Use `Decimal`, never `float`, for the arithmetic in between. This is the single most common source of bugs — a change that mixes units silently produces values off by 100x.

Sign convention: positive amount = income, negative = expense. `transaction_type` is derived from the sign, not entered independently. Net worth liabilities are stored as **negative** `value`s, so a plain `SUM(value)` is already net worth. Consumers that want a positive liability magnitude take `abs()` locally and then subtract (see `gui/reports_tab.py:361-366`) — don't assume `total_liabilities` in a given function is negative.

### Path resolution

All project-relative file access goes through `utils/paths.py` (`project_path(...)`), which anchors to the repo root via `__file__`. Do not introduce cwd-relative paths like `'assets/foo.png'` — the app must launch from any working directory. The `.tcl` theme path is passed as `.as_posix()` because Tcl treats backslashes as escapes.

### Layered structure

```
main.py           → Tk root, ttk style definitions, theme load
gui/main_window.py→ notebook + the five tabs, owns the single DatabaseManager
gui/*_tab.py      → one ttk.Frame subclass per tab
database/         → DatabaseManager: SQL layer, no UI
utils/            → dialogs, CSV in/out, shared widgets, helpers
```

One `DatabaseManager` instance is created in `MainWindow.__init__` and passed by reference into every tab and dialog. Tabs never construct their own. `DatabaseManager` opens a fresh connection per call via `get_connection()` (with `PRAGMA foreign_keys = ON`) and closes it — there is no long-lived connection or ORM.

Query logic mostly stays in `database/`, but the separation isn't absolute — `gui/net_worth_tab.py:264` calls `get_connection()` and runs raw SQL in the GUI layer. Prefer adding a `DatabaseManager` method over following that precedent.

All styling lives in `main.py` as named ttk styles (`Big.TButton`, `Count.TLabel`, `Centered.TNotebook`, …). Color palettes are dicts in `utils/helpers.py` (`VIS_CLRS`, `REPORT_CLRS`, `DP_COLORS`, `BDGT_CLRS`) — add colors there, not inline.

### Tab refresh protocol

Tabs are stale by default; they only reload data when shown. `MainWindow.setup_ui` binds `<<NotebookTabChanged>>` to a handler that calls `on_tab_opened()` on the newly selected tab **if that method exists**. Any new tab that displays DB-backed data must implement `on_tab_opened()` or it will show stale rows.

Separately, `MainWindow.refresh_dependent_tabs()` is the explicit path for changes that cross tab boundaries (e.g. editing categories in Settings). Dialogs receive `main_window=self` so they can call it.

### EditableTree

`utils/editable_tree.py` is a `ttk.Treeview` subclass used for the in-place-editable tables throughout the app. It's driven by callbacks passed at construction:

- `editable_columns` — column names that respond to double-click
- `get_options_callback(col)` — return a list to get a Combobox, `None` for an Entry
- `get_validation_callback(col)` — return `(func, allow_negative, allow_decimal)`; wired to `validate_money_string` in `utils/helpers.py` for money columns
- `on_commit_callback(row_id, col_name, new_value)` — receives the **string** value; the caller is responsible for parsing, unit conversion, DB write, and refresh

Combobox commit logic deliberately inspects Tcl focus (`popdown` check) to avoid saving while the dropdown is open — be careful editing that.

### CSV import pipeline

`utils/csv_importer.py`, in order: parse rows using the import template's column mapping (or auto-detected headers) → optionally invert signs → apply `description_rules` in `rule_order` (first regex match wins; a rule can rewrite the description, force a category, or drop the row via `ignore`) → fall back to keyword auto-categorization (`categories.keywords`, comma-separated, most-matches-wins) → insert.

Import templates live in `import_templates` + `description_rules` and are edited in `utils/import_template_manager.py`. A template with `id=None` means "auto-detected, not saved" and therefore has no description rules.

### Reports vs Visualizations

Both read the same data but render differently. `gui/visualizations_tab.py` embeds matplotlib figures directly in Tk. `gui/reports_tab.py` builds an **HTML string** with inline styles from `REPORT_CLRS`, embeds charts as base64 data URLs, and renders it via `tkinterweb`. Changing report appearance means editing HTML generation, not ttk styles.

### Schema migrations

`init_database()` runs on every startup and is idempotent (`CREATE TABLE IF NOT EXISTS`). Column additions are done as a bare `ALTER TABLE` wrapped in `try/except sqlite3.OperationalError` (see the `invert_amounts` migration) — follow that pattern for new columns so existing databases upgrade in place.
