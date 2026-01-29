"""Palentir OSINT - CAMEL-AI Native Agents.

Uses CAMEL-AI[all] native classes exclusively.
"""

import logging
from typing import Dict, Any, Optional, List

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType


logger = logging.getLogger(__name__)


class CAMELAgentFactory:
    """Factory for creating CAMEL-AI agents."""

    def __init__(self, model_type: str = "gpt-4"):
        """Initialize agent factory.

        Args:
            model_type: Model type to use
        """
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4,
        )
        logger.info(f"Agent factory initialized with model: {model_type}")

    def create_network_analyzer(self) -> ChatAgent:
        """Create network analyzer agent.

        Returns:
            ChatAgent for network analysis
        """
        return ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="NetworkAnalyzer",
                content=(
                    "You are a network reconnaissance specialist. "
                    "Analyze domains, IP addresses, and network infrastructure. "
                    "Return findings in structured JSON format."
                ),
            ),
            model=self.model,
        )

    def create_social_finder(self) -> ChatAgent:
        """Create social media finder agent.

        Returns:
            ChatAgent for social media intelligence
        """
        return ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="SocialFinder",
                content=(
                    "You are a social media intelligence specialist. "
                    "Find and analyze social media profiles for companies and people. "
                    "Return findings in structured JSON format."
                ),
            ),
            model=self.model,
        )

    def create_graph_builder(self) -> ChatAgent:
        """Create graph builder agent.

        Returns:
            ChatAgent for building knowledge graphs
        """
        return ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="GraphBuilder",
                content=(
                    "You are a knowledge graph specialist. "
                    "Build relationships and connections between entities. "
                    "Identify patterns and connections in intelligence data."
                ),
            ),
            model=self.model,
        )

    def create_memory_agent(self) -> ChatAgent:
        """Create memory management agent.

        Returns:
            ChatAgent for memory management
        """
        return ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="MemoryAgent",
                content=(
                    "You are a memory management specialist. "
                    "Store and retrieve important intelligence information. "
                    "Maintain context and historical data."
                ),
            ),
            model=self.model,
        )

    def create_synthesizer(self) -> ChatAgent:
        """Create synthesizer agent.

        Returns:
            ChatAgent for synthesizing intelligence
        """
        return ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="Synthesizer",
                content=(
                    "You are an intelligence synthesizer. "
                    "Combine findings from multiple sources into comprehensive reports. "
                    "Identify key insights and recommendations."
                ),
            ),
            model=self.model,
        )

    def create_custom_agent(
        self,
        role_name: str,
        description: str,
    ) -> ChatAgent:
        """Create a custom agent.

        Args:
            role_name: Role name
            description: Agent description

        Returns:
            ChatAgent with custom role
        """
        return ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name=role_name,
                content=description,
            ),
            model=self.model,
        )
