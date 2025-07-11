"""
MCP Server for Todo.txt management
"""
import asyncio
import json
import sys
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    CallToolRequest,
    ListToolsRequest
)
from todo_manager import TodoManager

# Global todo manager - will be initialized with actual file path
todo_manager: TodoManager = None

def init_todo_manager(todo_file_path: str):
    """Initialize the todo manager with file path"""
    global todo_manager
    todo_manager = TodoManager(todo_file_path)

# Create server instance
server = Server("todo-assistant")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_task_overview",
            description="Get comprehensive overview of all tasks including counts, priorities, and project status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="suggest_next_task", 
            description="Suggest the next task to work on based on priorities, due dates, and constraints",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_available_minutes": {
                        "type": "integer",
                        "description": "How many minutes are available for work"
                    },
                    "context_filter": {
                        "type": "string", 
                        "description": "Filter by context (e.g., 'offline', 'low')"
                    },
                    "energy_level": {
                        "type": "string",
                        "description": "Current energy level (high, medium, low)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="show_project_tasks",
            description="Show all tasks for a specific project",
            inputSchema={
                "type": "object", 
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project (without + prefix)"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="show_waiting_tasks",
            description="Show all tasks that are waiting/blocked, organized by project",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }  
        ),
        Tool(
            name="show_inbox_tasks",
            description="Show all inbox tasks that need to be processed",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_context_tasks",
            description="Show tasks filtered by specific context",
            inputSchema={
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "Context to filter by (e.g., 'offline', 'low', 'waiting')"
                    }
                },
                "required": ["context"]
            }
        ),
        Tool(
            name="query_tasks",
            description="Generic query interface for searching tasks by project, context, or task name with flexible filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "Search text to find in task descriptions (partial match, case-insensitive)"
                    },
                    "projects": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by specific projects (e.g., ['work', 'personal']). If empty, include all projects."
                    },
                    "contexts": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Filter by specific contexts (e.g., ['focus', 'offline']). If empty, include all contexts."
                    },
                    "exclude_completed": {
                        "type": "boolean",
                        "description": "Whether to exclude completed tasks (default: true)",
                        "default": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 1000)",
                        "default": 1000
                    }
                },
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    
    if todo_manager is None:
        return [TextContent(type="text", text="Error: Todo manager not initialized")]
    
    if arguments is None:
        arguments = {}
    
    try:
        if name == "get_task_overview":
            result = todo_manager.get_overview()
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "suggest_next_task":
            result = todo_manager.suggest_next_task(
                time_available_minutes=arguments.get("time_available_minutes"),
                context_filter=arguments.get("context_filter"),
                energy_level=arguments.get("energy_level")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "show_project_tasks":
            project_name = arguments["project_name"]
            result = todo_manager.get_project_tasks(project_name)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "show_waiting_tasks":
            result = todo_manager.get_waiting_tasks()
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "show_inbox_tasks":
            result = todo_manager.get_inbox_tasks()
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "show_context_tasks":
            context = arguments["context"]
            result = todo_manager.get_tasks_by_context(context)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        elif name == "query_tasks":
            query_text = arguments.get("query_text", "")
            projects = arguments.get("projects", [])
            contexts = arguments.get("contexts", [])
            exclude_completed = arguments.get("exclude_completed", True)
            max_results = arguments.get("max_results", 1000)
            result = todo_manager.query_tasks(
                query_text=query_text,
                projects=projects,
                contexts=contexts,
                exclude_completed=exclude_completed,
                max_results=max_results
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        else:
            return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

async def main():
    """Main entry point"""
    # Get todo file path from command line or use default
    todo_file = sys.argv[1]
    
    # Initialize todo manager with file path
    init_todo_manager(todo_file)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="todo-assistant",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
