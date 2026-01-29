"""
CAMEL-AI Integrated Agents with proper toolkit integration and error handling.
"""

import logging
from typing import Any, Dict, List, Optional

from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

logger = logging.getLogger(__name__)


class NetworkAnalyzerAgent:
    """Network reconnaissance agent with CAMEL-AI toolkit integration."""

    def __init__(self, model_type: ModelType = ModelType.GPT_3_5_TURBO):
        """Initialize Network Analyzer Agent."""
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        self.toolkits = {}
        self.tools = []
        self._initialize_toolkits()
        
        self.agent = ChatAgent(
            system_message=(
                "You are a network reconnaissance specialist. "
                "Use the available tools to analyze networks."
            ),
            model=self.model,
            tools=self.tools if self.tools else None,
        )
        
        logger.info("NetworkAnalyzerAgent initialized")

    def _initialize_toolkits(self) -> None:
        """Initialize toolkits with error handling."""
        try:
            from kitten_palentir.toolkits.advanced_osint_toolkit import CensysToolkit
            # Note: API credentials should be passed from settings or environment
            censys_api_id = "test_api_id"  # Should come from settings
            censys_api_secret = "test_api_secret"  # Should come from settings
            if censys_api_id and censys_api_secret:
                self.toolkits["censys"] = CensysToolkit(
                    api_id=censys_api_id,
                    api_secret=censys_api_secret,
                )
                self.tools.extend(self.toolkits["censys"].get_tools())
        except Exception as e:
            logger.warning(f"Could not initialize Censys toolkit: {e}")
        
        try:
            from kitten_palentir.toolkits.advanced_osint_toolkit import LiferaftToolkit
            # Note: API key should be passed from settings or environment
            liferaft_api_key = "test_api_key"  # Should come from settings
            if liferaft_api_key:
                self.toolkits["liferaft"] = LiferaftToolkit(liferaft_api_key)
                self.tools.extend(self.toolkits["liferaft"].get_tools())
        except Exception as e:
            logger.warning(f"Could not initialize Liferaft toolkit: {e}")

    async def analyze_network(self, query: str) -> Dict[str, Any]:
        """Analyze network using available tools."""
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Network analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools."""
        return self.tools


class SocialMediaIntelligenceAgent:
    """Social media intelligence agent."""

    def __init__(self, model_type: ModelType = ModelType.GPT_3_5_TURBO):
        """Initialize Social Media Intelligence Agent."""
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        self.toolkits = {}
        self.tools = []
        self._initialize_toolkits()
        
        self.agent = ChatAgent(
            system_message=(
                "You are a social media intelligence specialist. "
                "Use the available tools to find people and companies."
            ),
            model=self.model,
            tools=self.tools if self.tools else None,
        )
        
        logger.info("SocialMediaIntelligenceAgent initialized")

    def _initialize_toolkits(self) -> None:
        """Initialize toolkits with error handling."""
        try:
            from kitten_palentir.toolkits.social_media_toolkit import SocialMediaToolkit
            self.toolkits["social_media"] = SocialMediaToolkit()
            self.tools.extend(self.toolkits["social_media"].get_tools())
        except Exception as e:
            logger.warning(f"Could not initialize Social Media toolkit: {e}")
        
        try:
            from kitten_palentir.toolkits.advanced_osint_toolkit import SocialLinksToolkit
            # Note: API key should be passed from settings or environment
            sociallinks_api_key = "test_api_key"  # Should come from settings
            if sociallinks_api_key:
                self.toolkits["social_links"] = SocialLinksToolkit(sociallinks_api_key)
                self.tools.extend(self.toolkits["social_links"].get_tools())
        except Exception as e:
            logger.warning(f"Could not initialize Social Links toolkit: {e}")

    async def search_social_profiles(self, query: str) -> Dict[str, Any]:
        """Search for social profiles."""
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Social profile search failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools."""
        return self.tools


