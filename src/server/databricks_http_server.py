"""
Databricks Streamable HTTP MCP Server

This module runs the Databricks MCP server using the Streamable HTTP transport,
which exposes a single HTTP endpoint (default: /mcp) handling both requests and
responses. This is the transport expected by Gemini Enterprise's Custom MCP
Server (Preview) integration.
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
    """Main entry point for starting the Streamable HTTP server."""
    # Instantiate the MCP server
    server = DatabricksMCPServer()

    # Override FastMCP settings from application settings
    server.settings.host = settings.SERVER_HOST
    server.settings.port = settings.SERVER_PORT
    server.settings.debug = settings.DEBUG

    # FastMCP defaults the Streamable HTTP path to "/mcp".
    # Leaving this as default matches what Gemini Enterprise expects
    # (an HTTPS URL "typically ending in /mcp").
    mcp_path = getattr(server.settings, "streamable_http_path", "/mcp")

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Databricks MCP Streamable HTTP server v{settings.VERSION}")
    logger.info(f"Host: {server.settings.host}")
    logger.info(f"Port: {server.settings.port}")
    logger.info(f"Databricks Host: {settings.DATABRICKS_HOST}")
    logger.info(f"MCP Endpoint: http://{server.settings.host}:{server.settings.port}{mcp_path}")

    try:
        # run_streamable_http_async() is the single-endpoint transport
        # (requires mcp[cli]>=1.9.0). It replaces the older run_sse_async(),
        # which exposed two separate endpoints (/sse and /messages/).
        await server.run_streamable_http_async()
    except AttributeError:
        logger.error(
            "run_streamable_http_async() not found on FastMCP instance. "
            "Your installed 'mcp' package is likely too old — check that "
            "mcp[cli]>=1.9.0 is installed (see pyproject.toml)."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting Streamable HTTP server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Databricks MCP Streamable HTTP Server")
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
