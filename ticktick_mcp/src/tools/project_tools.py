"""
Project management tools for TickTick MCP.

This module contains MCP tools for managing TickTick projects,
including creating, reading, updating, and deleting projects.
"""

import logging
from mcp.server.fastmcp import FastMCP

from ..config import ensure_client
from ..utils.formatters import format_project, format_task

# Set up logging
logger = logging.getLogger(__name__)


def register_project_tools(mcp: FastMCP):
    """Register all project-related MCP tools."""
    
    @mcp.tool()
    async def get_projects() -> str:
        """
        Get all projects from TickTick.
        
        Note: This does not include the special "Inbox" project. 
        To get inbox tasks, use get_project_tasks with project_id="inbox".
        """
        try:
            ticktick = ensure_client()
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
    async def get_project(project_id: str) -> str:
        """
        Get details about a specific project.
        
        Args:
            project_id: ID of the project
        """
        try:
            ticktick = ensure_client()
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
        Get all tasks in a specific project or inbox.
        
        Args:
            project_id: ID of the project, or "inbox" to get inbox tasks
        
        Special values:
            - "inbox": Get tasks from the Inbox (a special system list where tasks
              without a specific project are stored)
        
        Examples:
            - get_project_tasks("abc123") → Get tasks from project with ID "abc123"
            - get_project_tasks("inbox") → Get tasks from Inbox
        """
        try:
            ticktick = ensure_client()
            project_data = ticktick.get_project_with_data(project_id)
            if 'error' in project_data:
                return f"Error fetching project data: {project_data['error']}"
            
            project = project_data.get('project', {})
            tasks = project_data.get('tasks', [])
            project_name = project.get('name', project_id)
            
            # Special message for empty inbox
            if project_id.lower() == "inbox" and not tasks:
                return "Your inbox is empty. 📭 Great job staying organized!"
            
            # General empty message for other projects
            if not tasks:
                return f"No tasks found in project '{project_name}'."
            
            # Format result
            result = f"Found {len(tasks)} tasks in project '{project_name}':\n\n"
            for i, task in enumerate(tasks, 1):
                result += f"Task {i}:\n" + format_task(task) + "\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in get_project_tasks: {e}")
            return f"Error retrieving project tasks: {str(e)}"

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
        # Validate view_mode
        if view_mode not in ["list", "kanban", "timeline"]:
            return "Invalid view_mode. Must be one of: list, kanban, timeline."
        
        try:
            ticktick = ensure_client()
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
        try:
            ticktick = ensure_client()
            result = ticktick.delete_project(project_id)
            if 'error' in result:
                return f"Error deleting project: {result['error']}"
            
            return f"Project {project_id} deleted successfully."
        except Exception as e:
            logger.error(f"Error in delete_project: {e}")
            return f"Error deleting project: {str(e)}"
