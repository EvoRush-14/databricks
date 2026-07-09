"""
Databricks MCP Server

This module implements a standalone MCP server that provides tools for interacting
with Databricks APIs. It follows the Model Context Protocol standard, communicating
via stdio and directly connecting to Databricks when tools are invoked.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, List, Optional, Union, cast

from mcp.server import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import TextContent
from mcp.server.stdio import stdio_server

from src.api import clusters, dbfs, jobs, notebooks, sql
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    filename="databricks_mcp.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabricksMCPServer(FastMCP):
    """An MCP server for Databricks APIs."""

    def __init__(self):
        """Initialize the Databricks MCP server."""
        allowed_hosts = settings.ALLOWED_HOSTS
        allowed_origins = settings.ALLOWED_ORIGINS

        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )

        super().__init__(
            name="databricks-mcp",
            instructions="Use this server to manage Databricks resources",
            transport_security=transport_security,
        )
        logger.info("Initializing Databricks MCP server")
        logger.info(f"Databricks host: {settings.DATABRICKS_HOST}")
        logger.info(f"Allowed hosts for transport security: {allowed_hosts}")
        logger.info(f"Allowed origins for transport security: {allowed_origins}")

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all Databricks MCP tools."""

        # ------------------------------------------------------------------
        # Cluster management tools
        # ------------------------------------------------------------------

        @self.tool(
            name="list_clusters",
            description="List all Databricks clusters",
        )
        async def list_clusters() -> List[TextContent]:
            logger.info("Listing clusters")
            try:
                result = await clusters.list_clusters()
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error listing clusters: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        @self.tool(
            name="create_cluster",
            description="Create a new Databricks cluster",
        )
        async def create_cluster(
            cluster_name: str,
            spark_version: str,
            node_type_id: str,
            num_workers: int = 1,
            autotermination_minutes: int = 60,
        ) -> List[TextContent]:
            logger.info(f"Creating cluster: {cluster_name}")
            try:
                params = {
                    "cluster_name": cluster_name,
                    "spark_version": spark_version,
                    "node_type_id": node_type_id,
                    "num_workers": num_workers,
                    "autotermination_minutes": autotermination_minutes,
                }
                result = await clusters.create_cluster(params)
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error creating cluster: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        @self.tool(
            name="terminate_cluster",
            description="Terminate a Databricks cluster",
        )
        async def terminate_cluster(cluster_id: str) -> List[TextContent]:
            logger.info(f"Terminating cluster: {cluster_id}")
            try:
                result = await clusters.terminate_cluster(cluster_id)
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error terminating cluster: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        @self.tool(
            name="get_cluster",
            description="Get information about a specific Databricks cluster",
        )
        async def get_cluster(cluster_id: str) -> List[TextContent]:
            logger.info(f"Getting cluster info: {cluster_id}")
            try:
                result = await clusters.get_cluster(cluster_id)
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error getting cluster info: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        @self.tool(
            name="start_cluster",
            description="Start a terminated Databricks cluster",
        )
        async def start_cluster(cluster_id: str) -> List[TextContent]:
            logger.info(f"Starting cluster: {cluster_id}")
            try:
                result = await clusters.start_cluster(cluster_id)
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error starting cluster: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        # ------------------------------------------------------------------
        # Job management tools
        # ------------------------------------------------------------------

        @self.tool(
            name="list_jobs",
            description="List all Databricks jobs",
        )
        async def list_jobs() -> List[TextContent]:
            logger.info("Listing jobs")
            try:
                result = await jobs.list_jobs()
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error listing jobs: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        @self.tool(
            name="run_job",
            description="Run a Databricks job",
        )
        async def run_job(
            job_id: str,
            notebook_params: Optional[Dict[str, Any]] = None,
        ) -> List[TextContent]:
            logger.info(f"Running job: {job_id}")
            try:
                result = await jobs.run_job(job_id, notebook_params or {})
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error running job: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        # ------------------------------------------------------------------
        # Notebook management tools
        # ------------------------------------------------------------------

        @self.tool(
            name="list_notebooks",
            description="List notebooks in a workspace directory",
        )
        async def list_notebooks(path: str) -> List[TextContent]:
            logger.info(f"Listing notebooks at path: {path}")
            try:
                result = await notebooks.list_notebooks(path)
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error listing notebooks: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        @self.tool(
            name="export_notebook",
            description="Export a notebook from the workspace. format must be one of: SOURCE, HTML, JUPYTER, DBC",
        )
        async def export_notebook(
            path: str,
            format: str = "SOURCE",
        ) -> List[TextContent]:
            logger.info(f"Exporting notebook at path: {path}")
            try:
                result = await notebooks.export_notebook(path, format)

                # For notebooks, we might want to trim the response for readability
                content = result.get("content", "")
                if len(content) > 1000:
                    summary = f"{content[:1000]}... [content truncated, total length: {len(content)} characters]"
                    result["content"] = summary

                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error exporting notebook: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        # ------------------------------------------------------------------
        # DBFS tools
        # ------------------------------------------------------------------

        @self.tool(
            name="list_files",
            description="List files and directories in a DBFS path",
        )
        async def list_files(dbfs_path: str) -> List[TextContent]:
            logger.info(f"Listing files at dbfs_path: {dbfs_path}")
            try:
                result = await dbfs.list_files(dbfs_path)
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error listing files: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

        # ------------------------------------------------------------------
        # SQL tools
        # ------------------------------------------------------------------

        @self.tool(
            name="execute_sql",
            description="Execute a SQL statement against a Databricks SQL warehouse",
        )
        async def execute_sql(
            statement: str,
            warehouse_id: str,
            catalog: Optional[str] = None,
            schema: Optional[str] = None,
        ) -> List[TextContent]:
            logger.info(f"Executing SQL on warehouse: {warehouse_id}")
            try:
                result = await sql.execute_sql(statement, warehouse_id, catalog, schema)
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error executing SQL: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


mcp = DatabricksMCPServer()


async def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Databricks MCP server")
        # Use the built-in method for stdio servers
        # This is the recommended approach for MCP servers
        await mcp.run_stdio_async()

    except Exception as e:
        logger.error(f"Error in Databricks MCP server: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # Turn off buffering in stdout
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)

    asyncio.run(main())
