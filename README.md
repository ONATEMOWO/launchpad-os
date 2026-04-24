# LaunchPad OS

LaunchPad OS is a Flask-based student application workspace for tracking internships, scholarships, and research opportunities in one place. It combines opportunity tracking, reusable application materials, checklist management, and readiness guidance so a student can see what still needs work before submitting an application.

## Project Summary

LaunchPad OS was developed as a senior seminar project focused on practical student productivity. The app is intentionally server-rendered and lightweight so the codebase stays readable, easy to explain, and easy to evaluate in a class setting.

## Core Features

- Public landing pages, login, registration, and project overview
- Authenticated workspace dashboard with readiness and attention views
- Opportunity tracking with statuses, deadlines, archive/restore, and search/filter
- Quick Capture intake flow for saving rough opportunity information before refining it
- Optional AI-assisted Quick Capture suggestions with deterministic fallback
- Browser-clipper-ready capture flow and a lightweight extension prototype
- Requirement checklists tied to each opportunity
- Guided checklist templates for internships, scholarships, and research opportunities
- Materials Vault for resumes, essays, notes, recommendation notes, and related drafts
- Opportunity-to-material linking
- Opportunity outreach tracking and in-app action digest panels
- Resource Hub for curated discovery sources and personal source links
- Opportunity tags and smart views for scaling to larger application sets
- Application Packet / Readiness summary on opportunity detail pages
- CSV export for user-owned opportunities and materials

## Technology Stack

- Python
- Flask
- Flask-Login
- Flask-WTF / WTForms
- SQLAlchemy
- SQLite for local development by default
- Bootstrap 5
- Jinja templates
- Webpack / npm for asset bundling
- pytest + WebTest for tests

## Local Setup

The recommended local workflow uses a Python virtual environment, npm for frontend assets, and the default SQLite development database.

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd launchpad_os
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements/dev.txt
```

### 4. Install frontend dependencies

```bash
npm install
```

### 5. Confirm local environment settings

This repo includes a development `.env` file with defaults such as:

- `FLASK_APP=autoapp.py`
- `FLASK_ENV=development`
- `DATABASE_URL=sqlite:////tmp/dev.db`

Optional AI-assisted intake can be configured with additional environment variables:

- `AI_INTAKE_ENDPOINT`
- `AI_INTAKE_API_KEY`
- `AI_INTAKE_MODEL`
- `AI_INTAKE_TIMEOUT`

If those values are not provided, LaunchPad OS automatically falls back to the normal Quick Capture review flow.

### 6. Initialize the local database

No manual setup is needed. The app calls `db.create_all()` automatically during startup, so all tables are created the first time the server runs. If you want a completely fresh local database, delete `/tmp/dev.db` and restart the server.

## Run the App Locally

For local evaluation, use port `5001`:

```bash
flask run --port 5001
```

Then open:

```text
http://127.0.0.1:5001
```

If you want the webpack watcher alongside Flask during active frontend work, you can also use:

```bash
npm start
```

## Running Tests

Run the full test suite:

```bash
.venv/bin/pytest
```

Or with the venv activated:

```bash
pytest
```

## Lint / Checks

Run the project lint/check command:

```bash
PATH=.venv/bin:$PATH .venv/bin/flask lint --check
```

Check patch formatting issues before commit:

```bash
git diff --check
```

## Building Assets

If you change CSS, JavaScript, or other frontend assets, rebuild them with:

```bash
PATH=.venv/bin:$PATH npm run build
```

If you only change Python files, templates, or docs, an asset rebuild is usually not needed.

## Optional AI-Assisted Intake

LaunchPad OS can optionally call an AI endpoint during Quick Capture to suggest:

- title
- organization
- category
- recognizable deadline text
- short summary
- starter checklist items

The user still reviews the prefilled form before saving. If AI is unavailable, unconfigured, or returns an error, the app keeps the normal deterministic Quick Capture behavior.

The implementation uses a configurable OpenAI-compatible chat-completions style endpoint and does not make the rest of the app depend on AI being available.

## Browser Clipper Prototype

The repository includes a lightweight browser clipper prototype in:

- `browser_extension/README.md`

