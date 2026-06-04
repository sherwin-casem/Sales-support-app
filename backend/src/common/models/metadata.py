"""Import all ORM models so Alembic autogenerate sees full metadata."""

from src.common.models.base import Base
from src.auth.models import RefreshToken  # noqa: F401
from src.leads.models import DecisionMaker, Lead  # noqa: F401
from src.users.models import User  # noqa: F401

target_metadata = Base.metadata
