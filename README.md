# LaunchPad OS

LaunchPad OS is a Flask-based student application workspace for tracking internships, scholarships, and research opportunities in one place. It combines opportunity tracking, reusable application materials, checklist management, and readiness guidance so a student can see what still needs work before submitting an application.

## Project Summary

LaunchPad OS was developed as a senior seminar project focused on practical student productivity. The app is intentionally server-rendered and lightweight so the codebase stays readable, easy to explain, and easy to evaluate in a class setting.

## Core Features

- Public landing pages, login, registration, and project overview
- Authenticated workspace dashboard with readiness and attention views
- Opportunity tracking with statuses, deadlines, archive/restore, and search/filter
- Quick Capture intake flow for saving rough opportunity information before refining it
- Requirement checklists tied to each opportunity
- Guided checklist templates for internships, scholarships, and research opportunities
- Materials Vault for resumes, essays, notes, recommendation notes, and related drafts
- Opportunity-to-material linking
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

### 6. Initialize the local database

This repo has Flask-Migrate configured, but it does not currently include a committed `migrations/` directory. For local development, the simplest setup is to create the tables directly:

```bash
flask shell
```

Then run:

```python
from launchpad_os.database import db
db.create_all()
exit()
```

If you want a fresh local database later, remove `/tmp/dev.db` and run `db.create_all()` again.

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

## Recommended Evaluation Flow

1. Create a user account or sign in.
2. Add an opportunity or use Quick Capture.
3. Open the opportunity detail page.
4. Add or generate checklist items.
5. Add materials and link them to the opportunity.
6. Review the workspace dashboard.
7. Export opportunities or materials as CSV from the list pages.

## CSV Export

LaunchPad OS supports authenticated CSV export for user-owned records:

- `GET /opportunities/export.csv`
- `GET /materials/export.csv`

Exports are scoped to the current authenticated user and do not include another user's data.

## Known Local Development Notes

- The default local database path is `/tmp/dev.db`.
- The app uses Bootstrap and webpack-managed assets.
- Flask-Static-Digest is part of the build process for production-style asset output.
- Tests create and drop an in-memory SQLite database automatically.
- The repository may show an existing `webob.compat` Python deprecation warning during tests on newer Python versions.

## Documentation

Additional project notes:

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

## AI / Open-Source Acknowledgement

This project builds on open-source tools including Flask, SQLAlchemy, Bootstrap, Font Awesome, webpack, and pytest. AI-assisted development support was used for planning, implementation guidance, debugging interpretation, and documentation drafting, with all code and written output reviewed before submission.
