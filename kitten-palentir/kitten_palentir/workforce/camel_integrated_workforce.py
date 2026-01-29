"""
CAMEL-AI Integrated Workforce with proper agent integration.

This module implements a workforce that uses CAMEL-AI native Workforce class
with properly integrated agents and toolkits.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.societies.workforce import Workforce, WorkforceMode
from camel.storages import Neo4jGraph
from camel.types import ModelPlatformType, ModelType

from kitten_palentir.agents.camel_integrated_agents import (
    NetworkAnalyzerAgent,
    SocialMediaIntelligenceAgent,
    DomainIntelligenceAgent,
    DataBreachIntelligenceAgent,
    AGENT_REGISTRY,
)
from kitten_palentir.toolkits.mcp_integration import PalentirMCPToolkit
from kitten_palentir.config.settings import get_settings

logger = logging.getLogger(__name__)


class PalentirCAMELWorkforce:
    """CAMEL-AI Workforce for OSINT operations."""

    def __init__(
        self,
        description: str = "Palentir OSINT Workforce",
        enable_mcp: bool = False,
        mcp_config_path: Optional[str] = None,
        share_memory: bool = True,
        graceful_shutdown_timeout: float = 30.0,
        neo4j_url: Optional[str] = None,
        neo4j_username: Optional[str] = None,
        neo4j_password: Optional[str] = None,
    ):
        """Initialize the Palentir CAMEL-AI Workforce.
        
        Args:
            description: Workforce description
            enable_mcp: Whether to enable MCP toolkit integration
            mcp_config_path: Path to MCP servers config (optional)
            share_memory: Whether to enable shared memory between agents
            graceful_shutdown_timeout: Timeout for graceful shutdown in seconds
            neo4j_url: Neo4j connection URL (optional, for graph memory)
            neo4j_username: Neo4j username (optional)
            neo4j_password: Neo4j password (optional)
        """
        # Get settings for model configuration
        settings = get_settings()
        
        # Create model for coordinator and task agents
        # Use GPT-5 as default (most efficient)
        model_type = ModelType.GPT_5 if hasattr(ModelType, 'GPT_5') else ModelType.GPT_4_TURBO
        model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        # Create coordinator agent
        coordinator_agent = ChatAgent(
            BaseMessage.make_assistant_message(
                role_name="Coordinator",
                content=(
                    "You are a coordinator responsible for managing OSINT tasks "
                    "across multiple specialized agents. You coordinate task "
                    "execution and ensure quality output."
                ),
            ),
            model=model,
        )
        
        # Create task agent
        task_agent = ChatAgent(
            BaseMessage.make_assistant_message(
                role_name="Task Planner",
                content=(
                    "You are a task planning agent responsible for analyzing "
                    "and decomposing complex OSINT tasks into manageable subtasks."
                ),
            ),
            model=model,
        )
        
        # Initialize Neo4jGraph as memory if credentials provided
        memory = None
        if neo4j_url and neo4j_username and neo4j_password:
            try:
                memory = Neo4jGraph(
                    url=neo4j_url,
                    username=neo4j_username,
                    password=neo4j_password,
                )
                logger.info("Neo4jGraph initialized as workforce memory")
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4jGraph: {e}. Continuing without graph memory.")
        
        # Create CAMEL-AI native workforce with proper configuration
        # Note: CAMEL Workforce doesn't accept 'memory' parameter directly
        # Memory is handled through share_memory flag and agent configurations
        self.workforce = Workforce(
            description=description,
            coordinator_agent=coordinator_agent,
            task_agent=task_agent,
            mode=WorkforceMode.PIPELINE,
            share_memory=share_memory,
            graceful_shutdown_timeout=graceful_shutdown_timeout,
        )
        
        # Initialize MCP toolkit if enabled
        self.mcp_toolkit: Optional[PalentirMCPToolkit] = None
        self.enable_mcp = enable_mcp
        if enable_mcp:
            self.mcp_toolkit = PalentirMCPToolkit(config_path=mcp_config_path)
            logger.info("MCP toolkit initialized (will connect when needed)")
        
        # Initialize agents
        self.agents: Dict[str, Any] = {}
        self._initialize_agents()
        
        logger.info(f"PalentirCAMELWorkforce initialized with {len(self.agents)} agents")

    def _initialize_agents(self) -> None:
        """Initialize all OSINT agents with API keys from settings."""
        # Get settings for API keys and model configuration
        settings = get_settings()
        
        # Use GPT-5 as default (most efficient)
        model_type = ModelType.GPT_5 if hasattr(ModelType, 'GPT_5') else ModelType.GPT_4_TURBO
        
        # Note: MCP tools will be added when agents are used (requires async connection)
        # For now, agents are created without MCP tools
        
        # Network Analyzer Agent - with optional Censys and Liferaft API keys
        network_agent = NetworkAnalyzerAgent(
            model_type=model_type,
            censys_api_id=settings.censys_api_id,
            censys_api_secret=settings.censys_api_secret,
            liferaft_api_key=settings.liferaft_api_key,
        )
        self.agents["network_analyzer"] = network_agent
        self.workforce.add_single_agent_worker(
            description="Network reconnaissance specialist",
            worker=network_agent.agent,
        )
        logger.info("Added NetworkAnalyzerAgent to workforce")
        
        # Social Media Intelligence Agent - with optional Social Links API key
        social_agent = SocialMediaIntelligenceAgent(
            model_type=model_type,
            sociallinks_api_key=settings.sociallinks_api_key,
        )
        self.agents["social_media_intelligence"] = social_agent
        self.workforce.add_single_agent_worker(
            description="Social media intelligence specialist",
            worker=social_agent.agent,
        )
        logger.info("Added SocialMediaIntelligenceAgent to workforce")
        
        # Domain Intelligence Agent - with optional Maltego and Censys API keys
        domain_agent = DomainIntelligenceAgent(
            model_type=model_type,
            maltego_api_key=settings.maltego_api_key,
            censys_api_id=settings.censys_api_id,
            censys_api_secret=settings.censys_api_secret,
        )
        self.agents["domain_intelligence"] = domain_agent
        self.workforce.add_single_agent_worker(
            description="Domain intelligence specialist",
            worker=domain_agent.agent,
        )
        logger.info("Added DomainIntelligenceAgent to workforce")
        
        # Data Breach Intelligence Agent - with optional Liferaft API key
        breach_agent = DataBreachIntelligenceAgent(
            model_type=model_type,
            liferaft_api_key=settings.liferaft_api_key,
        )
        self.agents["data_breach_intelligence"] = breach_agent
        self.workforce.add_single_agent_worker(
            description="Data breach intelligence specialist",
            worker=breach_agent.agent,
        )
        logger.info("Added DataBreachIntelligenceAgent to workforce")

    async def process_task(
        self,
        task_content: str,
        agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a task using the workforce.
        
        Args:
            task_content: Task content to process
            agent_name: Specific agent to use (optional)
            
        Returns:
            Task result
        """
        # Connect to MCP if enabled (using async context manager)
        if self.enable_mcp and self.mcp_toolkit:
            async with self.mcp_toolkit:
                # MCP tools are available during this context
                # Note: For full MCP integration, agents would need to be recreated with MCP tools
                # This is a simplified approach - MCP can be used separately
                return await self._execute_task(task_content, agent_name)
        else:
            return await self._execute_task(task_content, agent_name)
    
    async def _execute_task(
        self,
        task_content: str,
        agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute task (internal method)."""
        try:
            if agent_name and agent_name in self.agents:
                # Use specific agent
                agent = self.agents[agent_name]
                if hasattr(agent, "analyze_network"):
                    result = await agent.analyze_network(task_content)
                elif hasattr(agent, "search_social_profiles"):
                    result = await agent.search_social_profiles(task_content)
                elif hasattr(agent, "analyze_domain"):
                    result = await agent.analyze_domain(task_content)
                elif hasattr(agent, "search_breaches"):
                    result = await agent.search_breaches(task_content)
                else:
                    result = {"status": "error", "error": "Unknown agent type"}
            else:
                # Use workforce to process task
                result = await self.workforce.process_task(task_content)
            
            return result
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get agent by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """List all available agents.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys())

    def get_agent_tools(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get tools for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of tools
        """
        agent = self.agents.get(agent_name)
        if agent and hasattr(agent, "get_tools"):
            return agent.get_tools()
        return []

    def get_workforce_info(self) -> Dict[str, Any]:
        """Get workforce information.
        
        Returns:
            Workforce information
        """
        return {
            "description": self.workforce.description,
            "agents": self.list_agents(),
            "agent_count": len(self.agents),
        }

    async def disconnect(self) -> None:
        """Disconnect from all MCP servers and clean up resources."""
        try:
            # Disconnect MCP toolkit if enabled
            if self.mcp_toolkit:
                await self.mcp_toolkit.disconnect()
                logger.info("Disconnected from MCP servers")
            
            # Clean up any async resources
            for agent_name, agent in self.agents.items():
                if hasattr(agent, "disconnect"):
                    await agent.disconnect()
                    logger.info(f"Disconnected from {agent_name}")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def to_mcp_server(self, port: int = 8001, name: str = "Palentir-OSINT-Workforce"):
        """Convert workforce to MCP server.
        
        Args:
            port: Port for MCP server
            name: Name of the MCP server
            
        Returns:
            MCP server instance
        """
        return self.workforce.to_mcp(
            name=name,
            description="OSINT intelligence workforce",
            port=port,
        )


async def create_workforce(
    description: str = "Palentir OSINT Workforce",
) -> PalentirCAMELWorkforce:
    """Create a new Palentir CAMEL-AI Workforce.
    
    Args:
        description: Workforce description
        
    Returns:
        Initialized workforce instance
    """
    workforce = PalentirCAMELWorkforce(description=description)
    logger.info("Workforce created successfully")
    return workforce
