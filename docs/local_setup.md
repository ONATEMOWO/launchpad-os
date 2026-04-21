# Local Setup

## Recommended Local Workflow

LaunchPad OS runs locally with Python, a virtual environment, npm-managed frontend assets, and the default SQLite development database.

## Steps

```bash
cd launchpad_os
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
npm install
```

## Database Initialization

This repository has Flask-Migrate configured, but it does not currently include a committed `migrations/` directory. For local development, initialize the database tables directly:

```bash
flask shell
```

Then run:

```python
from launchpad_os.database import db
db.create_all()
exit()
```

The default local SQLite database path from `.env` is:

```text
/tmp/dev.db
```

If you need a clean local reset, remove `/tmp/dev.db` and run `db.create_all()` again.

## Running the App

Use the recommended local port `5001`:

```bash
flask run --port 5001
```

Open:

```text
http://127.0.0.1:5001
```

## Frontend Assets

If you change CSS or JavaScript, rebuild the bundled assets:

```bash
PATH=.venv/bin:$PATH npm run build
```

For active frontend work, `npm start` runs Flask and the webpack watcher together.
