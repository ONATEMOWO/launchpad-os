# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import Sequence, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from launchpad_os.database import db
from launchpad_os.opportunities.models import Opportunity
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
