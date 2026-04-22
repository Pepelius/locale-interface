# LocaleInterface

A modern desktop GUI for managing i18n localization files across multiple projects.

![Python 3.13](https://img.shields.io/badge/python-3.13-blue)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-green)

## Features

- **Connect multiple projects** — point to any project folder and locale files are auto-detected
- **Supported formats** — JSON, YAML, `.properties`, `.po` (gettext)
- **Group tree** — keys organized into collapsible groups via dot-notation (e.g. `auth.login.title`)
- **Side-by-side editing** — all languages visible at once in a scrollable table
- **Dynamic placeholder validation** — `{{variable}}` syntax with live ⚠ warnings when translations are inconsistent
- **Dark / light theme** — toggle in the toolbar
- **In-place saving** — files are written back to their original location and format

## Requirements

- Python 3.13+
- pip

## Setup

```bash
# Clone or open the project folder, then:
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

Make sure the virtual environment is active before running:

```bash
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python main.py
```

Alternatively, run directly via the venv Python without activating:

```bash
.venv/bin/python main.py        # Windows: .venv\Scripts\python main.py
```

## Usage

### Connect a project

1. Click **+ Project** in the toolbar.
2. Select the root folder of your project.
3. The app scans for locale files automatically. Review and confirm the detected files.
4. Your project appears in the left sidebar.

### Browse and edit

- Expand a project in the sidebar to see its key groups.
- Click a group to load its strings in the editor panel.
- Click any cell to edit — changes are held in memory until you save.

### Add a key

1. Select a project in the sidebar.
2. Click **+ Key** in the toolbar.
3. Enter a dot-notation key path (e.g. `auth.login.button`) and values for each language.

### Add a group

1. Select a project.
2. Click **+ Group** and enter a dot-notation prefix (e.g. `onboarding.step1`).
   The group appears in the sidebar ready for keys to be added under it.

### Save

Press **Ctrl+S** or click **Save** in the toolbar. All locale files for the current project are written back in-place.

## Placeholder syntax

Use `{{variable_name}}` (double curly braces) to embed dynamic values in translations:

```json
{
  "welcome.message": "Hello, {{user_name}}! You have {{count}} unread messages."
}
```

If a placeholder exists in one language but is missing or renamed in another, the editor shows a ⚠ warning on that row.

## Project structure

```
main.py             Entry point
app.py              Root window and application controller
models/             Data models (Project, LocaleFile, LocaleString)
parsers/            Format-specific file parsers
services/           File scanner and project persistence
ui/                 All UI components and dialogs
utils/              Locale detection and placeholder utilities
```

## Data storage

Connected projects are persisted to `~/.localeinterface/projects.json`. No localization file content is stored outside the original project files.
