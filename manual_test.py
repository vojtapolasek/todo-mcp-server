#!/usr/bin/env python3
"""
Manual test script for the MCP server
"""
import asyncio
import json
from src.server import init_todo_manager
from src.todo_manager import TodoManager

async def test_manually():
    # Use your actual todo file or test fixture
    todo_file = "tests/fixtures/sample_todo.txt"
    
    print("Initializing todo manager...")
    manager = TodoManager(todo_file)
    
    print("\n=== Task Overview ===")
    overview = manager.get_overview()
    print(json.dumps(overview, indent=2))
    
    print("\n=== Next Task Suggestion ===")  
    suggestion = manager.suggest_next_task(time_available_minutes=30)
    print(json.dumps(suggestion, indent=2))
    
    print("\n=== Inbox Tasks ===")
    inbox = manager.get_inbox_tasks()
    print(json.dumps(inbox, indent=2))
    
    print("\n=== Waiting Tasks ===")
    waiting = manager.get_waiting_tasks() 
    print(json.dumps(waiting, indent=2))

if __name__ == "__main__":
    asyncio.run(test_manually())
