"""
Task query and filtering tools for TickTick MCP.

This module contains MCP tools for querying and filtering tasks
by various criteria such as due dates, priority, and search terms.
"""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from ..config import ensure_client
from ..utils.validators import (
    get_project_tasks_by_filter,
    is_task_due_today,
    is_task_overdue,
    is_task_due_in_days,
    task_matches_search
)

# Set up logging
logger = logging.getLogger(__name__)


def register_query_tools(mcp: FastMCP):
    """Register all query and filtering MCP tools."""
    
    @mcp.tool()
    async def get_all_tasks() -> str:
        """Get all tasks from TickTick. Ignores closed projects."""
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def all_tasks_filter(task: Dict[str, Any]) -> bool:
                return True  # Include all tasks
            
            return get_project_tasks_by_filter(projects, all_tasks_filter, "included", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_all_tasks: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_tasks_by_priority(priority_id: int) -> str:
        """
        Get all tasks from TickTick by priority. Ignores closed projects.

        Args:
            priority_id: Priority level (0: None, 1: Low, 3: Medium, 5: High)
        """
        if priority_id not in [0, 1, 3, 5]:
            return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
        
        priority_names = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
        priority_name = priority_names[priority_id]
        
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def priority_filter(task: Dict[str, Any]) -> bool:
                return task.get('priority', 0) == priority_id
            
            return get_project_tasks_by_filter(projects, priority_filter, f"priority {priority_name}", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_tasks_by_priority: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_tasks_due_today() -> str:
        """Get all tasks from TickTick that are due today. Ignores closed projects."""
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def today_filter(task: Dict[str, Any]) -> bool:
                return is_task_due_today(task)
            
            return get_project_tasks_by_filter(projects, today_filter, "due today", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_tasks_due_today: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_overdue_tasks() -> str:
        """Get all overdue tasks from TickTick. Ignores closed projects."""
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def overdue_filter(task: Dict[str, Any]) -> bool:
                return is_task_overdue(task)
            
            return get_project_tasks_by_filter(projects, overdue_filter, "overdue", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_overdue_tasks: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_tasks_due_tomorrow() -> str:
        """Get all tasks from TickTick that are due tomorrow. Ignores closed projects."""
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def tomorrow_filter(task: Dict[str, Any]) -> bool:
                return is_task_due_in_days(task, 1)
            
            return get_project_tasks_by_filter(projects, tomorrow_filter, "due tomorrow", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_tasks_due_tomorrow: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_tasks_due_in_days(days: int) -> str:
        """
        Get all tasks from TickTick that are due in exactly X days. Ignores closed projects.
        
        Args:
            days: Number of days from today (e.g., 1 for tomorrow, 7 for next week)
        """
        if days < 0:
            return "Days must be a non-negative integer."
        
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def days_filter(task: Dict[str, Any]) -> bool:
                return is_task_due_in_days(task, days)
            
            day_text = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
            return get_project_tasks_by_filter(projects, days_filter, f"due {day_text}", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_tasks_due_in_days: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_tasks_due_this_week() -> str:
        """Get all tasks from TickTick that are due within the next 7 days. Ignores closed projects."""
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def week_filter(task: Dict[str, Any]) -> bool:
                # Check if task is due within the next 7 days (0-6 days from today)
                for day in range(7):
                    if is_task_due_in_days(task, day):
                        return True
                return False
            
            return get_project_tasks_by_filter(projects, week_filter, "due this week", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_tasks_due_this_week: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def search_tasks(search_term: str) -> str:
        """
        Search for tasks in TickTick by title, content, or subtask titles. Ignores closed projects.
        
        Args:
            search_term: Text to search for (case-insensitive)
        """
        if not search_term.strip():
            return "Search term cannot be empty."
        
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def search_filter(task: Dict[str, Any]) -> bool:
                return task_matches_search(task, search_term)
            
            return get_project_tasks_by_filter(projects, search_filter, f"matching '{search_term}'", ticktick)
            
        except Exception as e:
            logger.error(f"Error in search_tasks: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_engaged_tasks() -> str:
        """
        Get all tasks from TickTick that are "Engaged".
        This includes tasks marked as high priority (5), due today or overdue.
        """
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def engaged_filter(task: Dict[str, Any]) -> bool:
                # High priority tasks
                if task.get('priority', 0) == 5:
                    return True
                # Tasks due today
                if is_task_due_today(task):
                    return True
                # Overdue tasks
                if is_task_overdue(task):
                    return True
                return False
            
            return get_project_tasks_by_filter(projects, engaged_filter, "engaged (high priority, due today, or overdue)", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_engaged_tasks: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_next_tasks() -> str:
        """
        Get all tasks from TickTick that are "Next".
        This includes tasks marked as medium priority (3) or due tomorrow.
        """
        try:
            ticktick = ensure_client()
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            def next_filter(task: Dict[str, Any]) -> bool:
                # Medium priority tasks
                if task.get('priority', 0) == 3:
                    return True
                # Tasks due tomorrow
                if is_task_due_in_days(task, 1):
                    return True
                return False
            
            return get_project_tasks_by_filter(projects, next_filter, "next (medium priority or due tomorrow)", ticktick)
            
        except Exception as e:
            logger.error(f"Error in get_next_tasks: {e}")
            return f"Error retrieving projects: {str(e)}"
