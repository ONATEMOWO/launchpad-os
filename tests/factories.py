# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import Sequence, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from launchpad_os.database import db
from launchpad_os.materials.models import Material
from launchpad_os.opportunities.models import (
    Opportunity,
    OpportunityOutreach,
    OpportunityTag,
)
from launchpad_os.requirements.models import RequirementItem
from launchpad_os.resources.models import ResourceSource
from launchpad_os.user.models import User


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""

        abstract = True
        sqlalchemy_session = db.session


class UserFactory(BaseFactory):
    """User factory."""

    username = Sequence(lambda n: f"user{n}")
    email = Sequence(lambda n: f"user{n}@example.com")
    active = True

    class Meta:
        """Factory configuration."""

        model = User


class OpportunityFactory(BaseFactory):
    """Opportunity factory."""

    user = SubFactory(UserFactory)
    title = Sequence(lambda n: f"Opportunity {n}")
    organization = Sequence(lambda n: f"Organization {n}")
    category = "internship"
    status = "saved"
    priority = "medium"

    class Meta:
        """Factory configuration."""

        model = Opportunity


class MaterialFactory(BaseFactory):
    """Material factory."""

    user = SubFactory(UserFactory)
    title = Sequence(lambda n: f"Material {n}")
    material_type = "resume"
    content = "Reusable application content."
    link = None
    notes = None

    class Meta:
        """Factory configuration."""

        model = Material


class OpportunityOutreachFactory(BaseFactory):
    """Opportunity outreach factory."""

    opportunity = SubFactory(OpportunityFactory)
    contact_name = "Career Office"
    contact_role = "Coordinator"
    contact_method = "advisor@example.com"
    outreach_notes = "Sent initial question."
    outreach_status = "contacted"

    class Meta:
        """Factory configuration."""

        model = OpportunityOutreach


class OpportunityTagFactory(BaseFactory):
    """Opportunity tag factory."""

    user = SubFactory(UserFactory)
    name = Sequence(lambda n: f"tag-{n}")

    class Meta:
        """Factory configuration."""

        model = OpportunityTag


class ResourceSourceFactory(BaseFactory):
    """Resource source factory."""

    user = SubFactory(UserFactory)
    name = Sequence(lambda n: f"Resource Source {n}")
    category = "research"
    url = Sequence(lambda n: f"https://example.com/source-{n}")
    notes = "Useful page for new opportunities."

    class Meta:
        """Factory configuration."""

        model = ResourceSource


class RequirementItemFactory(BaseFactory):
    """Requirement item factory."""

    opportunity = SubFactory(OpportunityFactory)
    title = Sequence(lambda n: f"Requirement {n}")
    is_completed = False
    notes = None

    class Meta:
        """Factory configuration."""

        model = RequirementItem
