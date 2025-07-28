from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Button, Static, Select
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
import csv
from datetime import datetime
from typing import List, Dict, Any

from .data import generate_more_logs, filter_logs
from .api_client import DynatraceClient
from .models import TimeRange
from .ui_components import LogTable, QueryTextArea, LogDetails, LogTablePopulator
from .modals import SaveQueryModal, LoadQueryModal, ColumnSelectionModal, QueryHistoryModal
from .query_manager import QueryManager, QueryHistory, QueryProcessor





class DynatraceLogTUI(App):
    CSS = """
    #query_section {
        height: auto;
        max-height: 12;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #query_input {
        height: 6;
        border: solid $primary;
        width: 1fr;
        margin-right: 1;
    }
    
    #time_range_select {
        width: 35;
        margin-right: 1;
    }
    
    #log_table {
        height: 1fr;
        min-height: 20;
        border: solid $secondary;
    }
    
    #log_details {
        height: 10;
        border: solid $secondary;
        background: $surface;
    }
    
    #log_details.hidden {
        height: 0;
        display: none;
    }
    
    #main_content {
        width: 1fr;
        height: 1fr;
    }
    
    .button {
        margin: 0 1;
        min-width: 12;
    }
    
    .status {
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "run_query", "Run Query"),
        Binding("ctrl+enter", "run_query", "Run Query"),
        Binding("ctrl+s", "save_query", "Save Query"),
        Binding("ctrl+l", "load_query", "Load Query"),
        Binding("ctrl+h", "query_history", "History"),
        Binding("ctrl+c", "clear_query", "Clear"),
        Binding("ctrl+o", "column_selection", "Columns", priority=True),
        Binding("]", "increase_details", "Details+"),
        Binding("[", "decrease_details", "Details-"),
        Binding("ctrl+0", "toggle_details", "Toggle Details"),
        Binding("ctrl+e", "export_logs", "Export"),
        Binding("f1", "help", "Help"),
    ]
    
    current_logs = reactive([])
    selected_log = reactive(None)
    
    def __init__(self):
        super().__init__()
        self.query_manager = QueryManager()
        self.query_history = QueryHistory()
        
        # Initialize Dynatrace client with error handling
        try:
            self.dynatrace_client = DynatraceClient()
            self.use_dummy_data = False
        except ValueError as e:
            # If token is not set, use dummy data and show error
            self.dynatrace_client = None
            self.use_dummy_data = True
            self.token_error = str(e)
        
        # Initialize with dummy data for now
        self.all_logs = generate_more_logs(200)
        self.current_logs = self.all_logs.copy()
        self.current_query_name = ""
        self.current_time_range = "30m"  # Default time range
        
        # Column management
        self.all_columns = [
            "Timestamp", "Level", "Service", "Message", "Host", "Trace ID", "Span ID", "Content",
            "User ID", "Session ID", "Request ID", "Response Time", "Status Code", "Method", 
            "Endpoint", "Client IP", "User Agent", "Referer", "Thread ID", "Process ID",
            "Memory Usage", "CPU Usage", "Disk IO", "Network IO", "Cache Hit", "Database Query",
            "Error Code", "Stack Trace", "Custom Field 1", "Custom Field 2"
        ]
        self.visible_columns = ["Timestamp", "Level", "Service", "Message", "Host"]  # Default visible columns
        
        # Log details sizing
        self.details_heights = [5, 10, 15, 20, 30]  # Available heights
        self.current_details_index = 1  # Start with height 10 (index 1)
        self.details_visible = True
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        # Top query section with full width
        with Vertical():
            with Container(id="query_section"):
                yield Static("DQL Query", classes="status")
                with Horizontal():
                    yield QueryTextArea("", id="query_input")
                    with Vertical():
                        yield Static("Time Range:")
                        time_ranges = TimeRange.get_time_ranges()
                        yield Select(
                            options=[(label, value) for label, value in time_ranges],
                            value="30m",
                            id="time_range_select"
                        )
                    yield Button("Run Query", id="run_btn", classes="button")
                yield Static(f"Total Logs: {len(self.all_logs)}", id="log_count", classes="status")
            
            # Main content area
            with Vertical(id="main_content"):
                yield LogTable(id="log_table")
                yield Static("Log Details", classes="status")
                yield LogDetails(id="log_details")
        
        yield Footer()
    
    def on_mount(self) -> None:
        self.setup_table()
        self.populate_table()
        # Set placeholder-like text for the query input
        query_input = self.query_one("#query_input", QueryTextArea)
        if self.use_dummy_data:
            query_input.text = f"# {self.token_error}\n# Using dummy data for now...\n# Enter your DQL query here...\n# Use Ctrl+R or Ctrl+Enter to run"
            self.notify("Warning: Using dummy data - Dynatrace token not configured")
        else:
            query_input.text = "# Enter your DQL query here...\n# Use Ctrl+R or Ctrl+Enter to run"
    
    def setup_table(self):
        table = self.query_one("#log_table", LogTable)
        LogTablePopulator.setup_table_columns(table, self.visible_columns)
    
    def populate_table(self):
        table = self.query_one("#log_table", LogTable)
        LogTablePopulator.populate_table(table, self.current_logs, self.visible_columns)
        # Update log count after populating
        self.update_log_count()
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.cursor_row < len(self.current_logs):
            log = self.current_logs[event.cursor_row]
            self.selected_log = log
            self.update_log_details(log)
    
    def update_log_details(self, log: Dict[str, Any]):
        details = self.query_one("#log_details", LogDetails)
        details.text = LogTablePopulator.format_log_details(log)
    
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run_btn":
            query_input = self.query_one("#query_input", QueryTextArea)
            self.run_query(query_input.text)
    
    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "time_range_select":
            self.current_time_range = event.value
    
    def on_key(self, event) -> None:
        # Handle Ctrl+O globally regardless of focused widget
        if event.key == "ctrl+o":
            self.action_column_selection()
            event.prevent_default()
    
    def run_query(self, query: str):
        actual_query = QueryProcessor.clean_query(query)
        
        if actual_query:
            # Add to history when executing a real query
            self.query_history.add_query(actual_query)
            
            if self.use_dummy_data:
                # Use dummy data filtering
                self.current_logs = filter_logs(self.all_logs, actual_query)
                self.notify("Using dummy data - set DYNATRACE_TOKEN environment variable for real data")
            else:
                # Execute real Dynatrace query
                self.notify("Executing query...")
                try:
                    api_response = self.dynatrace_client.execute_query(actual_query, self.current_time_range)
                    
                    if "error" in api_response:
                        self.notify(f"Query failed: {api_response['error']}")
                        self.current_logs = []
                    else:
                        self.current_logs = self.dynatrace_client.convert_to_log_format(api_response)
                        self.notify(f"Query completed - {len(self.current_logs)} records")
                        
                except Exception as e:
                    self.notify(f"Query error: {str(e)}")
                    self.current_logs = []
        else:
            if self.use_dummy_data:
                self.current_logs = self.all_logs.copy()
            else:
                # For empty query with real API, show recent logs
                try:
                    api_response = self.dynatrace_client.execute_query("fetch logs", self.current_time_range)
                    if "error" not in api_response:
                        self.current_logs = self.dynatrace_client.convert_to_log_format(api_response)
                    else:
                        self.current_logs = []
                except:
                    self.current_logs = []
        
        self.populate_table()
        self.update_log_count()
    
    def action_save_query(self):
        query_input = self.query_one("#query_input", QueryTextArea)
        query = QueryProcessor.clean_query(query_input.text)
        
        if not query:
            self.notify("Please enter a query to save")
            return
        
        def handle_save_result(result):
            if result and result.get("action") == "save":
                name = result.get("name")
                query_to_save = result.get("query")
                if self.query_manager.add_query(name, query_to_save):
                    self.notify(f"Query '{name}' saved successfully")
                else:
                    self.notify(f"Query '{name}' already exists")
        
        self.push_screen(SaveQueryModal(query), handle_save_result)
    
    def action_load_query(self):
        def handle_load_result(result):
            if result:
                if result.get("action") == "load":
                    query = result.get("query")
                    if query:
                        query_input = self.query_one("#query_input", QueryTextArea)
                        query_input.text = query.query
                        self.notify(f"Loaded query '{query.name}'")
                elif result.get("action") == "delete":
                    query = result.get("query")
                    if query:
                        self.query_manager.delete_query(query.name)
                        self.notify(f"Query '{query.name}' deleted successfully")
                        # Reopen the load dialog to show updated list
                        self.action_load_query()
        
        self.push_screen(LoadQueryModal(self.query_manager.queries), handle_load_result)
    
    def action_query_history(self):
        def handle_history_result(result):
            if result:
                if result.get("action") == "load":
                    query = result.get("query")
                    if query:
                        query_input = self.query_one("#query_input", QueryTextArea)
                        query_input.text = query.query
                        self.notify(f"Loaded query from history")
                elif result.get("action") == "delete":
                    index = result.get("index")
                    if index is not None:
                        if self.query_history.clear_entry(index):
                            self.notify(f"Query deleted from history")
                            # Reopen the history dialog to show updated list
                            self.action_query_history()
                        else:
                            self.notify("Failed to delete query")
                elif result.get("action") == "clear_all":
                    self.query_history.clear_all()
                    self.notify("All query history cleared")
                    # Reopen the history dialog to show empty list
                    self.action_query_history()
        
        recent_queries = self.query_history.get_recent_queries(20)
        self.push_screen(QueryHistoryModal(recent_queries), handle_history_result)
    
    def action_clear_query(self):
        query_input = self.query_one("#query_input", QueryTextArea)
        query_input.text = ""
        self.current_logs = self.all_logs.copy()
        self.populate_table()
        self.update_log_count()
    
    def action_column_selection(self):
        def handle_column_result(result):
            if result and result.get("action") == "apply":
                new_columns = result.get("columns", [])
                if new_columns:  # Ensure at least one column is selected
                    self.visible_columns = new_columns
                    self.setup_table()  # Recreate table with new columns
                    self.populate_table()  # Repopulate with new column layout
                    self.notify(f"Updated columns: {', '.join(new_columns)}")
                else:
                    self.notify("At least one column must be selected")
        
        self.push_screen(ColumnSelectionModal(self.all_columns, self.visible_columns), handle_column_result)
    
    def action_increase_details(self):
        if self.details_visible and self.current_details_index < len(self.details_heights) - 1:
            self.current_details_index += 1
            self._update_details_height()
            height = self.details_heights[self.current_details_index]
            self.notify(f"Log details height: {height} lines")
        elif not self.details_visible:
            self.details_visible = True
            self._update_details_height()
            height = self.details_heights[self.current_details_index]
            self.notify(f"Log details shown: {height} lines")
    
    def action_decrease_details(self):
        if self.details_visible and self.current_details_index > 0:
            self.current_details_index -= 1
            self._update_details_height()
            height = self.details_heights[self.current_details_index]
            self.notify(f"Log details height: {height} lines")
        elif self.details_visible and self.current_details_index == 0:
            self.details_visible = False
            self._update_details_height()
            self.notify("Log details hidden")
    
    def action_toggle_details(self):
        self.details_visible = not self.details_visible
        self._update_details_height()
        if self.details_visible:
            height = self.details_heights[self.current_details_index]
            self.notify(f"Log details shown: {height} lines")
        else:
            self.notify("Log details hidden")
    
    def _update_details_height(self):
        details = self.query_one("#log_details", LogDetails)
        if self.details_visible:
            height = self.details_heights[self.current_details_index]
            details.styles.height = height
            details.remove_class("hidden")
        else:
            details.styles.height = 0
            details.add_class("hidden")
    
    
    def update_log_count(self):
        count_widget = self.query_one("#log_count", Static)
        count_widget.update(f"Showing: {len(self.current_logs)} / {len(self.all_logs)}")
    
    
    
    def action_run_query(self):
        query_input = self.query_one("#query_input", QueryTextArea)
        self.run_query(query_input.text)
    
    def action_export_logs(self):
        filename = f"dynatrace_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'level', 'service', 'message', 'host', 'trace_id', 'span_id', 'content']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for log in self.current_logs:
                    writer.writerow({
                        'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'level': log['level'],
                        'service': log['service'],
                        'message': log['message'],
                        'host': log['host'],
                        'trace_id': log['trace_id'],
                        'span_id': log['span_id'],
                        'content': log['content']
                    })
            
            self.notify(f"Exported {len(self.current_logs)} logs to {filename}")
        except Exception as e:
            self.notify(f"Export failed: {str(e)}")
    
    def action_help(self):
        help_text = """
