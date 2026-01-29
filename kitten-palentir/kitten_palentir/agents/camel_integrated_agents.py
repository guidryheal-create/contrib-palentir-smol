"""
CAMEL-AI Integrated Agents with proper toolkit integration.

This module implements agents that use CAMEL-AI native toolkit integration
following the official CAMEL-AI patterns from the examples.
"""

import logging
from typing import Any, Dict, List, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.toolkits import MemoryToolkit
from camel.types import ModelPlatformType, ModelType

from kitten_palentir.toolkits.social_media_toolkit import SocialMediaToolkit
from kitten_palentir.toolkits.advanced_osint_toolkit import (
    CensysToolkit,
    LiferaftToolkit,
    MaltegoToolkit,
    SocialLinksToolkit,
)

logger = logging.getLogger(__name__)


class NetworkAnalyzerAgent:
    """Network reconnaissance agent with CAMEL-AI toolkit integration."""

    def __init__(
        self,
        model_type: ModelType = ModelType.GPT_5,
        censys_api_id: Optional[str] = None,
        censys_api_secret: Optional[str] = None,
        liferaft_api_key: Optional[str] = None,
    ):
        """Initialize Network Analyzer Agent.
        
        Args:
            model_type: The model type to use for the agent
            censys_api_id: Censys API ID (optional)
            censys_api_secret: Censys API secret (optional)
            liferaft_api_key: Liferaft API key (optional)
        """
        # Create model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        # Initialize toolkits with API credentials
        all_tools = []
        
        if censys_api_id and censys_api_secret:
            self.censys_toolkit = CensysToolkit(censys_api_id, censys_api_secret)
            censys_tools = self.censys_toolkit.get_tools()
            all_tools.extend(censys_tools)
        else:
            self.censys_toolkit = None
            logger.warning("Censys toolkit not initialized - missing API credentials")
        
        if liferaft_api_key:
            self.liferaft_toolkit = LiferaftToolkit(liferaft_api_key)
            liferaft_tools = self.liferaft_toolkit.get_tools()
            all_tools.extend(liferaft_tools)
        else:
            self.liferaft_toolkit = None
            logger.warning("Liferaft toolkit not initialized - missing API key")
        
        # Create agent with tools
        self.agent = ChatAgent(
            system_message=(
                "You are a network reconnaissance specialist. "
                "Use the available tools to analyze networks, "
                "find IP addresses, and identify technologies."
            ),
            model=self.model,
            tools=all_tools,
        )
        
        # Add MemoryToolkit to agent
        memory_toolkit = MemoryToolkit(agent=self.agent)
        for tool in memory_toolkit.get_tools():
            self.agent.add_tool(tool)
        
        logger.info("NetworkAnalyzerAgent initialized with tools and memory")

    async def analyze_network(self, query: str) -> Dict[str, Any]:
        """Analyze network using available tools.
        
        Args:
            query: Network analysis query
            
        Returns:
            Analysis results
        """
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "response": response.msg.content if hasattr(response, 'msg') else str(response),
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Network analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools.
        
        Returns:
            List of tool definitions
        """
        return self.agent.tools if hasattr(self.agent, "tools") else []


class SocialMediaIntelligenceAgent:
    """Social media intelligence agent with CAMEL-AI toolkit integration."""

    def __init__(
        self,
        model_type: ModelType = ModelType.GPT_5,
        sociallinks_api_key: Optional[str] = None,
    ):
        """Initialize Social Media Intelligence Agent.
        
        Args:
            model_type: The model type to use for the agent
            sociallinks_api_key: Social Links API key (optional)
        """
        # Create model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        # Initialize toolkits
        all_tools = []
        
        self.social_media_toolkit = SocialMediaToolkit()
        social_tools = self.social_media_toolkit.get_tools()
        all_tools.extend(social_tools)
        
        if sociallinks_api_key:
            self.social_links_toolkit = SocialLinksToolkit(sociallinks_api_key)
            social_links_tools = self.social_links_toolkit.get_tools()
            all_tools.extend(social_links_tools)
        else:
            self.social_links_toolkit = None
            logger.warning("Social Links toolkit not initialized - missing API key")
        
        # Create agent with tools
        self.agent = ChatAgent(
            system_message=(
                "You are a social media intelligence specialist. "
                "Use the available tools to find people, companies, "
                "and profiles across social platforms."
            ),
            model=self.model,
            tools=all_tools,
        )
        
        # Add MemoryToolkit to agent
        memory_toolkit = MemoryToolkit(agent=self.agent)
        for tool in memory_toolkit.get_tools():
            self.agent.add_tool(tool)
        
        logger.info("SocialMediaIntelligenceAgent initialized with tools and memory")

    async def search_social_profiles(self, query: str) -> Dict[str, Any]:
        """Search for social profiles using available tools.
        
        Args:
            query: Social profile search query
            
        Returns:
            Search results
        """
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "response": response.msg.content if hasattr(response, 'msg') else str(response),
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Social profile search failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools.
        
        Returns:
            List of tool definitions
        """
        return self.agent.tools if hasattr(self.agent, "tools") else []


