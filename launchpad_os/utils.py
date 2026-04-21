# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
import csv
import io

from flask import Response, flash


def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)


def csv_response(filename, headers, rows):
    """Build a CSV attachment response from headers and row values."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    csv_content = buffer.getvalue()
    buffer.close()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
