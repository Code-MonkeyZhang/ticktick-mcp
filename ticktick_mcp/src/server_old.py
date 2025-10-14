import asyncio
import json
import os
import logging
import re
from datetime import datetime, timezone, date, timedelta
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .ticktick_client import TickTickClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("ticktick")

# Create TickTick client
ticktick = None

# Default timezone configuration
DEFAULT_TIMEZONE = os.getenv("TICKTICK_DISPLAY_TIMEZONE", "Local")

def initialize_client():
    global ticktick
    try:
        # Check if .env file exists with access token
        load_dotenv()
        
        # Check if we have valid credentials
        if os.getenv("TICKTICK_ACCESS_TOKEN") is None:
            logger.error("No access token found in .env file. Please run 'uv run -m ticktick_mcp.cli auth' to authenticate.")
            return False
        
        # Initialize the client
        ticktick = TickTickClient()
        logger.info("TickTick client initialized successfully")
        
        # Test API connectivity
        projects = ticktick.get_projects()
        if 'error' in projects:
            logger.error(f"Failed to access TickTick API: {projects['error']}")
            logger.error("Your access token may have expired. Please run 'uv run -m ticktick_mcp.cli auth' to refresh it.")
            return False
            
        logger.info(f"Successfully connected to TickTick API with {len(projects)} projects")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize TickTick client: {e}")
        return False

# Format a task object from TickTick for better display
def format_task(task: Dict, show_local_time: bool = True) -> str:
    """Format a task into a human-readable string with optional timezone conversion."""
    formatted = f"ID: {task.get('id', 'No ID')}\n"
    formatted += f"Title: {task.get('title', 'No title')}\n"
    
    # Add project ID
    formatted += f"Project ID: {task.get('projectId', 'None')}\n"
    
    # Add dates with timezone conversion
    if task.get('startDate'):
        if show_local_time:
            formatted += f"Start Date: {convert_utc_to_local(task.get('startDate'), task.get('timeZone'))}\n"
        else:
            formatted += f"Start Date: {task.get('startDate')} (UTC)\n"
    
    if task.get('dueDate'):
        if show_local_time:
            formatted += f"Due Date: {convert_utc_to_local(task.get('dueDate'), task.get('timeZone'))}\n"
        else:
            formatted += f"Due Date: {task.get('dueDate')} (UTC)\n"
    
    # 显示任务的时区信息（如果有）
    if task.get('timeZone'):
        formatted += f"Task Timezone: {task.get('timeZone')}\n"
    
    # Add priority if available
    priority_map = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
    priority = task.get('priority', 0)
    formatted += f"Priority: {priority_map.get(priority, str(priority))}\n"
    
    # Add status if available
    status = "Completed" if task.get('status') == 2 else "Active"
    formatted += f"Status: {status}\n"
    
    # Add content if available
    if task.get('content'):
        formatted += f"\nContent:\n{task.get('content')}\n"
    
    # Add subtasks if available
    items = task.get('items', [])
    if items:
        formatted += f"\nSubtasks ({len(items)}):\n"
        for i, item in enumerate(items, 1):
            status = "✓" if item.get('status') == 1 else "□"
            formatted += f"{i}. [{status}] {item.get('title', 'No title')}\n"
    
    return formatted

# Format a project object from TickTick for better display
def format_project(project: Dict) -> str:
    """Format a project into a human-readable string."""
    formatted = f"Name: {project.get('name', 'No name')}\n"
    formatted += f"ID: {project.get('id', 'No ID')}\n"
    
    # Add color if available
    if project.get('color'):
        formatted += f"Color: {project.get('color')}\n"
    
    # Add view mode if available
    if project.get('viewMode'):
        formatted += f"View Mode: {project.get('viewMode')}\n"
    
    # Add closed status if available
    if 'closed' in project:
        formatted += f"Closed: {'Yes' if project.get('closed') else 'No'}\n"
    
    # Add kind if available
    if project.get('kind'):
        formatted += f"Kind: {project.get('kind')}\n"
    
    return formatted

