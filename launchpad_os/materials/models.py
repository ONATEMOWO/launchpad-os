# -*- coding: utf-8 -*-
"""Material models."""
import datetime as dt

from launchpad_os.database import Column, PkModel, db, reference_col, relationship

MATERIAL_TYPE_CHOICES = [
    ("resume", "Resume"),
    ("cover_letter", "Cover letter"),
    ("essay", "Essay"),
    ("recommendation", "Recommendation"),
    ("transcript", "Transcript"),
    ("note", "Note"),
]


def utc_now():
    """Return the current timezone-aware UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


class Material(PkModel):
    """A reusable application material owned by a user."""

    __tablename__ = "materials"
    title = Column(db.String(120), nullable=False)
    material_type = Column(db.String(40), nullable=False)
    content = Column(db.Text, nullable=False)
    link = Column(db.String(255), nullable=True)
    notes = Column(db.Text, nullable=True)
    user_id = reference_col("users", nullable=False)
    user = relationship("User", backref="materials")
    created_at = Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Material({self.title!r})>"
