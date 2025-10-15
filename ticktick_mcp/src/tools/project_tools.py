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
    async def get_all_projects() -> str:
        """
        Get all projects from TickTick.
        
        Note: This does not include the special "Inbox" project. 
        To get inbox information and tasks, use get_project_info(project_id="inbox").
        """
        try:
            ticktick = ensure_client()
            projects = ticktick.get_all_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
            
            if not projects:
                return "No projects found."
            
            result = f"Found {len(projects)} projects:\n\n"
            for i, project in enumerate(projects, 1):
                result += f"Project {i}:\n" + format_project(project) + "\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in get_all_projects: {e}")
            return f"Error retrieving projects: {str(e)}"

    @mcp.tool()
    async def get_project_info(project_id: str) -> str:
        """
        Get comprehensive information about a project, including its details and all tasks.
        
        This tool provides a complete view of a project in one call, showing both
        the project metadata (name, color, view mode, etc.) and all tasks within it.
        
        Args:
            project_id: ID of the project, or "inbox" to get inbox information
        
        Returns:
            A formatted string containing:
            - Project basic information (name, ID, color, etc.)
            - List of all tasks in the project with their details
        
        Examples:
            - get_project_info("abc123") → Get project info and tasks
            - get_project_info("inbox") → Get inbox info and tasks
        """
        try:
            ticktick = ensure_client()
            project_data = ticktick.get_project_with_data(project_id)
            if 'error' in project_data:
                return f"Error fetching project data: {project_data['error']}"
            
            project = project_data.get('project', {})
            tasks = project_data.get('tasks', [])
            project_name = project.get('name', project_id)
            
            # Format project information
            result = "=" * 60 + "\n"
            result += "📁 PROJECT INFORMATION\n"
            result += "=" * 60 + "\n\n"
            result += format_project(project)
            result += "\n" + "=" * 60 + "\n"
            result += f"📋 TASKS IN '{project_name}' ({len(tasks)} tasks)\n"
            result += "=" * 60 + "\n\n"
            
            # Special message for empty projects
            if project_id.lower() == "inbox" and not tasks:
                result += "Your inbox is empty. 📭 Great job staying organized!\n"
            elif not tasks:
                result += f"No tasks found in this project.\n"
            else:
                # Format tasks
                for i, task in enumerate(tasks, 1):
                    result += f"Task {i}:\n" + format_task(task) + "\n"
            
            return result
        except Exception as e:
            logger.error(f"Error in get_project_info: {e}")
            return f"Error retrieving project information: {str(e)}"

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
