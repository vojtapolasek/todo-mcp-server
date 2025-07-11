"""
Test query tool functionality
"""
import pytest
import json
from pathlib import Path
from todo_manager import TodoManager

@pytest.fixture
def sample_todo_file():
    return str(Path(__file__).parent / "fixtures" / "sample_todo.txt")

@pytest.fixture
def manager(sample_todo_file):
    return TodoManager(sample_todo_file)

def test_query_by_text(manager):
    """Test querying tasks by text search"""
    result = manager.query_tasks(query_text="review")
    
    assert result['results_info']['search_applied'] == True
    assert result['results_info']['total_returned'] > 0
    
    # All returned tasks should contain "review" somewhere
    for task in result['tasks']:
        task_text = task['raw'].lower()
        assert 'review' in task_text

def test_query_by_project(manager):
    """Test querying tasks by project"""
    result = manager.query_tasks(projects=["work"])
    
    assert result['query_info']['projects_filter'] == ["work"]
    assert result['results_info']['total_returned'] > 0
    
    # All returned tasks should have 'work' project
    for task in result['tasks']:
        assert 'work' in task['projects']

def test_query_by_context(manager):
    """Test querying tasks by context"""
    result = manager.query_tasks(contexts=["quick"])
    
    assert result['query_info']['contexts_filter'] == ["quick"]
    assert result['results_info']['total_returned'] > 0
    
    # All returned tasks should have 'quick' context
    for task in result['tasks']:
        assert 'quick' in task['contexts']

def test_combined_query(manager):
    """Test combined text and filter query"""
    result = manager.query_tasks(
        query_text="team",
        projects=["work"],
        max_results=5
    )
    
    assert result['query_info']['query_text'] == "team"
    assert result['query_info']['projects_filter'] == ["work"]
    assert result['results_info']['total_returned'] <= 5

def test_max_results_limit(manager):
    """Test that max_results limit works"""
    result = manager.query_tasks(max_results=3)
    
    assert result['results_info']['total_returned'] <= 3
    assert len(result['tasks']) <= 3

def test_include_completed_tasks(manager):
    """Test including completed tasks"""
    result = manager.query_tasks(exclude_completed=False)
    
    assert result['query_info']['exclude_completed'] == False
    # Should have at least one completed task based on sample data
    completed_tasks = [t for t in result['tasks'] if t['completed']]
    assert len(completed_tasks) >= 1

def test_empty_query(manager):
    """Test query with no filters returns all active tasks"""
    result = manager.query_tasks()
    
    assert result['query_info']['query_text'] == ""
    assert result['results_info']['search_applied'] == False
    assert result['results_info']['total_returned'] > 0