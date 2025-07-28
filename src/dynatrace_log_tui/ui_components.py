"""
Reusable UI components for the Dynatrace Log TUI
"""
from textual.widgets import DataTable, TextArea
from textual.binding import Binding
from typing import Dict, Any
from rich.text import Text


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
                    row_data.append(log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"))
                elif column == "Level":
                    level_style = LogTablePopulator.get_level_style(log["level"])
                    row_data.append(Text(log["level"], style=level_style))
                elif column == "Service":
                    row_data.append(log["service"])
                elif column == "Message":
                    message = log["message"]
                    row_data.append(message[:50] + "..." if len(message) > 50 else message)
                elif column == "Host":
                    row_data.append(log["host"])
                elif column == "Trace ID":
                    row_data.append(log["trace_id"])
                elif column == "Span ID":
                    row_data.append(log["span_id"])
                elif column == "Content":
                    content = log["content"]
                    row_data.append(content[:30] + "..." if len(content) > 30 else content)
            
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
        return f"""Timestamp: {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
Level: {log['level']}
Service: {log['service']}
Host: {log['host']}
Trace ID: {log['trace_id']}
Span ID: {log['span_id']}

Message:
{log['message']}

Content:
{log['content']}"""