# Helper function for timezone conversion
def convert_utc_to_local(utc_time_str: str, target_timezone: str = None) -> str:
    """
    将UTC时间字符串转换为指定时区或本地时区的时间
    
    Args:
        utc_time_str: UTC时间字符串，格式如 "2019-11-13T03:00:00+0000"
        target_timezone: 目标时区，如 "Asia/Shanghai"，None表示使用系统本地时区
        
    Returns:
        转换后的时间字符串，包含原始UTC时间和本地时间
    """
    if not utc_time_str:
        return utc_time_str
    
    try:
        # 解析UTC时间
        normalized_date = normalize_iso_date(utc_time_str)
        utc_dt = datetime.fromisoformat(normalized_date)
        
        # 确定目标时区：任务时区 > 配置时区 > 本地时区
        if not target_timezone and DEFAULT_TIMEZONE != "Local":
            target_timezone = DEFAULT_TIMEZONE
        
        # 转换为目标时区
        if target_timezone:
            # 如果指定了时区，尝试使用zoneinfo（Python 3.9+）
            try:
                from zoneinfo import ZoneInfo
                local_dt = utc_dt.astimezone(ZoneInfo(target_timezone))
                timezone_name = target_timezone
            except (ImportError, Exception):
                # 降级到系统本地时区
                local_dt = utc_dt.astimezone()
                timezone_name = "Local"
        else:
            # 使用系统本地时区
            local_dt = utc_dt.astimezone()
            timezone_name = "Local"
        
        # 格式化返回
        local_time_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        return f"{local_time_str} ({timezone_name}) [UTC: {utc_time_str}]"
        
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回原始时间
        logger.warning(f"Failed to convert timezone for {utc_time_str}: {e}")
        return f"{utc_time_str} (UTC)"

# Helper function for date validation
def normalize_iso_date(date_str: str) -> str:
    """
    Normalize ISO date string to a format that Python's fromisoformat() can parse.
    
    Handles:
    - "Z" suffix → "+00:00"
    - "+0000" or "-0000" (no colon) → "+00:00" or "-00:00" (with colon)
    - Already correct formats remain unchanged
    
    Args:
        date_str: ISO date string in various formats
        
    Returns:
        Normalized ISO date string that fromisoformat() can parse
    """
    if not date_str:
        return date_str
    
    # Replace "Z" with "+00:00"
    normalized = date_str.replace("Z", "+00:00")
    
    # Handle "+0000" or "-0000" format (add colon before last 2 digits)
    # Match pattern: ends with +HHMM or -HHMM (4 digits after + or -)
    # Pattern: ends with + or - followed by exactly 4 digits
    pattern = r'([+-])(\d{2})(\d{2})$'
    match = re.search(pattern, normalized)
    if match:
        # Replace with format: +HH:MM
        normalized = re.sub(pattern, r'\1\2:\3', normalized)
    
    return normalized

# MCP Tools

@mcp.tool()
async def get_projects() -> str:
    """
    Get all projects from TickTick.
    
    Note: This does not include the special "Inbox" project. 
    To get inbox tasks, use the get_inbox_tasks tool separately.
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        if not projects:
            return "No projects found."
        
        result = f"Found {len(projects)} projects:\n\n"
        for i, project in enumerate(projects, 1):
            result += f"Project {i}:\n" + format_project(project) + "\n"
        
        return result
    except Exception as e:
        logger.error(f"Error in get_projects: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_inbox_tasks() -> str:
    """
    Get tasks from the Inbox.
    
    The Inbox is a special system list in TickTick where tasks 
    without a specific project are stored. This is useful for 
    quick task capture that can be organized later.
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        # Use the special project ID "inbox" to access the inbox
        inbox_data = ticktick.get_project_with_data("inbox")
        
        if 'error' in inbox_data:
            return f"Error fetching inbox: {inbox_data['error']}"
        
        project = inbox_data.get('project', {})
        tasks = inbox_data.get('tasks', [])
        
        if not tasks:
            return "Your inbox is empty. 📭 Great job staying organized!"
        
        result = f"Inbox: {project.get('name', 'Inbox')}\n"
        result += f"Found {len(tasks)} tasks:\n\n"
        
        for i, task in enumerate(tasks, 1):
            result += f"Task {i}:\n" + format_task(task) + "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_inbox_tasks: {e}")
        return f"Error retrieving inbox tasks: {str(e)}"

