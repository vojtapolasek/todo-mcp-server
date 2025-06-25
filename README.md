# Todo MCP Server

A Model Context Protocol (MCP) server for intelligent todo.txt management. This server provides both specialized tools and a generic interface for LLMs to interact with your todo.txt files, offering context-aware task suggestions based on energy levels, time availability, and priorities.

## Features

### Smart Task Suggestions
- **Energy-aware filtering**: Match tasks to your current energy level (high/medium/low)
- **Time-based recommendations**: Suggest tasks based on available time (@quick, @medium, @deep)
- **Priority and due-date sorting**: Automatic prioritization following todo.txt best practices
- **Context filtering**: Support for offline work, specific contexts, and project-based filtering

### Two Server Modes
1. **Multi-tool server** (`server.py`): 6 specialized tools for specific todo operations
2. **Simple server** (`simple_server.py`): Single generic tool for flexible LLM analysis

### Todo.txt Compatibility
- Full todo.txt format support with extensions
- Topydo-compatible sorting and filtering
- Enhanced context system for productivity optimization
- Recurrence pattern recognition (excludes `rec:+1w` from project parsing)

## Quick Start

### Prerequisites
- Python 3.9+
- todo.txt file

### Installation
```bash
git clone https://github.com/vojtapolasek/todo-mcp-server.git
cd todo-mcp-server
pip install -r requirements.txt

# Basic usage

## Run the multi-tool server
python src/server.py /path/to/your/todo.txt

##  Run the simple server (single tool)
python src/simple_server.py /path/to/your/todo.txt

# Integration with OpenWebUI
1. Install [mcpo-proxy](https://github.com/modelcontextprotocol/mcpo-proxy) to expose MCP as OpenAPI
2. Configure the proxy to point to your running server
3. Add the OpenAPI endpoint to OpenWebUI
4. Use the suggested system prompt for optimal results

## Context Tags for Enhanced Productivity

### Energy Level Contexts
- **High energy**: `@focus` `@creative` `@complex` `@brainstorm` `@learn`
- **Low energy**: `@routine` `@admin` `@communicate` `@organize` `@review`

### Time Duration Contexts
- **Quick tasks (≤15 min)**: `@quick` `@call` `@email`
- **Medium tasks (15-60 min)**: `@medium` `@meeting`
- **Long tasks (>60 min)**: `@deep` `@project`

### Example Todo Items
```
(A) finish quarterly report due:2025-01-15 +work @focus @deep
backup laptop @routine @quick +maintenance
call insurance company @call @quick +personal
brainstorm product features @creative @brainstorm +product
```

## Available Tools

### Multi-tool Server (server.py)
1. `get_task_overview` - Comprehensive task statistics and counts
2. `suggest_next_task` - Smart task recommendations with energy/time filtering
3. `show_project_tasks` - Tasks filtered by specific project
4. `show_waiting_tasks` - Tasks blocked/waiting for others
5. `show_inbox_tasks` - Unprocessed inbox items (+in project)
6. `show_context_tasks` - Tasks filtered by specific context

### Simple Server (simple_server.py)
1. `get_all_tasks` - Flexible task retrieval with comprehensive filtering options

## System Prompt for LLMs

```
You are my todo list assistant. You have tools to read my todo.txt file and get current date.

**CRITICAL RULES:**
- ALWAYS use tools before answering - never guess task content
- Quote tasks EXACTLY as returned by tools
- Only use information from tool responses - never add details
- Get current date at conversation start
- Leave tool arguments empty if I don't specify filters

**TASK ANALYSIS:**
- Priority: Only (A), (B), (C) from actual task text
- Energy contexts: High=@focus @creative @brainstorm @learn, Low=@routine @admin @organize @review
- Time contexts: @quick (≤15min), @medium (15-60min), @deep (>60min)
- Due dates: Only from "due:YYYY-MM-DD" format

**RESPONSE FORMAT:**
1. Get current date
2. Use todo tools
3. Quote exact task: "task text here"
4. Explain reasoning from retrieved data only
5. State if tools return errors/no data

**NEVER:**
- Invent task details not in tool output
- Estimate times without time contexts
- Assume task complexity
- Suggest non-existent tasks

Base everything on actual tool responses. When uncertain, ask for clarification.
```

## Development

### Running Tests
```bash
./run_tests.sh
```

### Manual Testing
```bash
python manual_test.py
```

### Project Structure
```
todo-mcp-server/
├── src/
│   ├── server.py              # Multi-tool MCP server
│   ├── simple_server.py       # Single-tool MCP server
│   ├── todo_manager.py        # High-level todo management
│   └── todo_parser.py         # Todo.txt parsing logic
├── tests/                     # Comprehensive test suite
├── requirements.txt
└── README.md
```

## Configuration

The server expect a todo.txt file path as a command-line argument. Ensure your todo.txt file is accessible and uses standard todo.txt format.


## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `./run_tests.sh`
5. Submit a pull request

## Use Cases

- **Personal productivity**: Context-aware task suggestions for optimal workflow
- **Team coordination**: Waiting task tracking and project management
- **Time management**: Smart task filtering based on available time slots
- **Energy management**: Match tasks to your current focus capacity
- **Offline work**: Filter tasks that can be completed without internet
