"""
Task CRUD tools for TickTick MCP.

This module contains MCP tools for creating, reading, updating, and deleting tasks,
including batch operations and subtask management.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from ..config import ensure_client
from ..utils.formatters import format_task
from ..utils.timezone import normalize_iso_date
from ..utils.validators import validate_task_data

# Set up logging
logger = logging.getLogger(__name__)


def register_task_tools(mcp: FastMCP):
    """Register all task-related MCP tools."""
    
    @mcp.tool()
    async def get_task(project_id: str, task_id: str) -> str:
        """
        Get details about a specific task.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
        """
        try:
            ticktick = ensure_client()
            task = ticktick.get_task(project_id, task_id)
            if 'error' in task:
                return f"Error fetching task: {task['error']}"
            
            return format_task(task)
        except Exception as e:
            logger.error(f"Error in get_task: {e}")
            return f"Error retrieving task: {str(e)}"

    @mcp.tool()
    async def create_task(
        title: str, 
        project_id: str, 
        content: str = None, 
        desc: str = None,
        start_date: str = None, 
        due_date: str = None, 
        priority: int = 0,
        is_all_day: bool = False,
        time_zone: str = None,
        reminders: List[str] = None,
        repeat_flag: str = None,
        sort_order: int = None,
        items: List[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new task in TickTick.
        
        Args:
            title: Task title
            project_id: ID of the project to add the task to
            content: Task description/content (optional)
            desc: Description of checklist (optional)
            start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
            is_all_day: Whether this is an all-day task (optional, default: False)
            time_zone: Time zone (e.g., "America/Los_Angeles") (optional)
            reminders: List of reminder triggers (e.g., ["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"]) (optional)
            repeat_flag: Recurring rules (e.g., "RRULE:FREQ=DAILY;INTERVAL=1") (optional)
            sort_order: Sort order value (optional)
            items: List of subtask dictionaries (optional)
        """
        # Validate priority
        if priority not in [0, 1, 3, 5]:
            return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
        
        try:
            # Validate dates if provided
            for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
                if date_str:
                    try:
                        # Try to parse the date to validate it
                        normalized_date = normalize_iso_date(date_str)
                        datetime.fromisoformat(normalized_date)
                    except ValueError:
                        return f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
            
            ticktick = ensure_client()
            task = ticktick.create_task(
                title=title,
                project_id=project_id,
                content=content,
                desc=desc,
                start_date=start_date,
                due_date=due_date,
                priority=priority,
                is_all_day=is_all_day,
                time_zone=time_zone,
                reminders=reminders,
                repeat_flag=repeat_flag,
                sort_order=sort_order,
                items=items
            )
            
            if 'error' in task:
                return f"Error creating task: {task['error']}"
            
            return f"Task created successfully:\n\n" + format_task(task)
        except Exception as e:
            logger.error(f"Error in create_task: {e}")
            return f"Error creating task: {str(e)}"

    @mcp.tool()
    async def update_task(
        task_id: str,
        project_id: str,
        title: str = None,
        content: str = None,
        desc: str = None,
        start_date: str = None,
        due_date: str = None,
        priority: int = None,
        is_all_day: bool = None,
        time_zone: str = None,
        reminders: List[str] = None,
        repeat_flag: str = None,
        sort_order: int = None,
        items: List[Dict[str, Any]] = None
    ) -> str:
        """
        Update an existing task in TickTick.
        
        Args:
            task_id: ID of the task to update
            project_id: ID of the project the task belongs to
            title: New task title (optional)
            content: New task description/content (optional)
            desc: New description of checklist (optional)
            start_date: New start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            due_date: New due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            priority: New priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
            is_all_day: Whether this is an all-day task (optional)
            time_zone: Time zone (e.g., "America/Los_Angeles") (optional)
            reminders: List of reminder triggers (e.g., ["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"]) (optional)
            repeat_flag: Recurring rules (e.g., "RRULE:FREQ=DAILY;INTERVAL=1") (optional)
            sort_order: Sort order value (optional)
            items: List of subtask dictionaries (optional)
        """
        # Validate priority if provided
        if priority is not None and priority not in [0, 1, 3, 5]:
            return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
        
        try:
            # Validate dates if provided
            for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
                if date_str:
                    try:
                        # Try to parse the date to validate it
                        normalized_date = normalize_iso_date(date_str)
                        datetime.fromisoformat(normalized_date)
                    except ValueError:
                        return f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
            
            ticktick = ensure_client()
            task = ticktick.update_task(
                task_id=task_id,
                project_id=project_id,
                title=title,
                content=content,
                desc=desc,
                start_date=start_date,
                due_date=due_date,
                priority=priority,
                is_all_day=is_all_day,
                time_zone=time_zone,
                reminders=reminders,
                repeat_flag=repeat_flag,
                sort_order=sort_order,
                items=items
            )
            
            if 'error' in task:
                return f"Error updating task: {task['error']}"
            
            return f"Task updated successfully:\n\n" + format_task(task)
        except Exception as e:
            logger.error(f"Error in update_task: {e}")
            return f"Error updating task: {str(e)}"

    @mcp.tool()
    async def complete_task(project_id: str, task_id: str) -> str:
        """
        Mark a task as complete.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
        """
        try:
            ticktick = ensure_client()
            result = ticktick.complete_task(project_id, task_id)
            if 'error' in result:
                return f"Error completing task: {result['error']}"
            
            return f"Task {task_id} marked as complete."
        except Exception as e:
            logger.error(f"Error in complete_task: {e}")
            return f"Error completing task: {str(e)}"

    @mcp.tool()
    async def delete_task(project_id: str, task_id: str) -> str:
        """
        Delete a task.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
        """
        try:
            ticktick = ensure_client()
            result = ticktick.delete_task(project_id, task_id)
            if 'error' in result:
                return f"Error deleting task: {result['error']}"
            
            return f"Task {task_id} deleted successfully."
        except Exception as e:
            logger.error(f"Error in delete_task: {e}")
            return f"Error deleting task: {str(e)}"

    @mcp.tool()
    async def create_subtask(
        subtask_title: str,
        parent_task_id: str,
        project_id: str,
        content: str = None,
        priority: int = 0
    ) -> str:
        """
        Create a subtask for a parent task within the same project.
        
        Args:
            subtask_title: Title of the subtask
            parent_task_id: ID of the parent task
            project_id: ID of the project (must be same for both parent and subtask)
            content: Optional content/description for the subtask
            priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        """
        # Validate priority
        if priority not in [0, 1, 3, 5]:
            return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
        
        try:
            ticktick = ensure_client()
            subtask = ticktick.create_subtask(
                subtask_title=subtask_title,
                parent_task_id=parent_task_id,
                project_id=project_id,
                content=content,
                priority=priority
            )
            
            if 'error' in subtask:
                return f"Error creating subtask: {subtask['error']}"
            
            return f"Subtask created successfully:\n\n" + format_task(subtask)
        except Exception as e:
            logger.error(f"Error in create_subtask: {e}")
            return f"Error creating subtask: {str(e)}"

    @mcp.tool()
    async def batch_create_tasks(tasks: List[Dict[str, Any]]) -> str:
        """
        Create multiple tasks in TickTick at once
        
        Args:
            tasks: List of task dictionaries. Each task must contain:
                - title (required): Task Name
                - project_id (required): ID of the project for the task
                - content (optional): Task description
                - desc (optional): Description of checklist
                - start_date (optional): Start date in ISO format (YYYY-MM-DDTHH:mm:ss+0000)
                - due_date (optional): Due date in ISO format (YYYY-MM-DDTHH:mm:ss+0000)
                - priority (optional): Priority level {0: "None", 1: "Low", 3: "Medium", 5: "High"}
                - is_all_day (optional): Whether this is an all-day task (boolean)
                - time_zone (optional): Time zone (e.g., "America/Los_Angeles")
                - reminders (optional): List of reminder triggers (e.g., ["TRIGGER:P0DT9H0M0S"])
                - repeat_flag (optional): Recurring rules (e.g., "RRULE:FREQ=DAILY;INTERVAL=1")
                - sort_order (optional): Sort order value (integer)
                - items (optional): List of subtask dictionaries
        
        Example:
            tasks = [
                {"title": "Example A", "project_id": "1234ABC", "priority": 5, "is_all_day": True},
                {"title": "Example B", "project_id": "1234XYZ", "content": "Description", "due_date": "2025-07-19T10:00:00+0000", "time_zone": "America/Los_Angeles"}
            ]
        """
        if not tasks:
            return "No tasks provided. Please provide a list of tasks to create."
        
        if not isinstance(tasks, list):
            return "Tasks must be provided as a list of dictionaries."
        
        # Validate all tasks before creating any
        validation_errors = []
        for i, task_data in enumerate(tasks):
            if not isinstance(task_data, dict):
                validation_errors.append(f"Task {i + 1}: Must be a dictionary")
                continue
            
            error = validate_task_data(task_data, i)
            if error:
                validation_errors.append(error)
        
        if validation_errors:
            return "Validation errors found:\n" + "\n".join(validation_errors)
        
        # Create tasks one by one and collect results
        created_tasks = []
        failed_tasks = []
        
        try:
            ticktick = ensure_client()
            for i, task_data in enumerate(tasks):
                try:
                    # Extract task parameters with defaults
                    title = task_data['title']
                    project_id = task_data['project_id']
                    content = task_data.get('content')
                    desc = task_data.get('desc')
                    start_date = task_data.get('start_date')
                    due_date = task_data.get('due_date')
                    priority = task_data.get('priority', 0)
                    is_all_day = task_data.get('is_all_day', False)
                    time_zone = task_data.get('time_zone')
                    reminders = task_data.get('reminders')
                    repeat_flag = task_data.get('repeat_flag')
                    sort_order = task_data.get('sort_order')
                    items = task_data.get('items')
                    
                    # Create the task
                    result = ticktick.create_task(
                        title=title,
                        project_id=project_id,
                        content=content,
                        desc=desc,
                        start_date=start_date,
                        due_date=due_date,
                        priority=priority,
                        is_all_day=is_all_day,
                        time_zone=time_zone,
                        reminders=reminders,
                        repeat_flag=repeat_flag,
                        sort_order=sort_order,
                        items=items
                    )
                    
                    if 'error' in result:
                        failed_tasks.append(f"Task {i + 1} ('{title}'): {result['error']}")
                    else:
                        created_tasks.append((i + 1, title, result))
                        
                except Exception as e:
                    failed_tasks.append(f"Task {i + 1} ('{task_data.get('title', 'Unknown')}'): {str(e)}")
            
            # Format the results
            result_message = f"Batch task creation completed.\n\n"
            result_message += f"Successfully created: {len(created_tasks)} tasks\n"
            result_message += f"Failed: {len(failed_tasks)} tasks\n\n"
            
            if created_tasks:
                result_message += "✅ Successfully Created Tasks:\n"
                for task_num, title, task_obj in created_tasks:
                    result_message += f"{task_num}. {title} (ID: {task_obj.get('id', 'Unknown')})\n"
                result_message += "\n"
            
            if failed_tasks:
                result_message += "❌ Failed Tasks:\n"
                for error in failed_tasks:
                    result_message += f"{error}\n"
            
            return result_message
            
        except Exception as e:
            logger.error(f"Error in batch_create_tasks: {e}")
            return f"Error during batch task creation: {str(e)}"