@mcp.tool()
async def get_project(project_id: str) -> str:
    """
    Get details about a specific project.
    
    Args:
        project_id: ID of the project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        project = ticktick.get_project(project_id)
        if 'error' in project:
            return f"Error fetching project: {project['error']}"
        
        return format_project(project)
    except Exception as e:
        logger.error(f"Error in get_project: {e}")
        return f"Error retrieving project: {str(e)}"

@mcp.tool()
async def get_project_tasks(project_id: str) -> str:
    """
    Get all tasks in a specific project.
    
    Args:
        project_id: ID of the project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        project_data = ticktick.get_project_with_data(project_id)
        if 'error' in project_data:
            return f"Error fetching project data: {project_data['error']}"
        
        tasks = project_data.get('tasks', [])
        if not tasks:
            return f"No tasks found in project '{project_data.get('project', {}).get('name', project_id)}'."
        
        result = f"Found {len(tasks)} tasks in project '{project_data.get('project', {}).get('name', project_id)}':\n\n"
        for i, task in enumerate(tasks, 1):
            result += f"Task {i}:\n" + format_task(task) + "\n"
        
        return result
    except Exception as e:
        logger.error(f"Error in get_project_tasks: {e}")
        return f"Error retrieving project tasks: {str(e)}"

@mcp.tool()
async def get_task(project_id: str, task_id: str) -> str:
    """
    Get details about a specific task.
    
    Args:
        project_id: ID of the project
        task_id: ID of the task
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
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
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
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
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
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
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
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
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.delete_task(project_id, task_id)
        if 'error' in result:
            return f"Error deleting task: {result['error']}"
        
        return f"Task {task_id} deleted successfully."
    except Exception as e:
        logger.error(f"Error in delete_task: {e}")
        return f"Error deleting task: {str(e)}"

@mcp.tool()
async def create_project(
    name: str,
    color: str = "#F18181",
    view_mode: str = "list"
) -> str:
    """
    Create a new project in TickTick.
    
    Args:
        name: Project name
        color: Color code (hex format) (optional)
        view_mode: View mode - one of list, kanban, or timeline (optional)
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate view_mode
    if view_mode not in ["list", "kanban", "timeline"]:
        return "Invalid view_mode. Must be one of: list, kanban, timeline."
    
    try:
        project = ticktick.create_project(
            name=name,
            color=color,
            view_mode=view_mode
        )
        
        if 'error' in project:
            return f"Error creating project: {project['error']}"
        
        return f"Project created successfully:\n\n" + format_project(project)
    except Exception as e:
        logger.error(f"Error in create_project: {e}")
        return f"Error creating project: {str(e)}"

@mcp.tool()
async def delete_project(project_id: str) -> str:
    """
    Delete a project.
    
    Args:
        project_id: ID of the project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.delete_project(project_id)
        if 'error' in result:
            return f"Error deleting project: {result['error']}"
        
        return f"Project {project_id} deleted successfully."
    except Exception as e:
        logger.error(f"Error in delete_project: {e}")
        return f"Error deleting project: {str(e)}"
    

### Improved Task MCP Tools

# Helper Functions

PRIORITY_MAP = {0: "None", 1: "Low", 3: "Medium", 5: "High"}

def get_user_timezone_today() -> date:
    """Get today's date in the user's timezone."""
    if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
        try:
            user_tz = ZoneInfo(DEFAULT_TIMEZONE)
            return datetime.now(user_tz).date()
        except Exception:
            # Fallback to local timezone if user timezone is invalid
            pass
    return datetime.now().date()

def _is_task_due_today(task: Dict[str, Any]) -> bool:
    """Check if a task is due today."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        # 使用normalize_iso_date来处理各种日期格式
        normalized_date = normalize_iso_date(due_date)
        task_due_dt = datetime.fromisoformat(normalized_date)
        
        # 将任务截止时间转换为用户时区
        if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
            try:
                user_tz = ZoneInfo(DEFAULT_TIMEZONE)
                task_due_local = task_due_dt.astimezone(user_tz)
            except Exception:
                # Fallback to local timezone
                task_due_local = task_due_dt.astimezone()
        else:
            task_due_local = task_due_dt.astimezone()
        
        task_due_date = task_due_local.date()
        today_date = get_user_timezone_today()
        return task_due_date == today_date
    except (ValueError, TypeError):
        return False

