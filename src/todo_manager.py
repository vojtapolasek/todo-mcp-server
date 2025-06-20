"""
High-level todo management with business logic
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from todo_parser import TodoParser

class TodoManager:
    def __init__(self, todo_file: str):
        self.parser = TodoParser(todo_file)
    
    def get_overview(self) -> Dict[str, Any]:
        """Get comprehensive task overview"""
        all_tasks = self.parser.load_all_tasks()
        active_tasks = [t for t in all_tasks if not t['completed']]
        main_tasks = self.parser.filter_tasks(exclude_contexts=['waiting'])
        
        # Priority distribution
        priority_counts = {}
        for task in main_tasks:
            priority = task['priority'] or 'No Priority'
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Project distribution (exclude inbox)
        project_counts = {}
        for task in active_tasks:
            for project in task['projects']:
                if project != 'in':
                    project_counts[project] = project_counts.get(project, 0) + 1
        
        # Due date analysis
        today = datetime.now().strftime('%Y-%m-%d')
        due_today = sum(1 for t in main_tasks if t['due_date'] == today)
        overdue = sum(1 for t in main_tasks if t['due_date'] and t['due_date'] < today)
        
        return {
            'total_tasks': len(all_tasks),
            'active_tasks': len(active_tasks),
            'completed_tasks': len(all_tasks) - len(active_tasks),
            'main_tasks': len(main_tasks),
            'waiting_tasks': len(self.parser.filter_tasks(include_contexts=['waiting'])),
            'inbox_tasks': len([t for t in active_tasks if 'in' in t['projects']]),
            'priority_distribution': priority_counts,
            'top_projects': dict(sorted(project_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'due_today': due_today,
            'overdue': overdue
        }
    
    def suggest_next_task(self, 
                         time_available_minutes: Optional[int] = None,
                         context_filter: Optional[str] = None,
                         energy_level: Optional[str] = None) -> Dict[str, Any]:
        """Suggest next task with reasoning"""
        
        filters = {'exclude_contexts': ['waiting']}
        if context_filter:
            filters['include_contexts'] = [context_filter]
        
        tasks = self.parser.filter_tasks(**filters)
        
        if not tasks:
            return {'error': 'No available tasks found'}
        
        # Simple suggestion logic - take the first (highest priority due date)
        suggested = tasks[0]
        alternatives = tasks[1:4] if len(tasks) > 1 else []
        
        # Build reasoning
        reasons = []
        if suggested['due_date']:
            today = datetime.now().strftime('%Y-%m-%d')
            if suggested['due_date'] <= today:
                reasons.append('Due today or overdue')
            else:
                reasons.append(f"Due {suggested['due_date']}")
        
        if suggested['priority']:
            reasons.append(f"High priority ({suggested['priority']})")
        
        if context_filter:
            reasons.append(f"Matches context: {context_filter}")
        
        if time_available_minutes:
            reasons.append(f"You have {time_available_minutes} minutes available")
        
        if not reasons:
            reasons.append("Next in priority order")
        
        return {
            'suggested_task': suggested,
            'reasoning': '; '.join(reasons),
            'alternatives': alternatives,
            'total_available': len(tasks)
        }
    
    def get_project_tasks(self, project_name: str) -> Dict[str, Any]:
        """Get all tasks for a specific project"""
        active_tasks = self.parser.filter_tasks(include_projects=[project_name])
        waiting_tasks = self.parser.filter_tasks(
            include_projects=[project_name],
            include_contexts=['waiting']
        )
        
        return {
            'project': project_name,
            'active_tasks': active_tasks,
            'waiting_tasks': waiting_tasks,
            'total_count': len(active_tasks) + len(waiting_tasks)
        }
    
    def get_waiting_tasks(self) -> Dict[str, Any]:
        """Get all waiting/blocked tasks organized by project"""
        waiting_tasks = self.parser.filter_tasks(include_contexts=['waiting'])
        
        # Group by project
        by_project = {}
        for task in waiting_tasks:
            projects = task['projects'] if task['projects'] else ['No Project']
            for project in projects:
                if project not in by_project:
                    by_project[project] = []
                by_project[project].append(task)
        
        return {
            'waiting_tasks': waiting_tasks,
            'by_project': by_project,
            'total_count': len(waiting_tasks)
        }
    
    def get_inbox_tasks(self) -> Dict[str, Any]:
        """Get all inbox tasks needing processing"""
        inbox_tasks = self.parser.filter_tasks(include_projects=['in'])
        
        return {
            'inbox_tasks': inbox_tasks,
            'count': len(inbox_tasks),
            'needs_processing': len(inbox_tasks) > 0
        }
    
    def get_tasks_by_context(self, context: str) -> Dict[str, Any]:
        """Get tasks filtered by specific context"""
        tasks = self.parser.filter_tasks(include_contexts=[context])
        
        return {
            'context': context,
            'tasks': tasks,
            'count': len(tasks)
        }