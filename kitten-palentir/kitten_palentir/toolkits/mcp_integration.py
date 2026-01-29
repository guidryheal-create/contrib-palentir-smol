"""Palentir OSINT - MCP Toolkit Integration.

Provides MCP toolkit integration for CAMEL agents.
"""

import logging
from pathlib import Path
from typing import List, Optional

from camel.toolkits import MCPToolkit

logger = logging.getLogger(__name__)


class PalentirMCPToolkit:
    """MCP toolkit wrapper for Palentir OSINT agents."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize MCP toolkit.
        
        Args:
            config_path: Path to MCP servers configuration file.
                        Defaults to "mcp_servers.json" in project root.
        """
        if config_path is None:
            # Default to project root
            config_path = str(Path(__file__).parent.parent.parent / "mcp_servers.json")
        
        self.config_path = config_path
        self.mcp_toolkit = MCPToolkit(config_path=config_path)
        self._connected = False
        
        logger.info(f"MCP Toolkit initialized with config: {config_path}")

    async def connect(self):
        """Connect to MCP servers."""
        if not self._connected:
            await self.mcp_toolkit.connect()
            self._connected = True
            logger.info("Connected to MCP servers")

    async def disconnect(self):
        """Disconnect from MCP servers."""
        if self._connected:
            await self.mcp_toolkit.disconnect()
            self._connected = False
            logger.info("Disconnected from MCP servers")

    def get_tools(self) -> List:
        """Get MCP tools.
        
        Returns:
            List of MCP tools (FunctionTool instances)
        """
        if not self._connected:
            logger.warning("MCP toolkit not connected. Call connect() first or use async context manager.")
            return []
        
        tools = self.mcp_toolkit.get_tools()
        logger.info(f"Retrieved {len(tools)} MCP tools")
        return tools

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