def _is_task_overdue(task: Dict[str, Any]) -> bool:
    """Check if a task is overdue."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        # 使用normalize_iso_date来处理各种日期格式
        normalized_date = normalize_iso_date(due_date)
        task_due = datetime.fromisoformat(normalized_date)
        
        # 获取用户时区的当前时间进行比较
        if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
            try:
                user_tz = ZoneInfo(DEFAULT_TIMEZONE)
                now_user_tz = datetime.now(user_tz)
                task_due_user_tz = task_due.astimezone(user_tz)
            except Exception:
                # Fallback to local timezone
                now_user_tz = datetime.now()
                task_due_user_tz = task_due.astimezone()
        else:
            now_user_tz = datetime.now()
            task_due_user_tz = task_due.astimezone()
        
        return task_due_user_tz < now_user_tz
    except (ValueError, TypeError):
        return False

def _is_task_due_in_days(task: Dict[str, Any], days: int) -> bool:
    """Check if a task is due in exactly X days."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        # 使用normalize_iso_date来处理各种日期格式
        normalized_date = normalize_iso_date(due_date)
        task_due_dt = datetime.fromisoformat(normalized_date)
        
        # 将任务截止时间转换为用户时区
        if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
            try:
                user_tz = ZoneInfo(DEFAULT_TIMEZONE)
                task_due_local = task_due_dt.astimezone(user_tz)
            except Exception:
                # Fallback to local timezone
                task_due_local = task_due_dt.astimezone()
        else:
            task_due_local = task_due_dt.astimezone()
        
        task_due_date = task_due_local.date()
        target_date = get_user_timezone_today() + timedelta(days=days)
        return task_due_date == target_date
    except (ValueError, TypeError):
        return False

def _task_matches_search(task: Dict[str, Any], search_term: str) -> bool:
    """Check if a task matches the search term (case-insensitive)."""
    search_term = search_term.lower()
    
    # Search in title
    title = task.get('title', '').lower()
    if search_term in title:
        return True
    
    # Search in content
    content = task.get('content', '').lower()
    if search_term in content:
        return True
    
    # Search in subtasks
    items = task.get('items', [])
    for item in items:
        item_title = item.get('title', '').lower()
        if search_term in item_title:
            return True
    
    return False

def _validate_task_data(task_data: Dict[str, Any], task_index: int) -> Optional[str]:
    """
    Validate a single task's data for batch creation.
    
    Returns:
        None if valid, error message string if invalid
    """
    # Check required fields
    if 'title' not in task_data or not task_data['title']:
        return f"Task {task_index + 1}: 'title' is required and cannot be empty"
    
    if 'project_id' not in task_data or not task_data['project_id']:
        return f"Task {task_index + 1}: 'project_id' is required and cannot be empty"
    
    # Validate priority if provided
    priority = task_data.get('priority')
    if priority is not None and priority not in [0, 1, 3, 5]:
        return f"Task {task_index + 1}: Invalid priority {priority}. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)"
    
    # Validate dates if provided
    for date_field in ['start_date', 'due_date']:
        date_str = task_data.get(date_field)
        if date_str:
            try:
                # Try to parse the date to validate it
                normalized_date = normalize_iso_date(date_str)
                datetime.fromisoformat(normalized_date)
            except ValueError:
                return f"Task {task_index + 1}: Invalid {date_field} format '{date_str}'. Use ISO format: YYYY-MM-DDTHH:mm:ss or with timezone"
    
    # Validate is_all_day if provided
    is_all_day = task_data.get('is_all_day')
    if is_all_day is not None and not isinstance(is_all_day, bool):
        return f"Task {task_index + 1}: 'is_all_day' must be a boolean (true/false)"
    
    # Validate reminders if provided
    reminders = task_data.get('reminders')
    if reminders is not None and not isinstance(reminders, list):
        return f"Task {task_index + 1}: 'reminders' must be a list"
    
    # Validate items (subtasks) if provided
    items = task_data.get('items')
    if items is not None and not isinstance(items, list):
        return f"Task {task_index + 1}: 'items' must be a list"
    
    # Validate sort_order if provided
    sort_order = task_data.get('sort_order')
    if sort_order is not None and not isinstance(sort_order, int):
        return f"Task {task_index + 1}: 'sort_order' must be an integer"
    
    return None

