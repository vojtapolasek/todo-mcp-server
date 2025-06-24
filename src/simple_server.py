"""
Simple MCP Server for Todo.txt management - Single Tool Approach
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

# Global todo manager
todo_manager: TodoManager = None

def init_todo_manager(todo_file_path: str):
    """Initialize the todo manager with file path"""
    global todo_manager
    todo_manager = TodoManager(todo_file_path)

# Create server instance
simple_server = Server("todo-assistant-simple")

@simple_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools - just one generic tool"""
    return [
        Tool(
            name="get_all_tasks",
            description="Get all tasks from the todo.txt file with optional filtering. Returns complete task data for LLM analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_completed": {
                        "type": "boolean",
                        "description": "Whether to include completed tasks (default: false)",
                        "default": False
                    },
                    "include_contexts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by specific contexts (e.g., ['offline', 'low']). If empty, include all contexts."
                    },
                    "exclude_contexts": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Exclude specific contexts (e.g., ['waiting']). If empty, exclude nothing."
                    },
                    "include_projects": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by specific projects (e.g., ['work', 'personal']). If empty, include all projects."
                    },
                    "exclude_projects": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Exclude specific projects (e.g., ['in']). If empty, exclude nothing."
                    },
                    "has_due_date": {
                        "type": "boolean",
                        "description": "Filter tasks that have/don't have due dates. If null, include both."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of tasks to return (default: 100)",
                        "default": 100
                    }
                },
                "required": []
            }
        )
    ]

@simple_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    
    if todo_manager is None:
        return [TextContent(type="text", text="Error: Todo manager not initialized")]
    
    if arguments is None:
        arguments = {}
    
    try:
        if name == "get_all_tasks":
            # Extract filtering parameters
            include_completed = arguments.get("include_completed", False)
            include_contexts = arguments.get("include_contexts", [])
            exclude_contexts = arguments.get("exclude_contexts", [])
            include_projects = arguments.get("include_projects", [])
            exclude_projects = arguments.get("exclude_projects", [])
            has_due_date = arguments.get("has_due_date")
            max_results = arguments.get("max_results", 100)
            
            # Get filtered tasks
            tasks = todo_manager.parser.filter_tasks(
                exclude_contexts=exclude_contexts if exclude_contexts else None,
                include_contexts=include_contexts if include_contexts else None,
                exclude_projects=exclude_projects if exclude_projects else None,
                include_projects=include_projects if include_projects else None,
                only_active=not include_completed,
                has_due_date=has_due_date
            )
            
            # Limit results
            if max_results and len(tasks) > max_results:
                tasks = tasks[:max_results]
            
            # Build comprehensive response with metadata
            result = {
                "tasks": tasks,
                "metadata": {
                    "total_returned": len(tasks),
                    "filters_applied": {
                        "include_completed": include_completed,
                        "include_contexts": include_contexts,
                        "exclude_contexts": exclude_contexts,
                        "include_projects": include_projects,
                        "exclude_projects": exclude_projects,
                        "has_due_date": has_due_date,
                        "max_results": max_results
                    },
                    "summary": _get_quick_summary(tasks)
                }
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        else:
            return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

def _get_quick_summary(tasks) -> dict:
    """Generate quick summary statistics for the returned tasks"""
    if not tasks:
        return {"message": "No tasks found"}
    
    # Count by priority
    priority_counts = {}
    for task in tasks:
        priority = task['priority'] or 'No Priority'
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # Count by project (top 10)
    project_counts = {}
    for task in tasks:
        for project in task['projects']:
            project_counts[project] = project_counts.get(project, 0) + 1
    top_projects = dict(sorted(project_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Count by context
    context_counts = {}
    for task in tasks:
        for context in task['contexts']:
            context_counts[context] = context_counts.get(context, 0) + 1
    
    # Due date analysis
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    due_today = sum(1 for t in tasks if t['due_date'] == today)
    overdue = sum(1 for t in tasks if t['due_date'] and t['due_date'] < today)
    with_due_dates = sum(1 for t in tasks if t['due_date'])
    
    return {
        "task_count": len(tasks),
        "priority_distribution": priority_counts,
        "top_projects": top_projects,
        "contexts": context_counts,
        "due_date_info": {
            "with_due_dates": with_due_dates,
            "due_today": due_today,
            "overdue": overdue
        }
    }

async def main():
    """Main entry point for simple server"""
    # Get todo file path from command line or use default
    todo_file = sys.argv[1]
    
    # Initialize todo manager with file path
    init_todo_manager(todo_file)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await simple_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="todo-assistant-simple",
                server_version="0.1.0",
                capabilities=simple_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
