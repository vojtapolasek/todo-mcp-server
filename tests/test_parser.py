"""
Test todo parser functionality
"""
import pytest
from pathlib import Path
from todo_parser import TodoParser

@pytest.fixture
def sample_todo_file():
    return Path(__file__).parent / "fixtures" / "sample_todo.txt"

@pytest.fixture 
def parser(sample_todo_file):
    return TodoParser(str(sample_todo_file))

def test_parse_priority_task(parser):
    """Test parsing task with priority"""
    task = parser.parse_line("(A) review quarterly reports due:2024-12-23 +work")
    
    assert task['priority'] == 'A'
    assert task['due_date'] == '2024-12-23'
    assert 'work' in task['projects']
    assert not task['completed']
    assert 'review quarterly reports' in task['description']

def test_parse_completed_task(parser):
    """Test parsing completed task"""
    task = parser.parse_line("x 2024-12-20 2024-12-19 completed example task")
    
    assert task['completed'] == True
    assert task['completion_date'] == '2024-12-20'
    assert task['creation_date'] == '2024-12-19'
    assert 'completed example task' in task['description']

def test_parse_waiting_context(parser):
    """Test parsing task with waiting context"""
    task = parser.parse_line("finish code review for PR #123 +development @waiting")
    
    assert 'waiting' in task['contexts']
    assert 'development' in task['projects']
    assert task['priority'] is None

def test_filter_exclude_waiting(parser):
    """Test filtering out waiting tasks"""
    tasks = parser.filter_tasks(exclude_contexts=['waiting'])
    
    # Should not contain the waiting task
    waiting_tasks = [t for t in tasks if 'waiting' in t['contexts']]
    assert len(waiting_tasks) == 0

def test_filter_include_inbox(parser):
    """Test filtering for inbox tasks only"""
    tasks = parser.filter_tasks(include_projects=['in'])
    
    # All tasks should have 'in' project
    for task in tasks:
        assert 'in' in task['projects']
    
    assert len(tasks) == 2  # Based on sample data

def test_task_sorting(parser):
    """Test that tasks are sorted correctly"""
    tasks = parser.filter_tasks(exclude_contexts=['waiting'])
    
    # Tasks should be sorted: due dates first, then by priority
    # The first task should be the one with earliest due date
    # Based on sample data: (C) backup laptop due:2024-12-20 comes first
    first_task = tasks[0]
    assert first_task['priority'] == 'C'
    assert first_task['due_date'] == '2024-12-20'
    
    # The second task should be (A) review quarterly reports due:2024-12-23  
    if len(tasks) > 1:
        second_task = tasks[1]
        assert second_task['priority'] == 'A'
        assert second_task['due_date'] == '2024-12-23'


def test_project_filtering(parser):
    """Test filtering by specific project"""
    work_tasks = parser.filter_tasks(include_projects=['work'])
    
    for task in work_tasks:
        assert 'work' in task['projects']
    
    assert len(work_tasks) > 0

def test_offline_context_filtering(parser):
    """Test filtering by offline context"""  
    offline_tasks = parser.filter_tasks(include_contexts=['offline'])
    
    for task in offline_tasks:
        assert 'offline' in task['contexts']