def _get_project_tasks_by_filter(projects: List[Dict], filter_func, filter_name: str) -> str:
    """
    Helper function to filter tasks across all projects AND Inbox.
    
    Args:
        projects: List of project dictionaries
        filter_func: Function that takes a task and returns True if it matches the filter
        filter_name: Name of the filter for output formatting
    
    Returns:
        Formatted string of filtered tasks
    """
    if not projects:
        return "No projects found."
    
    result = f"Found {len(projects)} projects + Inbox:\n\n"
    
    # Regular projects
    for i, project in enumerate(projects, 1):
        if project.get('closed'):
            continue
            
        project_id = project.get('id', 'No ID')
        project_data = ticktick.get_project_with_data(project_id)
        tasks = project_data.get('tasks', [])
        
        if not tasks:
            result += f"Project {i}:\n{format_project(project)}"
            result += f"With 0 tasks that are to be '{filter_name}' in this project :\n\n\n"
            continue
        
        # Filter tasks using the provided function
        filtered_tasks = [(t, task) for t, task in enumerate(tasks, 1) if filter_func(task)]
        
        result += f"Project {i}:\n{format_project(project)}"
        result += f"With {len(filtered_tasks)} tasks that are to be '{filter_name}' in this project :\n"
        
        for t, task in filtered_tasks:
            result += f"Task {t}:\n{format_task(task)}\n"
        
        result += "\n\n"
    
    # Inbox
    try:
        inbox_data = ticktick.get_project_with_data("inbox")
        if 'error' not in inbox_data:
            inbox_project = inbox_data.get('project', {}) or {'name': 'Inbox'}
            inbox_tasks = inbox_data.get('tasks', []) or []
            
            filtered_inbox_tasks = [(t, task) for t, task in enumerate(inbox_tasks, 1) if filter_func(task)]
            
            result += "Inbox:\n"
            result += f"Name: {inbox_project.get('name', 'Inbox')}\n"
            result += "ID: inbox\n"
            result += f"With {len(filtered_inbox_tasks)} tasks that are to be '{filter_name}' in this project :\n"
            
            for t, task in filtered_inbox_tasks:
                result += f"Task {t}:\n{format_task(task)}\n"
            
            result += "\n"
        else:
            result += f"Inbox: Error fetching inbox: {inbox_data['error']}\n"
    except Exception as e:
        logger.warning(f"Could not fetch inbox tasks: {e}")
        result += f"Inbox: Could not fetch (error: {str(e)})\n"
    
    return result

# New MCP Tools for Tasks