class DomainIntelligenceAgent:
    """Domain intelligence agent with CAMEL-AI toolkit integration."""

    def __init__(
        self,
        model_type: ModelType = ModelType.GPT_5,
        maltego_api_key: Optional[str] = None,
        censys_api_id: Optional[str] = None,
        censys_api_secret: Optional[str] = None,
    ):
        """Initialize Domain Intelligence Agent.
        
        Args:
            model_type: The model type to use for the agent
            maltego_api_key: Maltego API key (optional)
            censys_api_id: Censys API ID (optional)
            censys_api_secret: Censys API secret (optional)
        """
        # Create model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        # Initialize toolkits with API credentials
        all_tools = []
        
        if maltego_api_key:
            self.maltego_toolkit = MaltegoToolkit(maltego_api_key)
            maltego_tools = self.maltego_toolkit.get_tools()
            all_tools.extend(maltego_tools)
        else:
            self.maltego_toolkit = None
            logger.warning("Maltego toolkit not initialized - missing API key")
        
        if censys_api_id and censys_api_secret:
            self.censys_toolkit = CensysToolkit(censys_api_id, censys_api_secret)
            censys_tools = self.censys_toolkit.get_tools()
            all_tools.extend(censys_tools)
        else:
            self.censys_toolkit = None
            logger.warning("Censys toolkit not initialized - missing API credentials")
        
        # Create agent with tools
        self.agent = ChatAgent(
            system_message=(
                "You are a domain intelligence specialist. "
                "Use the available tools to analyze domains, "
                "find related entities, and identify infrastructure."
            ),
            model=self.model,
            tools=all_tools,
        )
        
        # Add MemoryToolkit to agent
        memory_toolkit = MemoryToolkit(agent=self.agent)
        for tool in memory_toolkit.get_tools():
            self.agent.add_tool(tool)
        
        logger.info("DomainIntelligenceAgent initialized with tools and memory")

    async def analyze_domain(self, query: str) -> Dict[str, Any]:
        """Analyze domain using available tools.
        
        Args:
            query: Domain analysis query
            
        Returns:
            Analysis results
        """
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "response": response.msg.content if hasattr(response, 'msg') else str(response),
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Domain analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools.
        
        Returns:
            List of tool definitions
        """
        return self.agent.tools if hasattr(self.agent, "tools") else []


class DataBreachIntelligenceAgent:
    """Data breach intelligence agent with CAMEL-AI toolkit integration."""

    def __init__(
        self,
        model_type: ModelType = ModelType.GPT_5,
        liferaft_api_key: Optional[str] = None,
    ):
        """Initialize Data Breach Intelligence Agent.
        
        Args:
            model_type: The model type to use for the agent
            liferaft_api_key: Liferaft API key (optional)
        """
        # Create model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        # Initialize toolkit with API credentials
        if liferaft_api_key:
            self.liferaft_toolkit = LiferaftToolkit(liferaft_api_key)
            tools = self.liferaft_toolkit.get_tools()
        else:
            self.liferaft_toolkit = None
            tools = []
            logger.warning("Liferaft toolkit not initialized - missing API key")
        
        # Create agent with tools
        self.agent = ChatAgent(
            system_message=(
                "You are a data breach intelligence specialist. "
                "Use the available tools to search for breaches, "
                "find compromised data, and analyze breach details."
            ),
            model=self.model,
            tools=tools,
        )
        
        # Add MemoryToolkit to agent
        memory_toolkit = MemoryToolkit(agent=self.agent)
        for tool in memory_toolkit.get_tools():
            self.agent.add_tool(tool)
        
        logger.info("DataBreachIntelligenceAgent initialized with tools and memory")

    async def search_breaches(self, query: str) -> Dict[str, Any]:
        """Search for data breaches using available tools.
        
        Args:
            query: Breach search query
            
        Returns:
            Search results
        """
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "response": response.msg.content if hasattr(response, 'msg') else str(response),
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Breach search failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools.
        
        Returns:
            List of tool definitions
        """
        return self.agent.tools if hasattr(self.agent, "tools") else []


# Agent registry for easy access
AGENT_REGISTRY = {
    "network_analyzer": NetworkAnalyzerAgent,
    "social_media_intelligence": SocialMediaIntelligenceAgent,
    "domain_intelligence": DomainIntelligenceAgent,
    "data_breach_intelligence": DataBreachIntelligenceAgent,
}


def get_agent(agent_name: str) -> Optional[Any]:
    """Get agent by name.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Agent instance or None
    """
    agent_class = AGENT_REGISTRY.get(agent_name)
    if agent_class:
        return agent_class()
    logger.warning(f"Agent {agent_name} not found")
    return None


def list_available_agents() -> List[str]:
    """List all available agents.
    
    Returns:
        List of agent names
    """
    return list(AGENT_REGISTRY.keys())
