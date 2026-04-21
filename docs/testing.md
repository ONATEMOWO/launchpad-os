# Testing

## Full Test Suite

Run the full automated test suite with:

```bash
.venv/bin/pytest
```

Or, with the virtual environment activated:

```bash
pytest
```

## Lint / CI-Style Check

Run the Flask lint check without auto-fixing:

```bash
PATH=.venv/bin:$PATH .venv/bin/flask lint --check
```

## Patch / Whitespace Check

Before commit, check for patch formatting issues:

```bash
git diff --check
```

## Notes

- Tests use the `tests.settings` configuration.
- The test suite creates and drops SQLite tables automatically.
- You do not need to initialize `/tmp/dev.db` to run tests.
- On newer Python versions, you may see an existing `webob.compat` deprecation warning during test runs.
