# -*- coding: utf-8 -*-
"""Resource hub models."""
import datetime as dt

from launchpad_os.database import Column, PkModel, db, reference_col, relationship

RESOURCE_CATEGORY_CHOICES = [
    ("internship", "Internships"),
    ("scholarship", "Scholarships"),
    ("research", "Research"),
    ("fellowship", "Fellowships & programs"),
]

RESOURCE_CATEGORY_LABELS = dict(RESOURCE_CATEGORY_CHOICES)


def utc_now():
    """Return the current timezone-aware UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


class ResourceSource(PkModel):
    """A user-saved resource source link in the hub."""

    __tablename__ = "resource_sources"
    name = Column(db.String(120), nullable=False)
    category = Column(db.String(30), nullable=False)
    url = Column(db.String(255), nullable=False)
    notes = Column(db.Text, nullable=True)
    user_id = reference_col("users", nullable=False)
    user = relationship("User", backref="resource_sources")
    created_at = Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<ResourceSource({self.name!r})>"

    @property
    def category_label(self):
        """Human-readable category label for templates."""
        return RESOURCE_CATEGORY_LABELS.get(self.category, self.category.title())
