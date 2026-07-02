"""
Databricks SSE Server

This module runs the Databricks MCP server using Server-Sent Events (SSE) as transport.
It starts an HTTP server using Starlette/Uvicorn, exposing the /sse and /messages/ endpoints.
"""

import asyncio
import logging
import sys
from typing import Optional

from src.core.config import settings
from src.server.databricks_mcp_server import DatabricksMCPServer


def setup_logging(log_level: Optional[str] = None):
    """
    Set up logging configuration.
    
    Args:
        log_level: Optional log level to override the default
    """
    level = getattr(logging, log_level or settings.LOG_LEVEL)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


async def main():
    """Main entry point for starting the SSE server."""
    # Instantiate the MCP server
    server = DatabricksMCPServer()

    # Override FastMCP settings from application settings
    server.settings.host = settings.SERVER_HOST
    server.settings.port = settings.SERVER_PORT
    server.settings.debug = settings.DEBUG

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Databricks MCP SSE server v{settings.VERSION}")
    logger.info(f"Host: {server.settings.host}")
    logger.info(f"Port: {server.settings.port}")
    logger.info(f"Databricks Host: {settings.DATABRICKS_HOST}")
    logger.info(f"SSE Endpoint: http://{server.settings.host}:{server.settings.port}/sse")
    logger.info(f"Message Endpoint: http://{server.settings.host}:{server.settings.port}/messages/")

    try:
        await server.run_sse_async()
    except Exception as e:
        logger.error(f"Error starting SSE server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Databricks MCP SSE Server")
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind the server to (overrides SERVER_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind the server to (overrides SERVER_PORT)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the log level",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()

    # Apply command line arguments to configuration
    if args.host:
        settings.SERVER_HOST = args.host
    if args.port:
        settings.SERVER_PORT = args.port
    if args.debug:
        settings.DEBUG = True
    
    # Set up logging
    setup_logging(args.log_level)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
