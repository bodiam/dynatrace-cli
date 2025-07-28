"""
Modal dialogs for the Dynatrace Log TUI
"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Input, TextArea, OptionList, Checkbox, Label
from textual.screen import ModalScreen
from textual.binding import Binding
from datetime import datetime
from typing import List

from .models import SavedQuery, HistoryQuery


class SaveQueryModal(ModalScreen):
    """Modal for saving a query"""
    
    CSS = """
    SaveQueryModal {
        align: center middle;
    }
    
    #save_dialog {
        width: 80;
        height: 25;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #save_query_input {
        width: 1fr;
        height: 6;
        margin: 1 0;
    }
    
    #save_name_input {
        width: 1fr;
        height: 3;
        margin: 1 0;
    }
    
    SaveQueryModal Button {
        margin: 1;
        min-width: 10;
    }
    """
    
    def __init__(self, current_query: str):
        super().__init__()
        self.current_query = current_query
    
    def compose(self) -> ComposeResult:
        with Container(id="save_dialog"):
            yield Static("Save Query", classes="status")
            yield Static("Query Name:")
            yield Input(placeholder="Enter query name...", id="save_name_input")
            yield Static("Query:")
            yield TextArea(self.current_query, id="save_query_input", read_only=True)
            with Horizontal():
                yield Button("Save", id="save_confirm", variant="primary")
                yield Button("Cancel", id="save_cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_confirm":
            name_input = self.query_one("#save_name_input", Input)
            if name_input.value.strip():
                self.dismiss({"action": "save", "name": name_input.value.strip(), "query": self.current_query})
            else:
                self.notify("Please enter a query name")
        elif event.button.id == "save_cancel":
            self.dismiss({"action": "cancel"})


class LoadQueryModal(ModalScreen):
    """Modal for loading a saved query"""
    
    CSS = """
    LoadQueryModal {
        align: center middle;
    }
    
    #load_dialog {
        width: 80;
        height: 25;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #load_query_list {
        height: 15;
        border: solid $secondary;
        margin: 1 0;
    }
    
    LoadQueryModal Button {
        margin: 1;
        min-width: 10;
    }
    """
    
    def __init__(self, queries: List[SavedQuery]):
        super().__init__()
        self.queries = queries
    
    def compose(self) -> ComposeResult:
        with Container(id="load_dialog"):
            yield Static("Load Query", classes="status")
            if self.queries:
                query_options = [(f"{q.name} - {q.query[:30]}...", q.name) for q in self.queries]
                yield OptionList(*[option[0] for option in query_options], id="load_query_list")
            else:
                yield Static("No saved queries found", id="load_query_list")
            with Horizontal():
                yield Button("Load", id="load_confirm", variant="primary")
                yield Button("Delete", id="load_delete", variant="error")
                yield Button("Cancel", id="load_cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load_confirm":
            if self.queries:
                option_list = self.query_one("#load_query_list", OptionList)
                if option_list.highlighted is not None:
                    selected_query = self.queries[option_list.highlighted]
                    self.dismiss({"action": "load", "query": selected_query})
                else:
                    self.notify("Please select a query")
            else:
                self.notify("No queries to load")
        elif event.button.id == "load_delete":
            if self.queries:
                option_list = self.query_one("#load_query_list", OptionList)
                if option_list.highlighted is not None:
                    selected_query = self.queries[option_list.highlighted]
                    self.dismiss({"action": "delete", "query": selected_query})
                else:
                    self.notify("Please select a query to delete")
            else:
                self.notify("No queries to delete")
        elif event.button.id == "load_cancel":
            self.dismiss({"action": "cancel"})


class ColumnSelectionModal(ModalScreen):
    """Modal for selecting visible columns"""
    
    BINDINGS = [
        Binding("up", "scroll_up", "Scroll Up"),
        Binding("down", "scroll_down", "Scroll Down"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
    ]
    
    CSS = """
    ColumnSelectionModal {
        align: center middle;
    }
    
    #column_dialog {
        width: 60;
        height: 80%;
        max-height: 40;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #column_list {
        height: 1fr;
        min-height: 25;
        border: solid $secondary;
        margin: 1 0;
        overflow-y: auto;
    }
    
    .column-row {
        height: 3;
        width: 100%;
        margin: 0;
        padding: 0 1;
    }
    
    .column-row Checkbox {
        width: auto;
        margin-right: 1;
    }
    
    .column-row Label {
        width: 1fr;
    }
    
    ColumnSelectionModal Button {
        margin: 1;
        min-width: 10;
    }
    
    #column_list {
        height: 1fr;
        min-height: 25;
        max-height: 30;
        border: solid $secondary;
        margin: 1 0;
        overflow-y: auto;
    }
    """
    
    def __init__(self, available_columns: List[str], selected_columns: List[str]):
        super().__init__()
        self.available_columns = available_columns
        self.selected_columns = selected_columns.copy()
        self.checkboxes = {}
    
    def _make_valid_id(self, column_name: str) -> str:
        """Convert column name to a valid widget ID by replacing spaces with underscores."""
        return f"col_{column_name.replace(' ', '_').replace('-', '_')}"
    
    def compose(self) -> ComposeResult:
        with Container(id="column_dialog"):
            yield Static("Select Columns to Display", classes="status")
            
            with VerticalScroll(id="column_list"):
                # First, add selected columns at the top
                for column in self.selected_columns:
                    if column in self.available_columns:
                        with Horizontal(classes="column-row"):
                            checkbox = Checkbox(value=True, id=self._make_valid_id(column))
                            self.checkboxes[column] = checkbox
                            yield checkbox
                            yield Label(column)
                
                # Then add remaining columns alphabetically
                remaining_columns = sorted([col for col in self.available_columns if col not in self.selected_columns])
                for column in remaining_columns:
                    with Horizontal(classes="column-row"):
                        checkbox = Checkbox(value=False, id=self._make_valid_id(column))
                        self.checkboxes[column] = checkbox
                        yield checkbox
                        yield Label(column)
            
            with Horizontal():
                yield Button("Apply", id="column_apply", variant="primary")
                yield Button("Cancel", id="column_cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "column_apply":
            # Get selected columns from checkboxes
            selected = []
            for column, checkbox in self.checkboxes.items():
                if checkbox.value:
                    selected.append(column)
            self.dismiss({"action": "apply", "columns": selected})
        elif event.button.id == "column_cancel":
            self.dismiss({"action": "cancel"})


class QueryHistoryModal(ModalScreen):
    """Modal for browsing query history"""
    
    CSS = """
    QueryHistoryModal {
        align: center middle;
    }
    
    #history_dialog {
        width: 80;
        height: 30;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #history_query_list {
        height: 20;
        border: solid $secondary;
        margin: 1 0;
    }
    
    QueryHistoryModal Button {
        margin: 1;
        min-width: 10;
    }
    """
    
    def __init__(self, history_queries: List[HistoryQuery]):
        super().__init__()
        self.history_queries = history_queries
    
    def compose(self) -> ComposeResult:
        with Container(id="history_dialog"):
            yield Static("Query History", classes="status")
            if self.history_queries:
                history_options = []
                for i, query in enumerate(self.history_queries):
                    # Format the query for display (truncate long queries)
                    query_preview = query.query.replace('\n', ' ').strip()
                    if len(query_preview) > 60:
                        query_preview = query_preview[:57] + "..."
                    
                    # Format the timestamp
                    try:
                        dt = datetime.fromisoformat(query.executed_at)
                        time_str = dt.strftime("%m/%d %H:%M")
                    except:
                        time_str = "Recent"
                    
                    display_text = f"[{time_str}] {query_preview}"
                    history_options.append(display_text)
                
                yield OptionList(*history_options, id="history_query_list")
            else:
                yield Static("No query history found", id="history_query_list")
            
            with Horizontal():
                yield Button("Load", id="history_load", variant="primary")
                yield Button("Delete", id="history_delete", variant="error")
                yield Button("Clear All", id="history_clear_all", variant="error")
                yield Button("Cancel", id="history_cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "history_load":
            if self.history_queries:
                option_list = self.query_one("#history_query_list", OptionList)
                if option_list.highlighted is not None:
                    selected_query = self.history_queries[option_list.highlighted]
                    self.dismiss({"action": "load", "query": selected_query})
                else:
                    self.notify("Please select a query from history")
            else:
                self.notify("No history to load")
        elif event.button.id == "history_delete":
            if self.history_queries:
                option_list = self.query_one("#history_query_list", OptionList)
                if option_list.highlighted is not None:
                    selected_index = option_list.highlighted
                    self.dismiss({"action": "delete", "index": selected_index})
                else:
                    self.notify("Please select a query to delete")
            else:
                self.notify("No history to delete")
        elif event.button.id == "history_clear_all":
            self.dismiss({"action": "clear_all"})
        elif event.button.id == "history_cancel":
            self.dismiss({"action": "cancel"})
    
    def action_scroll_up(self) -> None:
        history_list = self.query_one("#history_query_list")
        history_list.scroll_up()
    
    def action_scroll_down(self) -> None:
        history_list = self.query_one("#history_query_list")
        history_list.scroll_down()
    
    def action_page_up(self) -> None:
        history_list = self.query_one("#history_query_list")
        history_list.scroll_page_up()
    
    def action_page_down(self) -> None:
        history_list = self.query_one("#history_query_list")
        history_list.scroll_page_down()