The actual extension files live in `browser_extension/` and open LaunchPad OS Quick Capture with:

- page title
- page URL
- selected text when available

Quick Capture can also be prefilled directly with query parameters, for example:

```text
/opportunities/capture/?source=clipper&title=Example&url=https://example.com&selected_text=Important%20details
```

## Reminder / Digest Behavior

LaunchPad OS currently provides reminder support as an in-app action digest on the workspace dashboard. It highlights:

- overdue opportunities
- due soon opportunities
- high-priority low-readiness opportunities
- follow-up due opportunities
- opportunities missing checklist items
- opportunities missing linked materials

Email sending is not implemented in this repository. The current reminder path is intentionally in-app and demo-friendly.

## Scaling Support

For larger sets of opportunities, LaunchPad OS now supports:

- custom opportunity tags
- tag filtering
- smart views for urgent work, follow-up due, low readiness, missing materials, and missing checklist items

## Recommended Evaluation Flow

1. Create a user account or sign in.
2. Open the Resource Hub and try a capture-from-source shortcut.
3. Use Quick Capture with rough notes or a link.
4. Optionally test AI-assisted Quick Capture if configured.
5. Open the opportunity detail page.
6. Add or generate checklist items.
7. Add outreach details and linked materials.
8. Add tags and test smart views on the opportunities page.
9. Review the workspace dashboard and action digest.
10. Export opportunities or materials as CSV from the list pages.

## CSV Export

LaunchPad OS supports authenticated CSV export for user-owned records:

- `GET /opportunities/export.csv`
- `GET /materials/export.csv`

Exports are scoped to the current authenticated user and do not include another user's data.

## Deployment

LaunchPad OS is configured to deploy on Render. The app factory explicitly imports every model module and calls `db.create_all()` during startup, so all tables are created on first boot without any manual migration step. If tables already exist, `create_all()` skips them safely. No `flask db upgrade` or separate release command is required.

A startup log line confirms the initialization ran:

```
Startup: db.create_all() complete. Registered tables: [...]
```

This line is visible in Render's log output immediately after the worker starts.

### Required Render environment variables

| Variable | Value | Notes |
|---|---|---|
| `DATABASE_URL` | set by Render PostgreSQL add-on | required |
| `SECRET_KEY` | a long random string | required |
| `SEND_FILE_MAX_AGE_DEFAULT` | `31556926` | long cache for static assets |
| `FLASK_ENV` | `production` or leave unset | optional; does not control debug mode |

### Variables that must NOT be set on Render

| Variable | Why |
|---|---|
| `FLASK_DEBUG` | any truthy value (`1`, `true`) enables debug mode, which activates the Flask Debug Toolbar and exposes internals |

`DEBUG` defaults to `False` and is only `True` when `FLASK_DEBUG=1` is explicitly set. Do not set this variable on Render under any circumstances.

## Known Local Development Notes

- The default local database path is `/tmp/dev.db`.
- Tables are created automatically on startup; no manual `db.create_all()` step is needed.
- The app uses Bootstrap and webpack-managed assets.
- Flask-Static-Digest is part of the build process for production-style asset output.
- Tests create and drop an in-memory SQLite database automatically.
- The repository may show an existing `webob.compat` Python deprecation warning during tests on newer Python versions.

## Documentation

Additional project notes:

- [Assistive features](docs/assistive_features.md)
- [Local setup](docs/local_setup.md)
- [Testing notes](docs/testing.md)
- [Acknowledgements](docs/acknowledgements.md)
- [Screenshots folder](docs/screenshots)

## Screenshots

Add final screenshots to `docs/screenshots/` before submission. Suggested captures:

- Public landing page
- Workspace dashboard
- Opportunities list
- Opportunity detail / Application Packet
- Materials Vault
- Quick Capture flow
- Resource Hub
- Action digest and smart views

## AI / Open-Source Acknowledgement

This project builds on open-source tools including Flask, SQLAlchemy, Bootstrap, Font Awesome, webpack, and pytest. AI-assisted development support was used for planning, implementation guidance, debugging interpretation, and documentation drafting, with all code and written output reviewed before submission.
