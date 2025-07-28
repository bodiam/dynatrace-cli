from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Button, Static, Select
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
import csv
import argparse
import sys
from datetime import datetime
from typing import List, Dict, Any

from .data import generate_more_logs, filter_logs
from .api_client import DynatraceClient
from .models import TimeRange
from .ui_components import LogTable, QueryTextArea, LogDetails, LogTablePopulator
from .modals import SaveQueryModal, LoadQueryModal, ColumnSelectionModal, QueryHistoryModal, SearchModal
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
        Binding("/", "search", "Search"),
        Binding("n", "search_next", "Next Match"),
        Binding("shift+n", "search_prev", "Prev Match"),
        Binding("escape", "clear_search", "Clear Search"),
        Binding("f1", "help", "Help"),
    ]
    
    current_logs = reactive([])
    selected_log = reactive(None)
    
    def __init__(self, development_mode: bool = False):
        super().__init__()
        self.query_manager = QueryManager()
        self.query_history = QueryHistory()
        self.development_mode = development_mode
        
        # Initialize Dynatrace client with error handling
        if development_mode:
            # In development mode, always use dummy data
            self.dynatrace_client = None
            self.use_dummy_data = True
            self.token_error = "Development mode - using dummy data"
        else:
            # In production mode, require API credentials
            try:
                self.dynatrace_client = DynatraceClient()
                self.use_dummy_data = False
            except ValueError as e:
                # In production mode, exit if credentials are missing
                print(f"Error: {e}")
                print("\nTo run in development mode with dummy data, use:")
                print("  uv run python -m src.dynatrace_log_tui.main --development")
                sys.exit(1)
        
        # Initialize data based on mode
        if self.development_mode:
            # Only use dummy data in development mode
            self.all_logs = generate_more_logs(200)
            self.current_logs = self.all_logs.copy()
        else:
            # In production mode, start with empty logs and fetch real data on mount
            self.all_logs = []
            self.current_logs = []
        
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
        
        # Search functionality
        self.search_term = ""
        self.search_matches = []  # List of (row_index, column_index) tuples
        self.current_match_index = -1
        self.search_active = False
    
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
                yield Static("Loading...", id="log_count", classes="status")
            
            # Main content area
            with Vertical(id="main_content"):
                yield LogTable(id="log_table")
                yield Static("Log Details", classes="status")
                yield LogDetails(id="log_details")
        
        yield Footer()
    
    def on_mount(self) -> None:
        self.setup_table()
        
        # Set placeholder-like text for the query input
        query_input = self.query_one("#query_input", QueryTextArea)
        
        if self.development_mode:
            # Development mode - use dummy data
            self.populate_table()
            query_input.text = "# Development mode - using dummy data\n# Enter your DQL query here to test filtering...\n# Use Ctrl+R or Ctrl+Enter to run"
            self.notify("Development mode: Using dummy data for testing")
        else:
            # Production mode - fetch real logs from Dynatrace
            query_input.text = "# Connected to Dynatrace API\n# Loading recent logs...\n# Use Ctrl+R or Ctrl+Enter to run custom queries"
            self.notify("Loading recent logs from Dynatrace...")
            self._load_initial_logs()
    
    def _load_initial_logs(self):
        """Load initial logs from Dynatrace API on startup"""
        try:
            api_response = self.dynatrace_client.execute_query("fetch logs", self.current_time_range)
            
            if "error" in api_response:
                self.notify(f"Failed to load logs: {api_response['error']}")
                self.current_logs = []
            else:
                self.current_logs = self.dynatrace_client.convert_to_log_format(api_response)
                self.notify(f"Loaded {len(self.current_logs)} recent logs from Dynatrace")
                
                # Update query input to show success
                query_input = self.query_one("#query_input", QueryTextArea)
                query_input.text = "# Connected to Dynatrace API\n# Recent logs loaded - enter your DQL query here...\n# Use Ctrl+R or Ctrl+Enter to run"
                
        except Exception as e:
            self.notify(f"Error loading initial logs: {str(e)}")
            self.current_logs = []
        
        # Populate table with loaded data (or empty if failed)
        self.populate_table()
    
    def setup_table(self):
        table = self.query_one("#log_table", LogTable)
        LogTablePopulator.setup_table_columns(table, self.visible_columns)
    
    def populate_table(self):
        table = self.query_one("#log_table", LogTable)
        LogTablePopulator.populate_table(table, self.current_logs, self.visible_columns, self.search_term)
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
            
            if self.development_mode:
                # Development mode - use dummy data filtering
                self.current_logs = filter_logs(self.all_logs, actual_query)
                self.notify("Development mode: Filtering dummy data")
            elif self.use_dummy_data:
                # Fallback mode - use dummy data filtering
                self.current_logs = filter_logs(self.all_logs, actual_query)
                self.notify("Using dummy data - configure Dynatrace credentials for real data")
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
            if self.development_mode:
                # Development mode - use dummy data
                self.current_logs = self.all_logs.copy()
            else:
                # Production mode - reload recent logs from API
                try:
                    api_response = self.dynatrace_client.execute_query("fetch logs", self.current_time_range)
                    if "error" not in api_response:
                        self.current_logs = self.dynatrace_client.convert_to_log_format(api_response)
                        self.notify(f"Reloaded {len(self.current_logs)} recent logs")
                    else:
                        self.notify(f"Failed to reload logs: {api_response['error']}")
                        self.current_logs = []
                except Exception as e:
                    self.notify(f"Error reloading logs: {str(e)}")
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
        elif not self.details_visible:
            self.details_visible = True
            self._update_details_height()
            height = self.details_heights[self.current_details_index]
            self.notify(f"Log details shown: {height} lines")
    
    def action_decrease_details(self):
        if self.details_visible and self.current_details_index > 0:
            self.current_details_index -= 1
            self._update_details_height()
        elif self.details_visible and self.current_details_index == 0:
            self.details_visible = False
            self._update_details_height()
            self.notify("Log details hidden")
    
    def action_toggle_details(self):
        self.details_visible = not self.details_visible
        self._update_details_height()
        if not self.details_visible:
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
        if self.development_mode:
            count_widget.update(f"Showing: {len(self.current_logs)} / {len(self.all_logs)} (dummy data)")
        else:
            count_widget.update(f"Showing: {len(self.current_logs)} logs from Dynatrace")
    
    
    
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
    
    def action_search(self):
        """Open search dialog"""
        def handle_search_result(result):
            if result:
                if result.get("action") == "search":
                    search_term = result.get("term", "")
                    if search_term:
                        self._perform_search(search_term)
                    else:
                        self._clear_search()
                elif result.get("action") == "clear":
                    self._clear_search()
        
        self.push_screen(SearchModal(self.search_term), handle_search_result)
    
    def action_search_next(self):
        """Navigate to next search match"""
        if not self.search_active or not self.search_matches:
            self.notify("No active search. Press / to search.")
            return
        
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self._navigate_to_match()
    
    def action_search_prev(self):
        """Navigate to previous search match"""
        if not self.search_active or not self.search_matches:
            self.notify("No active search. Press / to search.")
            return
        
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self._navigate_to_match()
    
    def action_clear_search(self):
        """Clear current search and highlighting"""
        self._clear_search()
    
    def _perform_search(self, search_term: str):
        """Perform search and find all matches"""
        self.search_term = search_term.lower()
        self.search_matches = []
        self.current_match_index = -1
        self.search_active = True
        
        # Find all matches in current logs
        for row_index, log in enumerate(self.current_logs):
            for col_index, column in enumerate(self.visible_columns):
                if column == "Level":  # Skip level column as it's not text searchable
                    continue
                
                # Get the text content for this cell
                cell_text = ""
                if column == "Timestamp":
                    cell_text = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                elif column == "Service":
                    cell_text = str(log["service"])
                elif column == "Message":
                    cell_text = str(log["message"])
                elif column == "Host":
                    cell_text = str(log["host"])
                elif column == "Trace ID":
                    cell_text = str(log["trace_id"])
                elif column == "Span ID":
                    cell_text = str(log["span_id"])
                elif column == "Content":
                    cell_text = str(log["content"])
                
                # Check if search term is in this cell
                if self.search_term in cell_text.lower():
                    self.search_matches.append((row_index, col_index))
        
        # Update table with highlighting
        self.populate_table()
        
        # Navigate to first match or show no results
        if self.search_matches:
            self.current_match_index = 0
            self._navigate_to_match()
            self.notify(f"Found {len(self.search_matches)} matches for '{search_term}'")
        else:
            self.notify(f"No matches found for '{search_term}'")
    
    def _navigate_to_match(self):
        """Navigate to the current search match"""
        if not self.search_matches or self.current_match_index < 0:
            return
        
        row_index, col_index = self.search_matches[self.current_match_index]
        
        # Select the row in the table
        table = self.query_one("#log_table", LogTable)
        try:
            # Move cursor to the specific row and column
            table.move_cursor(row=row_index, column=col_index)
            # Scroll to make sure the row is visible
            table.scroll_to(row=row_index, column=col_index, animate=False)
        except Exception:
            # Fallback: just move cursor to row
            try:
                table.move_cursor(row=row_index)
            except Exception:
                # Last fallback: just set cursor coordinate
                table.cursor_coordinate = (row_index, col_index)
        
        # Update status
        self.notify(f"Match {self.current_match_index + 1} of {len(self.search_matches)}")
    
    def _clear_search(self):
        """Clear search state and highlighting"""
        self.search_term = ""
        self.search_matches = []
        self.current_match_index = -1
        self.search_active = False
        
        # Refresh table without highlighting
        self.populate_table()
        self.notify("Search cleared")

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
- /: Search within log entries
- n: Next search match
- Shift+N: Previous search match
- Escape: Clear search highlighting
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
5. Use / to search within the log entries
6. Use n/N to navigate between search matches
7. Save frequently used queries for later use
8. Browse automatic query history with Ctrl+H
9. Export filtered results to CSV file
10. Clear query with Ctrl+K or Escape when focused on query field

Query Examples:
- "ERROR" - Show only error logs
- "payment" - Show logs containing "payment"
- "user-service" - Show logs from user-service

Features:
- Real-time filtering of log data
- Search and highlight within displayed logs
- Multiple saved queries with CRUD operations
- CSV export of filtered results
- Detailed log inspection
- Keyboard navigation support
        """
        self.notify(help_text)

def main():
    parser = argparse.ArgumentParser(
        description="Dynatrace Log TUI - Terminal interface for querying Dynatrace logs"
    )
    parser.add_argument(
        "--development", 
        action="store_true",
        help="Run in development mode with dummy data (no API credentials required)"
    )
    
    args = parser.parse_args()
    
    app = DynatraceLogTUI(development_mode=args.development)
    app.run()

if __name__ == "__main__":
    main()