class DomainIntelligenceAgent:
    """Domain intelligence agent."""

    def __init__(self, model_type: ModelType = ModelType.GPT_3_5_TURBO):
        """Initialize Domain Intelligence Agent."""
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        self.toolkits = {}
        self.tools = []
        self._initialize_toolkits()
        
        self.agent = ChatAgent(
            system_message=(
                "You are a domain intelligence specialist. "
                "Use the available tools to analyze domains."
            ),
            model=self.model,
            tools=self.tools if self.tools else None,
        )
        
        logger.info("DomainIntelligenceAgent initialized")

    def _initialize_toolkits(self) -> None:
        """Initialize toolkits with error handling."""
        try:
            from kitten_palentir.toolkits.advanced_osint_toolkit import MaltegoToolkit
            # Note: API key should be passed from settings or environment
            maltego_api_key = "test_api_key"  # Should come from settings
            if maltego_api_key:
                self.toolkits["maltego"] = MaltegoToolkit(maltego_api_key)
                self.tools.extend(self.toolkits["maltego"].get_tools())
        except Exception as e:
            logger.warning(f"Could not initialize Maltego toolkit: {e}")
        
        try:
            from kitten_palentir.toolkits.advanced_osint_toolkit import CensysToolkit
            # Note: API credentials should be passed from settings or environment
            censys_api_id = "test_api_id"  # Should come from settings
            censys_api_secret = "test_api_secret"  # Should come from settings
            if censys_api_id and censys_api_secret:
                self.toolkits["censys"] = CensysToolkit(
                    api_id=censys_api_id,
                    api_secret=censys_api_secret,
                )
                self.tools.extend(self.toolkits["censys"].get_tools())
        except Exception as e:
            logger.warning(f"Could not initialize Censys toolkit: {e}")

    async def analyze_domain(self, query: str) -> Dict[str, Any]:
        """Analyze domain."""
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Domain analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools."""
        return self.tools


class DataBreachIntelligenceAgent:
    """Data breach intelligence agent."""

    def __init__(self, model_type: ModelType = ModelType.GPT_3_5_TURBO):
        """Initialize Data Breach Intelligence Agent."""
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=model_type,
        )
        
        self.toolkits = {}
        self.tools = []
        self._initialize_toolkits()
        
        self.agent = ChatAgent(
            system_message=(
                "You are a data breach intelligence specialist. "
                "Use the available tools to search for breaches."
            ),
            model=self.model,
            tools=self.tools if self.tools else None,
        )
        
        logger.info("DataBreachIntelligenceAgent initialized")

    def _initialize_toolkits(self) -> None:
        """Initialize toolkits with error handling."""
        try:
            from kitten_palentir.toolkits.advanced_osint_toolkit import LiferaftToolkit
            # Note: API key should be passed from settings or environment
            liferaft_api_key = "test_api_key"  # Should come from settings
            if liferaft_api_key:
                self.toolkits["liferaft"] = LiferaftToolkit(liferaft_api_key)
                self.tools.extend(self.toolkits["liferaft"].get_tools())
        except Exception as e:
            logger.warning(f"Could not initialize Liferaft toolkit: {e}")

    async def search_breaches(self, query: str) -> Dict[str, Any]:
        """Search for data breaches."""
        try:
            response = await self.agent.astep(query)
            return {
                "status": "success",
                "content": response.msg.content if hasattr(response, 'msg') else str(response),
                "tool_calls": response.info.get('tool_calls', []),
                "messages": [msg.content for msg in response.msgs] if hasattr(response, 'msgs') else [],
            }
        except Exception as e:
            logger.error(f"Breach search failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools."""
        return self.tools


AGENT_REGISTRY = {
    "network_analyzer": NetworkAnalyzerAgent,
    "social_media_intelligence": SocialMediaIntelligenceAgent,
    "domain_intelligence": DomainIntelligenceAgent,
    "data_breach_intelligence": DataBreachIntelligenceAgent,
}


def get_agent(agent_name: str) -> Optional[Any]:
    """Get agent by name."""
    agent_class = AGENT_REGISTRY.get(agent_name)
    if agent_class:
        return agent_class()
    logger.warning(f"Agent {agent_name} not found")
    return None


def list_available_agents() -> List[str]:
    """List all available agents."""
    return list(AGENT_REGISTRY.keys())
