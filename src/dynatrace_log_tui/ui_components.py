"""
Reusable UI components for the Dynatrace Log TUI
"""
from textual.widgets import DataTable, TextArea
from textual.binding import Binding
from typing import Dict, Any, Optional
from rich.text import Text
from rich.markup import escape
import re


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
    def _highlight_search_term(text: str, search_term: str) -> Text:
        """Highlight search term in text with yellow background"""
        if not search_term or not text:
            return Text(text)
        
        # Create a Text object
        rich_text = Text()
        
        # Find all matches (case-insensitive)
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        last_end = 0
        
        for match in pattern.finditer(text):
            # Add text before match
            if match.start() > last_end:
                rich_text.append(text[last_end:match.start()])
            
            # Add highlighted match
            rich_text.append(text[match.start():match.end()], style="bold yellow on black")
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            rich_text.append(text[last_end:])
        
        return rich_text
    
    @staticmethod
    def populate_table(table: LogTable, logs: list, visible_columns: list, search_term: str = "") -> None:
        """Populate the table with log data, optionally highlighting search terms"""
        table.clear()
        
        for log in logs:
            row_data = []
            for column in visible_columns:
                if column == "Timestamp":
                    # Timestamp is safe, no need to escape or highlight
                    row_data.append(log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"))
                elif column == "Level":
                    # Level uses Text with style, no markup parsing or search highlighting
                    level_style = LogTablePopulator.get_level_style(log["level"])
                    row_data.append(Text(log["level"], style=level_style))
                elif column == "Service":
                    # Apply search highlighting or escape
                    service_text = str(log["service"])
                    if search_term and search_term.lower() in service_text.lower():
                        row_data.append(LogTablePopulator._highlight_search_term(service_text, search_term))
                    else:
                        row_data.append(escape(service_text))
                elif column == "Message":
                    # Apply search highlighting to message and truncate if needed
                    message = str(log["message"])
                    truncated_message = message[:50] + "..." if len(message) > 50 else message
                    if search_term and search_term.lower() in message.lower():
                        row_data.append(LogTablePopulator._highlight_search_term(truncated_message, search_term))
                    else:
                        row_data.append(escape(truncated_message))
                elif column == "Host":
                    # Apply search highlighting or escape
                    host_text = str(log["host"])
                    if search_term and search_term.lower() in host_text.lower():
                        row_data.append(LogTablePopulator._highlight_search_term(host_text, search_term))
                    else:
                        row_data.append(escape(host_text))
                elif column == "Trace ID":
                    # Apply search highlighting or escape
                    trace_id = str(log["trace_id"])
                    if search_term and search_term.lower() in trace_id.lower():
                        row_data.append(LogTablePopulator._highlight_search_term(trace_id, search_term))
                    else:
                        row_data.append(escape(trace_id))
                elif column == "Span ID":
                    # Apply search highlighting or escape
                    span_id = str(log["span_id"])
                    if search_term and search_term.lower() in span_id.lower():
                        row_data.append(LogTablePopulator._highlight_search_term(span_id, search_term))
                    else:
                        row_data.append(escape(span_id))
                elif column == "Content":
                    # Apply search highlighting to content and truncate if needed
                    content = str(log["content"])
                    truncated_content = content[:30] + "..." if len(content) > 30 else content
                    if search_term and search_term.lower() in content.lower():
                        row_data.append(LogTablePopulator._highlight_search_term(truncated_content, search_term))
                    else:
                        row_data.append(escape(truncated_content))
            
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