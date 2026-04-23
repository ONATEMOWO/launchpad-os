# -*- coding: utf-8 -*-
"""Opportunity models."""
import datetime as dt

from launchpad_os.database import Column, PkModel, db, reference_col, relationship

CATEGORY_CHOICES = [
    ("internship", "Internship"),
    ("scholarship", "Scholarship"),
    ("research", "Research"),
]

STATUS_CHOICES = [
    ("saved", "Saved"),
    ("planning", "Preparing"),
    ("in progress", "In Progress"),
    ("submitted", "Submitted"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
    ("archived", "Archived"),
]

STATUS_LABELS = dict(STATUS_CHOICES)

PRIORITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

OUTREACH_STATUS_CHOICES = [
    ("not contacted", "Not Contacted"),
    ("contacted", "Contacted"),
    ("replied", "Replied"),
    ("follow-up due", "Follow-up Due"),
]

OUTREACH_STATUS_LABELS = dict(OUTREACH_STATUS_CHOICES)

opportunity_materials = db.Table(
    "opportunity_materials",
    Column(
        "opportunity_id",
        db.Integer,
        db.ForeignKey("opportunities.id"),
        primary_key=True,
    ),
    Column(
        "material_id",
        db.Integer,
        db.ForeignKey("materials.id"),
        primary_key=True,
    ),
)


def utc_now():
    """Return the current timezone-aware UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


class Opportunity(PkModel):
    """An internship, scholarship, or research opportunity for a user."""

    __tablename__ = "opportunities"
    title = Column(db.String(120), nullable=False)
    organization = Column(db.String(120), nullable=False)
    category = Column(db.String(30), nullable=False)
    deadline = Column(db.Date, nullable=True)
    status = Column(db.String(30), nullable=False, default="saved")
    priority = Column(db.String(20), nullable=False, default="medium")
    link = Column(db.String(255), nullable=True)
    notes = Column(db.Text, nullable=True)
    user_id = reference_col("users", nullable=False)
    user = relationship("User", backref="opportunities")
    materials = relationship(
        "Material", secondary=opportunity_materials, backref="opportunities"
    )
    created_at = Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Opportunity({self.title!r})>"

    @property
    def status_label(self):
        """Human-readable status label for templates."""
        return STATUS_LABELS.get(self.status, self.status.title())


class OpportunityOutreach(PkModel):
    """Lightweight contact and outreach tracking for an opportunity."""

    __tablename__ = "opportunity_outreach"
    contact_name = Column(db.String(120), nullable=True)
    contact_role = Column(db.String(120), nullable=True)
    contact_method = Column(db.String(255), nullable=True)
    outreach_notes = Column(db.Text, nullable=True)
    outreach_status = Column(
        db.String(30),
        nullable=False,
        default="not contacted",
        server_default="not contacted",
    )
    opportunity_id = reference_col(
        "opportunities",
        nullable=False,
        column_kwargs={"unique": True},
    )
    opportunity = relationship(
        "Opportunity",
        backref=db.backref("outreach", uselist=False, cascade="all, delete-orphan"),
    )
    created_at = Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<OpportunityOutreach({self.outreach_status!r})>"

    @property
    def outreach_status_label(self):
        """Human-readable outreach status label for templates."""
        return OUTREACH_STATUS_LABELS.get(
            self.outreach_status, self.outreach_status.title()
        )
