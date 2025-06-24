"""
Test simple MCP server functionality
"""
import pytest
import json
from pathlib import Path
from src.simple_server import simple_server, init_todo_manager

@pytest.fixture
def sample_todo_file():
    return str(Path(__file__).parent / "fixtures" / "sample_todo.txt") 

@pytest.fixture
def initialized_simple_server(sample_todo_file):
    """Initialize simple server with test data"""
    init_todo_manager(sample_todo_file)
    return simple_server

@pytest.mark.asyncio
async def test_list_tools_simple(initialized_simple_server):
    """Test that the simple server has only one tool"""
    from src.simple_server import handle_list_tools
    
    tools = await handle_list_tools()
    
    assert len(tools) == 1
    assert tools[0].name == "get_all_tasks"

@pytest.mark.asyncio
async def test_get_all_tasks_default(initialized_simple_server):
    """Test getting all tasks with default parameters"""
    from src.simple_server import handle_call_tool
    
    result = await handle_call_tool("get_all_tasks", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert 'tasks' in data
    assert 'metadata' in data
    assert data['metadata']['total_returned'] > 0
    
    # Should exclude completed tasks by default
    for task in data['tasks']:
        assert not task['completed']

@pytest.mark.asyncio
async def test_get_all_tasks_include_completed(initialized_simple_server):
    """Test getting all tasks including completed ones"""
    from src.simple_server import handle_call_tool
    
    result = await handle_call_tool("get_all_tasks", {
        "include_completed": True
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    # Should have at least one completed task based on sample data
    completed_tasks = [t for t in data['tasks'] if t['completed']]
    assert len(completed_tasks) >= 1

@pytest.mark.asyncio
async def test_get_all_tasks_filter_by_project(initialized_simple_server):
    """Test filtering tasks by project"""
    from src.simple_server import handle_call_tool
    
    result = await handle_call_tool("get_all_tasks", {
        "include_projects": ["work"]
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    # All returned tasks should have 'work' project
    for task in data['tasks']:
        assert 'work' in task['projects']

@pytest.mark.asyncio
async def test_get_all_tasks_exclude_waiting(initialized_simple_server):
    """Test excluding waiting tasks"""
    from src.simple_server import handle_call_tool
    
    result = await handle_call_tool("get_all_tasks", {
        "exclude_contexts": ["waiting"]
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    # No tasks should have 'waiting' context
    for task in data['tasks']:
        assert 'waiting' not in task['contexts']

@pytest.mark.asyncio
async def test_get_all_tasks_max_results(initialized_simple_server):
    """Test limiting results"""
    from src.simple_server import handle_call_tool
    
    result = await handle_call_tool("get_all_tasks", {
        "max_results": 3
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert data['metadata']['total_returned'] <= 3
    assert len(data['tasks']) <= 3

@pytest.mark.asyncio
async def test_get_all_tasks_with_due_dates_only(initialized_simple_server):
    """Test filtering for tasks with due dates only"""
    from src.simple_server import handle_call_tool
    
    result = await handle_call_tool("get_all_tasks", {
        "has_due_date": True
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    # All returned tasks should have due dates
    for task in data['tasks']:
        assert task['due_date'] is not None

@pytest.mark.asyncio
async def test_metadata_summary(initialized_simple_server):
    """Test that metadata summary is comprehensive"""
    from src.simple_server import handle_call_tool
    
    result = await handle_call_tool("get_all_tasks", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    summary = data['metadata']['summary']
    assert 'task_count' in summary
    assert 'priority_distribution' in summary
    assert 'top_projects' in summary
    assert 'contexts' in summary
    assert 'due_date_info' in summary
