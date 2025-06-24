"""
Todo.txt parser with filtering and sorting capabilities
"""
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class TodoParser:
    def __init__(self, todo_file: str):
        self.todo_file = Path(todo_file)
    
    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse single todo.txt line into structured data"""
        line = line.strip()
        if not line:
            return None
            
        task = {
            'raw': line,
            'completed': line.startswith('x '),
            'priority': None,
            'projects': [],
            'contexts': [],
            'due_date': None,
            'threshold_date': None,
            'recurrence': None,
            'description': self._clean_description(line),
            'creation_date': None,
            'completion_date': None
        }
        
        # Extract completion date and creation date for completed tasks
        if task['completed']:
            # Format: x 2024-01-15 2024-01-10 task description
            date_pattern = r'^x\s+(\d{4}-\d{2}-\d{2})(?:\s+(\d{4}-\d{2}-\d{2}))?'
            match = re.match(date_pattern, line)
            if match:
                task['completion_date'] = match.group(1)
                if match.group(2):
                    task['creation_date'] = match.group(2)
        
        # Extract priority for active tasks
        if not task['completed']:
            priority_match = re.match(r'^(\([A-Z]\))', line)
            if priority_match:
                task['priority'] = priority_match.group(1)[1:-1]
        
# Extract projects (+project) - exclude rec:+1d patterns
                task['projects'] = re.findall(r'(?<!:)\+(\w+)', line)
        
        # Extract contexts (@context)  
        task['contexts'] = re.findall(r'@(\w+)', line)
        
        # Extract due date
        due_match = re.search(r'due:(\d{4}-\d{2}-\d{2})', line)
        if due_match:
            task['due_date'] = due_match.group(1)
            
        # Extract threshold date
        threshold_match = re.search(r't:(\d{4}-\d{2}-\d{2})', line)
        if threshold_match:
            task['threshold_date'] = threshold_match.group(1)
            
        # Extract recurrence
        rec_match = re.search(r'rec:(\+?\w+)', line)
        if rec_match:
            task['recurrence'] = rec_match.group(1)
            
        return task
    
    def _clean_description(self, line: str) -> str:
        """Clean description by removing metadata"""
        # Remove completion marker and dates
        clean = re.sub(r'^x\s+\d{4}-\d{2}-\d{2}(?:\s+\d{4}-\d{2}-\d{2})?\s*', '', line)
        # Remove priority
        clean = re.sub(r'^\([A-Z]\)\s*', '', clean)
        # Remove metadata
        clean = re.sub(r'\s+due:\d{4}-\d{2}-\d{2}', '', clean)
        clean = re.sub(r'\s+t:\d{4}-\d{2}-\d{2}', '', clean)
        clean = re.sub(r'\s+rec:\+?\w+', '', clean)
        return clean.strip()
    
    def load_all_tasks(self) -> List[Dict[str, Any]]:
        """Load and parse all tasks from file"""
        if not self.todo_file.exists():
            return []
            
        try:
            with open(self.todo_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            raise Exception(f"Error reading todo file: {e}")
            
        tasks = []
        for i, line in enumerate(lines):
            task = self.parse_line(line)
            if task:
                task['line_number'] = i + 1
                tasks.append(task)
        return tasks
    
    def filter_tasks(self, 
                    exclude_contexts: List[str] = None, 
                    include_contexts: List[str] = None,
                    exclude_projects: List[str] = None,
                    include_projects: List[str] = None,
                    only_active: bool = True,
                    has_due_date: bool = None) -> List[Dict[str, Any]]:
        """Filter tasks with multiple criteria"""
        exclude_contexts = exclude_contexts or []
        include_contexts = include_contexts or []
        exclude_projects = exclude_projects or []
        include_projects = include_projects or []
        
        tasks = self.load_all_tasks()
        filtered = []
        
        for task in tasks:
            # Skip completed if only_active
            if only_active and task['completed']:
                continue
                
            # Skip active if looking for completed
            if not only_active and not task['completed']:
                continue
                
            # Context filters
            if exclude_contexts and any(ctx in task['contexts'] for ctx in exclude_contexts):
                continue
                
            if include_contexts and not any(ctx in task['contexts'] for ctx in include_contexts):
                continue
                
            # Project filters
            if exclude_projects and any(proj in task['projects'] for proj in exclude_projects):
                continue
                
            if include_projects and not any(proj in task['projects'] for proj in include_projects):
                continue
                
            # Due date filter
            if has_due_date is not None:
                if has_due_date and not task['due_date']:
                    continue
                if not has_due_date and task['due_date']:
                    continue
                
            filtered.append(task)
        
        return self.sort_tasks(filtered)
    
    def sort_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort tasks: due dates first, then by priority (mimicking topydo)"""
        def sort_key(task):
            # Due date first (None goes to end)
            if task['due_date']:
                due_sort = task['due_date']
            else:
                due_sort = 'zzzz-12-31'  # Far future date
            
            # Priority second (A=1, B=2, etc., None=999)
            if task['priority']:
                priority_sort = ord(task['priority']) - ord('A') + 1
            else:
                priority_sort = 999
                
            # Line number as tiebreaker (original order)
            line_sort = task.get('line_number', 999)
                
            return (due_sort, priority_sort, line_sort)
            
        return sorted(tasks, key=sort_key)
