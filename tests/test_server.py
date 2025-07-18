"""
Test MCP server functionality - corrected version
"""
import pytest
import json
from pathlib import Path
from server import server, init_todo_manager

@pytest.fixture
def sample_todo_file():
    return str(Path(__file__).parent / "fixtures" / "sample_todo.txt") 

@pytest.fixture
def initialized_server(sample_todo_file):
    """Initialize server with test data"""
    init_todo_manager(sample_todo_file)
    return server

@pytest.mark.asyncio
async def test_list_tools(initialized_server):
    """Test that all expected tools are listed"""
    # Call the handler function directly
    from server import handle_list_tools
    
    tools = await handle_list_tools()
    
    tool_names = [tool.name for tool in tools]
    expected_tools = [
        "get_task_overview",
        "suggest_next_task", 
        "show_project_tasks",
        "show_waiting_tasks",
        "show_inbox_tasks",
        "show_context_tasks",
        "query_tasks"
    ]
    
    for expected in expected_tools:
        assert expected in tool_names
    
    # Verify we have the right number of tools
    assert len(tools) == len(expected_tools)


@pytest.mark.asyncio
async def test_get_task_overview(initialized_server):
    """Test task overview tool"""
    # Import and call the handler directly
    from server import handle_call_tool
    
    result = await handle_call_tool("get_task_overview", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert 'total_tasks' in data
    assert 'active_tasks' in data
    assert 'priority_distribution' in data
    assert data['total_tasks'] > 0

@pytest.mark.asyncio
async def test_suggest_next_task(initialized_server):
    """Test task suggestion"""
    from server import handle_call_tool
    
    result = await handle_call_tool("suggest_next_task", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert 'suggested_task' in data
    assert 'reasoning' in data
    assert 'alternatives' in data

@pytest.mark.asyncio  
async def test_suggest_next_task_with_time(initialized_server):
    """Test task suggestion with time constraint"""
    from server import handle_call_tool
    
    result = await handle_call_tool("suggest_next_task", {
        "time_available_minutes": 30
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert 'You have 30 minutes available' in data['reasoning']

@pytest.mark.asyncio
async def test_show_project_tasks(initialized_server):
    """Test showing tasks for specific project"""
    from server import handle_call_tool
    
    result = await handle_call_tool("show_project_tasks", {
        "project_name": "work"
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert data['project'] == 'work'
    assert 'active_tasks' in data
    assert 'waiting_tasks' in data

@pytest.mark.asyncio
async def test_show_inbox_tasks(initialized_server):
    """Test showing inbox tasks"""
    from server import handle_call_tool
    
    result = await handle_call_tool("show_inbox_tasks", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert 'inbox_tasks' in data
    assert 'count' in data
    assert data['count'] == 2  # Based on sample data

@pytest.mark.asyncio
async def test_show_waiting_tasks(initialized_server):
    """Test showing waiting tasks"""
    from server import handle_call_tool
    
    result = await handle_call_tool("show_waiting_tasks", {})
    
    assert len(result) == 1  
    data = json.loads(result[0].text)
    
    assert 'waiting_tasks' in data
    assert 'by_project' in data

@pytest.mark.asyncio
async def test_show_context_tasks(initialized_server):
    """Test showing tasks by context"""
    from server import handle_call_tool
    
    result = await handle_call_tool("show_context_tasks", {
        "context": "offline"
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert data['context'] == 'offline'
    assert 'tasks' in data
    assert 'count' in data

@pytest.mark.asyncio
async def test_invalid_tool_name(initialized_server):
    """Test calling non-existent tool"""
    from server import handle_call_tool
    
    result = await handle_call_tool("invalid_tool", {})
    
    assert len(result) == 1
    assert "Unknown tool" in result[0].text

@pytest.mark.asyncio  
async def test_missing_required_argument(initialized_server):
    """Test calling tool without required argument"""
    from server import handle_call_tool
    
    result = await handle_call_tool("show_project_tasks", {})
    

@pytest.mark.asyncio
async def test_query_tasks(initialized_server):
    """Test generic query tasks tool"""
    from server import handle_call_tool
    
    result = await handle_call_tool("query_tasks", {
        "query_text": "review",
        "projects": ["work"],
        "max_results": 10
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    
    assert 'tasks' in data
    assert 'query_info' in data
    assert 'results_info' in data
    assert data['query_info']['query_text'] == "review"
    assert data['query_info']['projects_filter'] == ["work"]
    assert data['results_info']['total_returned'] <= 10