@mcp.tool()
async def get_all_tasks() -> str:
    """Get all tasks from TickTick. Ignores closed projects."""
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def all_tasks_filter(task: Dict[str, Any]) -> bool:
            return True  # Include all tasks
        
        return _get_project_tasks_by_filter(projects, all_tasks_filter, "included")
        
    except Exception as e:
        logger.error(f"Error in get_all_tasks: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_tasks_by_priority(priority_id: int) -> str:
    """
    Get all tasks from TickTick by priority. Ignores closed projects.

    Args:
        priority_id: Priority of tasks to retrieve {0: "None", 1: "Low", 3: "Medium", 5: "High"}
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    if priority_id not in PRIORITY_MAP:
        return f"Invalid priority_id. Valid values: {list(PRIORITY_MAP.keys())}"
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def priority_filter(task: Dict[str, Any]) -> bool:
            return task.get('priority', 0) == priority_id
        
        priority_name = f"{PRIORITY_MAP[priority_id]} ({priority_id})"
        return _get_project_tasks_by_filter(projects, priority_filter, f"priority '{priority_name}'")
        
    except Exception as e:
        logger.error(f"Error in get_tasks_by_priority: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_tasks_due_today() -> str:
    """Get all tasks from TickTick that are due today. Ignores closed projects."""
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def today_filter(task: Dict[str, Any]) -> bool:
            return _is_task_due_today(task)
        
        return _get_project_tasks_by_filter(projects, today_filter, "due today")
        
    except Exception as e:
        logger.error(f"Error in get_tasks_due_today: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_overdue_tasks() -> str:
    """Get all overdue tasks from TickTick. Ignores closed projects."""
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def overdue_filter(task: Dict[str, Any]) -> bool:
            return _is_task_overdue(task)
        
        return _get_project_tasks_by_filter(projects, overdue_filter, "overdue")
        
    except Exception as e:
        logger.error(f"Error in get_overdue_tasks: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_tasks_due_tomorrow() -> str:
    """Get all tasks from TickTick that are due today. Ignores closed projects."""
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def today_filter(task: Dict[str, Any]) -> bool:
            return _is_task_due_in_days(task, 1)
        
        return _get_project_tasks_by_filter(projects, today_filter, "due today")
        
    except Exception as e:
        logger.error(f"Error in get_tasks_due_today: {e}")
        return f"Error retrieving projects: {str(e)}"
    
@mcp.tool()
async def get_tasks_due_in_days(days: int) -> str:
    """
    Get all tasks from TickTick that are due in exactly X days. Ignores closed projects.
    
    Args:
        days: Number of days from today (0 = today, 1 = tomorrow, etc.)
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    if days < 0:
        return "Days must be a non-negative integer."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def days_filter(task: Dict[str, Any]) -> bool:
            return _is_task_due_in_days(task, days)
        
        day_description = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
        return _get_project_tasks_by_filter(projects, days_filter, f"due {day_description}")
        
    except Exception as e:
        logger.error(f"Error in get_tasks_due_in_days: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_tasks_due_this_week() -> str:
    """Get all tasks from TickTick that are due within the next 7 days. Ignores closed projects."""
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def week_filter(task: Dict[str, Any]) -> bool:
            due_date = task.get('dueDate')
            if not due_date:
                return False
            
            try:
                # 使用normalize_iso_date来处理各种日期格式
                normalized_date = normalize_iso_date(due_date)
                task_due_dt = datetime.fromisoformat(normalized_date)
                
                # 将任务截止时间转换为用户时区
                if DEFAULT_TIMEZONE and DEFAULT_TIMEZONE != "Local":
                    try:
                        user_tz = ZoneInfo(DEFAULT_TIMEZONE)
                        task_due_local = task_due_dt.astimezone(user_tz)
                    except Exception:
                        # Fallback to local timezone
                        task_due_local = task_due_dt.astimezone()
                else:
                    task_due_local = task_due_dt.astimezone()
                
                task_due_date = task_due_local.date()
                today = get_user_timezone_today()
                week_from_today = today + timedelta(days=7)
                return today <= task_due_date <= week_from_today
            except (ValueError, TypeError):
                return False
        
        return _get_project_tasks_by_filter(projects, week_filter, "due this week")
        
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
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    if not search_term.strip():
        return "Search term cannot be empty."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def search_filter(task: Dict[str, Any]) -> bool:
            return _task_matches_search(task, search_term)
        
        return _get_project_tasks_by_filter(projects, search_filter, f"matching '{search_term}'")
        
    except Exception as e:
        logger.error(f"Error in search_tasks: {e}")
        return f"Error retrieving projects: {str(e)}"

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
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
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
        
        error = _validate_task_data(task_data, i)
        if error:
            validation_errors.append(error)
    
    if validation_errors:
        return "Validation errors found:\n" + "\n".join(validation_errors)
    
    # Create tasks one by one and collect results
    created_tasks = []
    failed_tasks = []
    
    try:
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

# New MCP Tools for Getting things done framework (Priority / Due Dates)

@mcp.tool()
async def get_engaged_tasks() -> str:
    """
    Get all tasks from TickTick that are "Engaged".
    This includes tasks marked as high priority (5), due today or overdue.
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def engaged_filter(task: Dict[str, Any]) -> bool:
            is_high_priority = task.get('priority', 0) == 5
            is_overdue = _is_task_overdue(task)
            is_today = _is_task_due_today(task)
            return is_high_priority or is_overdue or is_today
        
        return _get_project_tasks_by_filter(projects, engaged_filter, "engaged")
        
    except Exception as e:
        logger.error(f"Error in get_engaged_tasks: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_next_tasks() -> str:
    """
    Get all tasks from TickTick that are "Next".
    This includes tasks marked as medium priority (3) or due tomorrow.
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        def next_filter(task: Dict[str, Any]) -> bool:
            is_medium_priority = task.get('priority', 0) == 3
            is_due_tomorrow = _is_task_due_in_days(task, 1)
            return is_medium_priority or is_due_tomorrow
        
        return _get_project_tasks_by_filter(projects, next_filter, "next")
        
    except Exception as e:
        logger.error(f"Error in get_next_tasks: {e}")
        return f"Error retrieving projects: {str(e)}"

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
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate priority
    if priority not in [0, 1, 3, 5]:
        return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
    
    try:
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

def main():
    """Main entry point for the MCP server."""
    # Initialize the TickTick client
    if not initialize_client():
        logger.error("Failed to initialize TickTick client. Please check your API credentials.")
        return
    
    # Run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()