Dynatrace Log TUI - Help

Keyboard Shortcuts:
- Ctrl+Q: Quit application
- Ctrl+R or Ctrl+Enter: Run current query
- Ctrl+S: Save current query (opens dialog)
- Ctrl+L: Load saved query (opens dialog)
- Ctrl+H: Browse query history (opens dialog)
- Ctrl+C: Clear current query
- Ctrl+O: Select columns to display (opens dialog)
- ]: Increase log details height
- [: Decrease log details height
- Ctrl+0: Toggle log details visibility
- Ctrl+E: Export current results to CSV
- F1: Show this help

Usage:
1. Enter a DQL-like query in the input field
2. Press Ctrl+R, Ctrl+Enter, or click "Run Query" to execute
3. Browse results in the table using arrow keys
4. Select a row to view detailed log information
5. Save frequently used queries for later use
6. Browse automatic query history with Ctrl+H
7. Export filtered results to CSV file
8. Clear query with Ctrl+K or Escape when focused on query field

Query Examples:
- "ERROR" - Show only error logs
- "payment" - Show logs containing "payment"
- "user-service" - Show logs from user-service

Features:
- Real-time filtering of log data
- Multiple saved queries with CRUD operations
- CSV export of filtered results
- Detailed log inspection
- Keyboard navigation support
        """
        self.notify(help_text)

def main():
    app = DynatraceLogTUI()
    app.run()

if __name__ == "__main__":
    main()