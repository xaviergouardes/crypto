from datetime import datetime
from zoneinfo import ZoneInfo


class TimestampHelper:
    """Convertit timestamps en datetime UTC."""

    @staticmethod
    def to_utc(ts):
        if isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=ZoneInfo("UTC"))
        return datetime.fromisoformat(str(ts)).replace(tzinfo=ZoneInfo("UTC"))