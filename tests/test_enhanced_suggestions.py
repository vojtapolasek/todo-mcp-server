"""
Test enhanced task suggestion functionality with energy and time contexts
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

def test_suggest_high_energy_tasks(manager):
    """Test suggesting tasks for high energy level"""
    result = manager.suggest_next_task(energy_level="high")
    
    suggested_task = result['suggested_task']
    
    # Should suggest a task with high energy contexts
    high_energy_contexts = ['focus', 'creative', 'complex', 'brainstorm', 'learn']
    task_contexts = suggested_task['contexts']
    
    assert any(ctx in high_energy_contexts for ctx in task_contexts), \
        f"Expected high energy context in {task_contexts}"
    
    assert 'filtered for high energy tasks' in result['reasoning']
    assert result['filtered_candidates'] < result['total_available']

def test_suggest_low_energy_tasks(manager):
    """Test suggesting tasks for low energy level"""
    result = manager.suggest_next_task(energy_level="low")
    
    suggested_task = result['suggested_task']
    
    # Should suggest a task with low energy contexts
    low_energy_contexts = ['routine', 'admin', 'communicate', 'organize', 'review']
    task_contexts = suggested_task['contexts']
    
    assert any(ctx in low_energy_contexts for ctx in task_contexts), \
        f"Expected low energy context in {task_contexts}"
    
    assert 'filtered for low energy tasks' in result['reasoning']

def test_suggest_quick_tasks(manager):
    """Test suggesting tasks for short time availability"""
    result = manager.suggest_next_task(time_available_minutes=10)
    
    suggested_task = result['suggested_task']
    
    # Should suggest a task with quick time contexts
    quick_contexts = ['quick', 'call', 'email']
    task_contexts = suggested_task['contexts']
    
    assert any(ctx in quick_contexts for ctx in task_contexts), \
        f"Expected quick context in {task_contexts}"
    
    assert 'filtered for quick duration tasks' in result['reasoning']

def test_suggest_medium_time_tasks(manager):
    """Test suggesting tasks for medium time availability"""
    result = manager.suggest_next_task(time_available_minutes=45)
    
    suggested_task = result['suggested_task']
    
    # Should suggest a task with medium time contexts or allow others
    medium_contexts = ['medium', 'meeting']
    quick_contexts = ['quick', 'call', 'email']
    task_contexts = suggested_task['contexts']
    
    # Should prefer medium or allow quick tasks
    has_suitable_context = (any(ctx in medium_contexts for ctx in task_contexts) or
                           any(ctx in quick_contexts for ctx in task_contexts))
    
    assert has_suitable_context, f"Expected medium or quick context in {task_contexts}"

def test_suggest_long_time_tasks(manager):
    """Test suggesting tasks for long time availability"""
    result = manager.suggest_next_task(time_available_minutes=120)
    
    suggested_task = result['suggested_task']
    
    # Should suggest a task with long time contexts
    long_contexts = ['deep', 'project']
    task_contexts = suggested_task['contexts']
    
    assert any(ctx in long_contexts for ctx in task_contexts), \
        f"Expected deep work context in {task_contexts}"
    
    assert 'filtered for long duration tasks' in result['reasoning']

def test_combined_energy_and_time_filtering(manager):
    """Test combining energy level and time constraints"""
    result = manager.suggest_next_task(
        energy_level="low", 
        time_available_minutes=15
    )
    
    suggested_task = result['suggested_task']
    task_contexts = suggested_task['contexts']
    
    # Should have both low energy and quick contexts
    low_energy_contexts = ['routine', 'admin', 'communicate', 'organize', 'review']
    quick_contexts = ['quick', 'call', 'email']
    
    has_low_energy = any(ctx in low_energy_contexts for ctx in task_contexts)
    has_quick_time = any(ctx in quick_contexts for ctx in task_contexts)
    
    # At minimum should have one of the constraints satisfied
    assert has_low_energy or has_quick_time, \
        f"Expected low energy or quick context in {task_contexts}"
    
    reasoning = result['reasoning']
    assert ('filtered for low energy tasks' in reasoning or 
            'filtered for quick duration tasks' in reasoning)

def test_no_matching_contexts_fallback(manager):
    """Test fallback when no tasks match the energy/time criteria"""
    # Try to find high energy tasks when most are routine
    # This should fall back to showing all available tasks
    result = manager.suggest_next_task(energy_level="high", time_available_minutes=5)
    
    # Should still return a task (fallback behavior)
    assert 'suggested_task' in result
    assert result['total_available'] > 0
    
    # If no perfect matches, should mention fallback or show what was found
    assert result['filtered_candidates'] >= 0

def test_context_filtering_with_existing_context_filter(manager):
    """Test that energy/time filtering works with existing context filters"""
    result = manager.suggest_next_task(
        context_filter="offline",
        energy_level="high",
        time_available_minutes=90
    )
    
    suggested_task = result['suggested_task']
    
    # Should have the original context filter
    assert 'offline' in suggested_task['contexts']
    
    # Should also consider energy/time if possible
    reasoning = result['reasoning']
    assert 'Matches context offline' in reasoning

def test_energy_level_invalid(manager):
    """Test behavior with invalid energy level"""
    result = manager.suggest_next_task(energy_level="invalid")
    
    # Should still work, just ignore the invalid energy level
    assert 'suggested_task' in result
    assert result['total_available'] > 0

@pytest.mark.parametrize("energy_level,expected_contexts", [
    ("high", ['focus', 'creative', 'brainstorm', 'learn']),
    ("low", ['routine', 'admin', 'organize']),
])
def test_energy_level_context_mapping(manager, energy_level, expected_contexts):
    """Test that different energy levels map to correct context types"""
    result = manager.suggest_next_task(energy_level=energy_level)
    
    if result['filtered_candidates'] > 0:  # Only test if filtering found something
        suggested_task = result['suggested_task']
        task_contexts = suggested_task['contexts']
        
        has_expected = any(ctx in expected_contexts for ctx in task_contexts)
        assert has_expected, \
            f"Expected one of {expected_contexts} in {task_contexts} for {energy_level} energy"

@pytest.mark.parametrize("time_minutes,expected_category", [
    (5, "quick"),
    (15, "quick"), 
    (30, "medium"),
    (60, "medium"),
    (90, "long"),
    (180, "long"),
])
def test_time_duration_categorization(manager, time_minutes, expected_category):
    """Test that different time durations get categorized correctly"""
    result = manager.suggest_next_task(time_available_minutes=time_minutes)
    
    reasoning = result['reasoning']
    
    if result['filtered_candidates'] < result['total_available']:
        # Filtering occurred, check the category
        assert f"filtered for {expected_category} duration tasks" in reasoning