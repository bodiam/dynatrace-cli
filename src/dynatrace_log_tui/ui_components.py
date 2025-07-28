"""
Reusable UI components for the Dynatrace Log TUI
"""
from textual.widgets import DataTable, TextArea
from textual.binding import Binding
from typing import Dict, Any
from rich.text import Text
from rich.markup import escape


class LogTable(DataTable):
    """Custom DataTable for displaying log entries"""
    
    BINDINGS = [
        Binding("ctrl+o", "column_selection", "Columns"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
    
    def action_column_selection(self) -> None:
        self.app.action_column_selection()


class QueryTextArea(TextArea):
    """Custom TextArea for DQL query input"""
    
    BINDINGS = [
        Binding("ctrl+k", "clear_query", "Clear Query"),
        Binding("escape", "clear_query", "Clear Query"),
    ]
    
    def action_clear_query(self) -> None:
        self.text = ""
        self.app.action_clear_query()


class LogDetails(TextArea):
    """Custom TextArea for displaying detailed log information"""
    
    BINDINGS = [
        Binding("ctrl+o", "column_selection", "Columns"),
        Binding("]", "increase_details", "Details+"),
        Binding("[", "decrease_details", "Details-"),
        Binding("ctrl+0", "toggle_details", "Toggle Details"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.read_only = True
    
    def action_column_selection(self) -> None:
        self.app.action_column_selection()
    
    def action_increase_details(self) -> None:
        self.app.action_increase_details()
    
    def action_decrease_details(self) -> None:
        self.app.action_decrease_details()
    
    def action_toggle_details(self) -> None:
        self.app.action_toggle_details()


class LogTablePopulator:
    """Helper class for populating the log table with data"""
    
    @staticmethod
    def get_level_style(level: str) -> str:
        """Get the style for a log level"""
        styles = {
            "ERROR": "bold red",
            "WARN": "bold yellow", 
            "INFO": "bold blue",
            "DEBUG": "dim"
        }
        return styles.get(level, "")
    
    @staticmethod
    def populate_table(table: LogTable, logs: list, visible_columns: list) -> None:
        """Populate the table with log data"""
        table.clear()
        
        for log in logs:
            row_data = []
            for column in visible_columns:
                if column == "Timestamp":
                    # Timestamp is safe, no need to escape
                    row_data.append(log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"))
                elif column == "Level":
                    # Level uses Text with style, no markup parsing
                    level_style = LogTablePopulator.get_level_style(log["level"])
                    row_data.append(Text(log["level"], style=level_style))
                elif column == "Service":
                    # Escape service name to prevent markup interpretation
                    row_data.append(escape(str(log["service"])))
                elif column == "Message":
                    # Escape message content and truncate if needed
                    message = str(log["message"])
                    escaped_message = escape(message)
                    row_data.append(escaped_message[:50] + "..." if len(escaped_message) > 50 else escaped_message)
                elif column == "Host":
                    # Escape host name
                    row_data.append(escape(str(log["host"])))
                elif column == "Trace ID":
                    # Escape trace ID
                    row_data.append(escape(str(log["trace_id"])))
                elif column == "Span ID":
                    # Escape span ID
                    row_data.append(escape(str(log["span_id"])))
                elif column == "Content":
                    # Escape content and truncate if needed
                    content = str(log["content"])
                    escaped_content = escape(content)
                    row_data.append(escaped_content[:30] + "..." if len(escaped_content) > 30 else escaped_content)
            
            table.add_row(*row_data)
    
    @staticmethod
    def setup_table_columns(table: LogTable, visible_columns: list) -> None:
        """Setup table columns"""
        table.clear(columns=True)
        for column in visible_columns:
            table.add_column(column)
    
    @staticmethod
    def format_log_details(log: Dict[str, Any]) -> str:
        """Format log details for display"""
        # Escape all string content to prevent markup interpretation
        return f"""Timestamp: {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
Level: {escape(str(log['level']))}
Service: {escape(str(log['service']))}
Host: {escape(str(log['host']))}
Trace ID: {escape(str(log['trace_id']))}
Span ID: {escape(str(log['span_id']))}

Message:
{escape(str(log['message']))}

Content:
{escape(str(log['content']))}"""