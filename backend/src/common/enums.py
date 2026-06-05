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


class LeadSource(str, enum.Enum):
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    DISCOVERY = "DISCOVERY"
    SEARCH = "SEARCH"


class CrawlRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EmailVerificationStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    VALID_FORMAT = "VALID_FORMAT"
    MX_FOUND = "MX_FOUND"
    INVALID = "INVALID"


class PhoneVerificationStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    VALID_FORMAT = "VALID_FORMAT"
    INVALID = "INVALID"


class IntentSignalType(str, enum.Enum):
    HIRING = "HIRING"
    EXPANSION = "EXPANSION"
    FUNDING = "FUNDING"
    OTHER = "OTHER"


class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


class CampaignChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    LINKEDIN = "LINKEDIN"
    WHATSAPP = "WHATSAPP"


class CampaignLeadStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    REPLIED = "REPLIED"
    CONVERTED = "CONVERTED"


class MessageChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    LINKEDIN = "LINKEDIN"
    WHATSAPP = "WHATSAPP"
