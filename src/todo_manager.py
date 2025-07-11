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
        
        # Define energy and time context mappings
        ENERGY_CONTEXTS = {
            'high': ['focus', 'creative', 'complex', 'brainstorm', 'learn'],
            'medium': ['medium'],  # Neutral tasks
            'low': ['routine', 'admin', 'communicate', 'organize', 'review']
        }
        
        TIME_CONTEXTS = {
            'quick': ['quick', 'call', 'email'],        # ≤15 min
            'medium': ['medium', 'meeting'],             # 15-60 min  
            'long': ['deep', 'project']                  # >60 min
        }
        
        filters = {'exclude_contexts': ['waiting']}
        if context_filter:
            filters['include_contexts'] = [context_filter]
        
        tasks = self.parser.filter_tasks(**filters)
        
        if not tasks:
            return {'error': 'No available tasks found'}
        
        candidate_tasks = tasks
        filtering_reasons = []
        
        # Filter by energy level
        if energy_level and energy_level in ENERGY_CONTEXTS:
            energy_tasks = [task for task in candidate_tasks 
                        if any(ctx in ENERGY_CONTEXTS[energy_level] 
                                for ctx in task['contexts'])]
            if energy_tasks:
                candidate_tasks = energy_tasks
                filtering_reasons.append(f"filtered for {energy_level} energy tasks")
        
        # Filter by time available
        if time_available_minutes:
            target_time_category = None
            if time_available_minutes <= 15:
                target_time_category = 'quick'
            elif time_available_minutes <= 60:
                target_time_category = 'medium'
            else:
                target_time_category = 'long'
            
            time_tasks = [task for task in candidate_tasks 
                        if any(ctx in TIME_CONTEXTS[target_time_category] 
                            for ctx in task['contexts'])]
            if time_tasks:
                candidate_tasks = time_tasks
                filtering_reasons.append(f"filtered for {target_time_category} duration tasks")
        
        # Fallback: if no tasks match energy/time filters, use original list
        if not candidate_tasks:
            candidate_tasks = tasks
            filtering_reasons.append("no tasks matched filters, showing all available")
        
        # Select the best candidate
        suggested = candidate_tasks[0]
        alternatives = candidate_tasks[1:4] if len(candidate_tasks) > 1 else []
        
        # Build reasoning
        reasons = []
        if suggested['due_date']:
            today = datetime.now().strftime('%Y-%m-%d')
            if suggested['due_date'] <= today:
                reasons.append('Due today or overdue')
            else:
                reasons.append(f"Due {suggested['due_date']}")
        
        if suggested['priority']:
            reasons.append(f"Priority {suggested['priority']}")
        
        if context_filter:
            reasons.append(f"Matches context {context_filter}")
        
        # Add time available to reasoning
        if time_available_minutes:
            reasons.append(f"You have {time_available_minutes} minutes available")
        
        # Add filtering reasons
        if filtering_reasons:
            reasons.extend(filtering_reasons)
        
        if not reasons:
            reasons.append("Next in priority order")
        
        return {
            'suggested_task': suggested,
            'reasoning': '; '.join(reasons),
            'alternatives': alternatives,
            'total_available': len(tasks),
            'filtered_candidates': len(candidate_tasks)
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

    def query_tasks(self, 
                   query_text: str = "",
                   projects: List[str] = None,
                   contexts: List[str] = None,
                   exclude_completed: bool = True,
                   max_results: int = 20) -> Dict[str, Any]:
        """Generic query interface for searching tasks"""
        
        # Start with base filtering
        filters = {
            'only_active': exclude_completed
        }
        
        # Apply project and context filters if provided
        if projects:
            filters['include_projects'] = projects
        if contexts:
            filters['include_contexts'] = contexts
            
        # Get filtered tasks
        tasks = self.parser.filter_tasks(**filters)
        
        # Apply text search if query_text is provided
        if query_text:
            query_lower = query_text.lower()
            matching_tasks = []
            
            for task in tasks:
                # Search in description (cleaned task text)
                if query_lower in task['description'].lower():
                    matching_tasks.append(task)
                    continue
                
                # Search in raw task text
                if query_lower in task['raw'].lower():
                    matching_tasks.append(task)
                    continue
                    
                # Search in projects
                if any(query_lower in proj.lower() for proj in task['projects']):
                    matching_tasks.append(task)
                    continue
                    
                # Search in contexts
                if any(query_lower in ctx.lower() for ctx in task['contexts']):
                    matching_tasks.append(task)
                    continue
                    
            tasks = matching_tasks
        
        # Limit results
        if max_results and len(tasks) > max_results:
            tasks = tasks[:max_results]
            truncated = True
        else:
            truncated = False
        
        # Build response with metadata
        return {
            'tasks': tasks,
            'query_info': {
                'query_text': query_text,
                'projects_filter': projects or [],
                'contexts_filter': contexts or [],
                'exclude_completed': exclude_completed,
                'max_results': max_results
            },
            'results_info': {
                'total_returned': len(tasks),
                'truncated': truncated,
                'search_applied': bool(query_text)
            }
        }