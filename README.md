# Dynatrace Log TUI

A Terminal User Interface (TUI) application for querying and browsing Dynatrace logs using DQL (Dynatrace Query Language). Built with Python and Textual, inspired by [Posting.sh](https://posting.sh/).

## Features

- **Real Dynatrace API Integration**: Execute DQL queries against your Dynatrace environment
- **Interactive Log Browser**: Browse results in a table with keyboard navigation
- **Time Range Selection**: Choose from predefined time ranges (30min, 1h, 2h, 6h, today, yesterday, 24h, 7d)
- **Log Search & Highlighting**: Search within log entries with yellow highlighting and match navigation
- **Detailed Log Inspection**: View complete log details in a dedicated panel
- **Query Management**: Save, load, and manage frequently used queries
- **Query History**: Browse and reuse previous queries with delete/clear options
- **Column Selection**: Choose which log columns to display
- **CSV Export**: Export filtered results to CSV files
- **Rich UI**: Color-coded log levels and intuitive interface
- **Fallback Mode**: Works with dummy data when Dynatrace connection is unavailable

## Prerequisites

Before using this application, you need:

1. **Dynatrace Environment**: Access to a Dynatrace environment
2. **API Token**: A Dynatrace API token with appropriate permissions

### Creating a Dynatrace API Token

1. Go to [https://myaccount.dynatrace.com/platformTokens](https://myaccount.dynatrace.com/platformTokens)
2. Click "Create new token"
3. Give it a descriptive name (e.g., "Log TUI Access")
4. Add the following scopes:
   - `storage:logs:read`
   - `storage:buckets:read`
5. Copy the generated token (starts with `dt0s16.`)

## Configuration

Set the required environment variables:

```bash
# Your Dynatrace environment URL (required)
export DYNATRACE_BASE_URL='https://abc12345.apps.dynatrace.com'

# Your Dynatrace API token (required)
export DYNATRACE_TOKEN='dt0s16.YOUR_TOKEN_HERE'
```

> **Note**: Replace `abc12345` with your actual Dynatrace environment ID and `YOUR_TOKEN_HERE` with your actual token.

## Installation

This project uses Python 3.13+ and can be installed using pip or uv.

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd dynatrace-log-tui

# Install dependencies
pip install -e .

# Run the application
dynatrace-log-tui
```

### Using uv (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd dynatrace-log-tui

# Install dependencies and run in production mode (requires API credentials)
uv run python -m src.dynatrace_log_tui.main

# Or run in development mode (uses dummy data, no credentials required)
uv run python -m src.dynatrace_log_tui.main --development

# Or install as a package and run
uv pip install -e .
dynatrace-log-tui

# Development mode with installed package
dynatrace-log-tui --development
```

## Usage

### Basic Operations

#### Production Mode (with API credentials)
1. **Set Environment Variables**: Configure `DYNATRACE_BASE_URL` and `DYNATRACE_TOKEN`
2. **Start the Application**: Run `dynatrace-log-tui` or `uv run python -m src.dynatrace_log_tui.main`
3. **Select Time Range**: Choose from the dropdown (defaults to "Last 30 minutes")
4. **Enter DQL Query**: Type your DQL query in the input field
5. **Execute Query**: Press `Ctrl+R`, `Ctrl+Enter`, or click "Run Query"
6. **Browse Results**: Use arrow keys to navigate the log table
7. **View Details**: Select a log entry to see detailed information

#### Development Mode (dummy data)
1. **Start the Application**: Run `dynatrace-log-tui --development` or `uv run python -m src.dynatrace_log_tui.main --development`
2. **Test UI Features**: All functionality works with generated dummy data
3. **Simulate Queries**: Enter search terms to filter dummy log entries
4. **No API Required**: Perfect for testing, development, and demonstrations

### Keyboard Shortcuts

- `Ctrl+Q`: Quit application
- `Ctrl+R` / `Ctrl+Enter`: Execute current query
- `Ctrl+S`: Save current query (opens save dialog)
- `Ctrl+L`: Load saved query (opens load dialog)
- `Ctrl+H`: Browse query history (with delete/clear options)
- `Ctrl+C`: Clear current query
- `Ctrl+O`: Select columns to display
- `/`: Search within log entries (case-insensitive)
- `n`: Navigate to next search match
- `Shift+N`: Navigate to previous search match
- `Escape`: Clear search highlighting
- `Ctrl+E`: Export current results to CSV
- `]` / `[`: Increase/decrease log details panel height
- `Ctrl+0`: Toggle log details panel visibility
- `F1`: Show help information

### DQL Query Examples

- `fetch logs` - Get recent logs
- `fetch logs | filter loglevel == "ERROR"` - Show only error logs
- `fetch logs | filter contains(content, "payment")` - Logs containing "payment"
- `fetch logs | filter dt.entity.service == "user-service"` - Logs from specific service
- `fetch logs | filter in(loglevel, {"ERROR", "WARN"})` - Error and warning logs
- `fetch logs | sort timestamp desc | limit 100` - Latest 100 logs

## Architecture

The application follows a modular architecture for maintainability and extensibility:

### Core Modules

- **`main.py`**: Main TUI application orchestration using Textual framework
- **`api_client.py`**: Dynatrace API client with real-time query execution
- **`models.py`**: Data models (TimeRange, HistoryQuery, SavedQuery) and utilities
- **`ui_components.py`**: Reusable UI widgets (LogTable, QueryTextArea, LogDetails)
- **`modals.py`**: Modal dialogs (Save/Load queries, Column selection, History browser)
- **`query_manager.py`**: Business logic for query and history management
- **`data.py`**: Dummy data generation for fallback mode

### Key Features

- **Real API Integration**: Direct integration with Dynatrace APIs
- **Smart Fallback**: Automatically uses dummy data when API is unavailable
- **Modular Design**: Clean separation of concerns for easy maintenance
- **Persistent Storage**: Query history and saved queries stored in JSON files
- **Environment-based Configuration**: Secure credential management via environment variables

## Error Handling

The application provides clear error messages for common issues:

- **Missing Environment Variables**: Detailed setup instructions
- **API Connection Issues**: Graceful fallback to dummy data mode
- **Query Errors**: Clear error messages from Dynatrace API
- **Network Timeouts**: Configurable timeout handling

## Operating Modes

### Production Mode (Default)
- **Requirements**: `DYNATRACE_BASE_URL` and `DYNATRACE_TOKEN` must be set
- **Data Source**: Real-time data from your Dynatrace environment
- **Features**: Full DQL query support, configurable time ranges
- **Usage**: `dynatrace-log-tui` or `uv run python -m src.dynatrace_log_tui.main`
- **Error Handling**: Application exits with helpful error message if credentials are missing

### Development Mode
- **Requirements**: No API credentials needed
- **Data Source**: Generated dummy data for testing
- **Features**: All UI features functional, query filtering simulation
- **Usage**: `dynatrace-log-tui --development` or `uv run python -m src.dynatrace_log_tui.main --development`
- **Purpose**: Testing, development, and demonstration without API access

## Development

### Project Structure

```
dynatrace-log-tui/
├── src/
│   └── dynatrace_log_tui/
│       ├── __init__.py
│       ├── main.py           # Main TUI application & orchestration
│       ├── api_client.py     # Dynatrace API integration
│       ├── models.py         # Data models and time utilities
│       ├── ui_components.py  # Reusable UI widgets
│       ├── modals.py         # Modal dialog components
│       ├── query_manager.py  # Query & history management
│       └── data.py           # Dummy data generation
├── pyproject.toml            # Project configuration
├── README.md                 # This documentation
└── uv.lock                   # Dependency lock file
```

### Environment Variables

The application requires these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `DYNATRACE_BASE_URL` | Your Dynatrace environment URL | `https://abc12345.apps.dynatrace.com` |
| `DYNATRACE_TOKEN` | Dynatrace API token | `dt0s16.ABC123...` |

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd dynatrace-log-tui

# Install dependencies
uv pip install -e .

# Run in development mode (no API credentials needed)
dynatrace-log-tui --development

# Or run with uv directly
uv run python -m src.dynatrace_log_tui.main --development

# For production testing, set environment variables:
export DYNATRACE_BASE_URL='https://your-env.apps.dynatrace.com'
export DYNATRACE_TOKEN='your-token-here'

# Then run in production mode
dynatrace-log-tui
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Future Enhancements

- **Advanced DQL Support**: Enhanced DQL syntax validation and auto-completion
- **Real-time Log Streaming**: Live log updates from Dynatrace
- **Theme Customization**: Multiple color themes and UI customization
- **Query Syntax Highlighting**: Enhanced query input with syntax highlighting
- **Export Formats**: JSON, XML, and other export formats
- **Advanced Filtering**: Custom filter expressions and saved filters
- **Performance Optimization**: Query caching and result pagination

## License

This project is open source and available under the MIT License.

## Inspiration

This project is inspired by [Posting.sh](https://posting.sh/), an excellent TUI client for Postman. The goal is to provide a similar experience for Dynatrace log querying and analysis.