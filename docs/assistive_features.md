# Assistive Features

LaunchPad OS includes several assistive layers on top of its core tracking workflow.

## AI-Assisted Intake

Quick Capture can optionally request AI suggestions for:

- title
- organization
- category
- deadline text
- short summary
- starter checklist items

The user still reviews and edits the prefilled form before saving. If AI is not configured or the request fails, the app falls back to deterministic Quick Capture behavior automatically.

## Browser-Clipper-Ready Capture

Quick Capture accepts prefilled values through query parameters, including:

- `title`
- `url` or `link`
- `selected_text`
- `details`
- `notes`

The repository also includes a lightweight prototype extension in `browser_extension/`.

## In-App Reminder Digest

The workspace dashboard surfaces:

- overdue opportunities
- due soon opportunities
- high-priority low-readiness opportunities
- follow-up due opportunities
- opportunities missing checklist items
- opportunities missing linked materials

This is currently implemented as an in-app digest. Email delivery is not part of this repository.

## Scaling Support

Opportunity organization now includes:

- custom tags
- tag filtering
- smart views for urgent work, follow-up due, low readiness, missing materials, and missing checklist items

## Discovery Support

The Resource Hub includes:

- curated discovery sources
- personal saved sources
- capture-from-source shortcuts into Quick Capture
