"""
Query and history management for the Dynatrace Log TUI
"""
import json
import os
from typing import List
from datetime import datetime

from .models import SavedQuery, HistoryQuery


class QueryManager:
    """Manager for saved queries"""
    
    def __init__(self, filename: str = "saved_queries.json"):
        self.filename = filename
        self.queries = self.load_queries()
    
    def load_queries(self) -> List[SavedQuery]:
        """Load saved queries from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    return [SavedQuery.from_dict(q) for q in data]
            except:
                return []
        return []
    
    def save_queries(self) -> None:
        """Save queries to file"""
        with open(self.filename, 'w') as f:
            json.dump([q.to_dict() for q in self.queries], f, indent=2)
    
    def add_query(self, name: str, query: str) -> bool:
        """Add a new query"""
        if query.strip() and not any(q.name == name for q in self.queries):
            self.queries.insert(0, SavedQuery(name, query))
            self.save_queries()
            return True
        return False
    
    def delete_query(self, name: str) -> None:
        """Delete a query by name"""
        self.queries = [q for q in self.queries if q.name != name]
        self.save_queries()
    
    def get_query(self, name: str) -> SavedQuery:
        """Get a query by name"""
        for q in self.queries:
            if q.name == name:
                return q
        return None
    
    def update_query(self, name: str, new_query: str) -> bool:
        """Update an existing query"""
        for q in self.queries:
            if q.name == name:
                q.query = new_query
                self.save_queries()
                return True
        return False


class QueryHistory:
    """Manager for query history"""
    
    def __init__(self, filename: str = "query_history.json"):
        self.filename = filename
        self.history = self.load_history()
    
    def load_history(self) -> List[HistoryQuery]:
        """Load history from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    return [HistoryQuery.from_dict(q) for q in data]
            except:
                return []
        return []
    
    def save_history(self) -> None:
        """Save history to file"""
        with open(self.filename, 'w') as f:
            json.dump([q.to_dict() for q in self.history], f, indent=2)
    
    def add_query(self, query: str) -> None:
        """Add a query to history"""
        # Clean the query (remove comments and empty lines)
        query_lines = [line for line in query.split('\n') if line.strip() and not line.strip().startswith('#')]
        clean_query = '\n'.join(query_lines).strip()
        
        if clean_query:
            # Remove if already exists to avoid duplicates
            self.history = [q for q in self.history if q.query != clean_query]
            # Add to front
            self.history.insert(0, HistoryQuery(clean_query))
            # Keep only last 50 queries
            self.history = self.history[:50]
            self.save_history()
    
    def get_recent_queries(self, limit: int = 20) -> List[HistoryQuery]:
        """Get recent queries"""
        return self.history[:limit]
    
    def clear_entry(self, index: int) -> bool:
        """Remove a specific query from history by index"""
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self.save_history()
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all query history"""
        self.history = []
        self.save_history()


class QueryProcessor:
    """Utility class for processing queries"""
    
    @staticmethod
    def clean_query(query: str) -> str:
        """Clean query by removing comments and empty lines"""
        query_lines = [line for line in query.split('\n') if line.strip() and not line.strip().startswith('#')]
        return '\n'.join(query_lines).strip()
    
    @staticmethod
    def has_actual_query(query: str) -> bool:
        """Check if query contains actual content (not just comments)"""
        return bool(QueryProcessor.clean_query(query))