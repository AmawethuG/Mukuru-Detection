"""
Import all models so Base.metadata is fully populated before create_all().
"""
from backend.models.user import User, UserSession  # noqa: F401
from backend.models.scan import ScanResult  # noqa: F401
from backend.models.transaction import Transaction  # noqa: F401
from backend.models.sms import SMSMessage  # noqa: F401
from backend.models.audit import AuditLog  # noqa: F401
