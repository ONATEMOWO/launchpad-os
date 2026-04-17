# -*- coding: utf-8 -*-
"""Requirement checklist models."""
import datetime as dt

from launchpad_os.database import Column, PkModel, db, reference_col, relationship


def utc_now():
    """Return the current timezone-aware UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


class RequirementItem(PkModel):
    """A checklist item for an opportunity application."""

    __tablename__ = "requirement_items"
    title = Column(db.String(120), nullable=False)
    is_completed = Column(db.Boolean(), nullable=False, default=False)
    notes = Column(db.Text, nullable=True)
    opportunity_id = reference_col("opportunities", nullable=False)
    opportunity = relationship("Opportunity", backref="requirement_items")
    created_at = Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<RequirementItem({self.title!r})>"
