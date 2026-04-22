# Copilot Instructions

## Environment

- **Python 3.13**, virtualenv at `.venv/`
- Install dependencies: `source .venv/bin/activate && pip install -r requirements.txt`
- Run: `python main.py`
- Dependencies: `customtkinter`, `pyyaml`, `polib` (see `requirements.txt`)

## Architecture

A CustomTkinter desktop app for managing i18n localizations across multiple connected projects.

### Module layout

```
main.py                   Entry point — instantiates and runs App
app.py                    App(CTk) — root window, all app state, event wiring
models/
  project.py              Project, LocaleFile dataclasses
  locale_string.py        LocaleString(key, translations: dict[lang, value])
parsers/
  base.py                 BaseParser ABC + flatten()/unflatten() helpers
  json_parser.py          JSON ↔ flat dict
  yaml_parser.py          YAML ↔ flat dict
  properties_parser.py    .properties ↔ flat dict
  po_parser.py            .po (via polib) ↔ flat dict
services/
  project_scanner.py      Auto-detect locale files by heuristic in a directory
  project_store.py        Persist project list to ~/.localeinterface/projects.json
ui/
  toolbar.py              Top bar — Save, + Key, + Group, + Project, theme toggle
  sidebar.py              Left tree panel (projects → groups); SidebarNode tree
  editor_panel.py         Right table (key col + per-language entry cols)
  dialogs/
    connect_project.py    Folder picker + detected-files checklist
    add_key.py            Key path + per-language value inputs
    add_group.py          Group path input
utils/
  locale_detector.py      is_locale_code(), detect_language_from_filename()
  placeholder_utils.py    extract_placeholders(), validate_consistency()
```

### Data flow

1. **Load**: `project_scanner` finds locale files → each `Parser.load()` returns a flat `{dotted.key: value}` dict → `App._load_strings()` builds `list[LocaleString]` grouped by key, merging all language files.
2. **Edit**: UI entries call `App._on_string_changed(key, lang, value)` on every keystroke → updates `_all_strings` in-place.
3. **Save**: `App._save_strings()` → for each `LocaleFile`, filter strings by language → `Parser.save()` writes the full flat key set back (nested in the file).

### Key conventions

- **Flat key format**: all parsers normalise to/from `{"auth.login.title": "value"}` internally. Nesting is only in the serialised file.
- **Groups are virtual**: derived from key prefixes at render time — there is no separate group storage. `LocaleString.group` returns everything left of the last `.`.
- **Dynamic placeholders**: `{{variable}}` (double braces). `validate_consistency()` compares placeholder sets across non-empty translations for the same key and returns per-language warnings.
- **State lives in `App`**: `_all_strings: dict[project_name, list[LocaleString]]` is the single source of truth. UI components receive callbacks and never mutate state directly.
- **Save is explicit**: changes are held in memory. `Ctrl+S` or the Save button writes all locale files for the current project back in-place via each parser's `save()`.
- **Project persistence**: `~/.localeinterface/projects.json` stores connected project paths and their locale file metadata. Loaded on startup by `project_store.load_projects()`.
- **Sidebar re-renders fully** on every state change (expand/collapse, selection). Keep `_render()` and `_render_node()` lightweight — no I/O or heavy computation.

### Adding a new file format

1. Create `parsers/myformat_parser.py` subclassing `BaseParser` and implementing `load(path) -> dict` and `save(path, data)`.
2. Register the extension in `services/project_scanner.py` (`LOCALE_EXTENSIONS`) and in `app.py` (`_parser_for()`).

### Placeholder syntax

- Syntax: `{{variable_name}}` — double curly braces, snake_case name.
- Example: `"Welcome back, {{user_name}}! Your plan expires on {{expiry_date}}."`
- `validate_consistency()` returns `{"fi": ["Missing: {{user_name}}", "Extra: {{käyttäjä}}"]}` style diffs.

