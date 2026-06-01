import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    SALES = "SALES"


class LeadStatus(str, enum.Enum):
    NEW = "NEW"
    ENRICHED = "ENRICHED"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    CONVERTED = "CONVERTED"
