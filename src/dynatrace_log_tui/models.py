"""
Data models and utilities for the Dynatrace Log TUI
"""
from datetime import datetime, timedelta, timezone
from typing import List, Tuple


class TimeRange:
    """Helper class for time range calculations"""
    
    @staticmethod
    def get_time_ranges() -> List[Tuple[str, str]]:
        """Return available time range options"""
        return [
            ("Last 30 minutes", "30m"),
            ("Last 60 minutes", "60m"), 
            ("Last 2 hours", "2h"),
            ("Last 6 hours", "6h"),
            ("Today", "today"),
            ("Yesterday", "yesterday"),
            ("Last 24 hours", "24h"),
            ("Last 7 days", "7d")
        ]
    
    @staticmethod
    def calculate_timeframe(time_range: str) -> Tuple[str, str]:
        """Calculate start and end times for the given range"""
        now = datetime.now(timezone.utc)
        
        if time_range == "30m":
            start = now - timedelta(minutes=30)
            end = now
        elif time_range == "60m":
            start = now - timedelta(minutes=60)
            end = now
        elif time_range == "2h":
            start = now - timedelta(hours=2)
            end = now
        elif time_range == "6h":
            start = now - timedelta(hours=6)
            end = now
        elif time_range == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif time_range == "yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == "24h":
            start = now - timedelta(hours=24)
            end = now
        elif time_range == "7d":
            start = now - timedelta(days=7)
            end = now
        else:
            # Default to last 30 minutes
            start = now - timedelta(minutes=30)
            end = now
        
        return start.isoformat(), end.isoformat()


class HistoryQuery:
    """Represents a query in the history"""
    
    def __init__(self, query: str, executed_at: str = None):
        self.query = query
        self.executed_at = executed_at or datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "executed_at": self.executed_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HistoryQuery':
        return cls(data["query"], data.get("executed_at", datetime.now().isoformat()))


class SavedQuery:
    """Represents a saved query"""
    
    def __init__(self, name: str, query: str):
        self.name = name
        self.query = query
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "query": self.query,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SavedQuery':
        query = cls(data["name"], data["query"])
        query.created_at = data.get("created_at", datetime.now().isoformat())
        return query