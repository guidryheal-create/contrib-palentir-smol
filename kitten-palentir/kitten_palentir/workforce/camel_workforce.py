"""Palentir OSINT - CAMEL-AI Native Workforce Implementation.

This module uses CAMEL-AI[all] native classes exclusively:
- camel.societies.workforce.Workforce
- camel.agents.ChatAgent
- camel.tasks.Task
- camel.storages for memory
- camel.toolkits for tools
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.tasks import Task
from camel.societies.workforce import Workforce, WorkforceMode
from camel.storages import Neo4jGraph
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Shared state models using Pydantic
class CompanyFact(BaseModel):
    """Company intelligence fact."""

    timestamp: str
    company_name: str
    fact_type: str
    content: str
    source: str
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntelligenceReport(BaseModel):
    """Intelligence report from agents."""

    company_name: str
    report_type: str
    findings: List[str]
    connections: List[Dict[str, str]]
    timestamp: str
    agent_name: str
    confidence: float


class SharedIntelligenceState(BaseModel):
    """Shared intelligence state between agents."""

    facts: Dict[str, CompanyFact] = Field(default_factory=dict)
    reports: Dict[str, IntelligenceReport] = Field(default_factory=dict)
    graph_nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    graph_edges: List[Dict[str, str]] = Field(default_factory=list)


class PalentirCAMELWorkforce:
    """CAMEL-AI native workforce for Palentir OSINT.

    Uses CAMEL-AI[all] native classes exclusively.
    """

    def __init__(
        self,
        model_platform: str = "openai",
        model_type: str = "gpt-4",
        neo4j_url: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
    ):
        """Initialize CAMEL-AI workforce.

        Args:
            model_platform: Model platform (openai, etc.)
            model_type: Model type (gpt-4, etc.)
            neo4j_url: Neo4j connection URL
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        # Create model using CAMEL-AI ModelFactory
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4,
        )

        # Initialize Neo4j graph memory
        self.graph = Neo4jGraph(
            url=neo4j_url,
            username=neo4j_user,
            password=neo4j_password,
        )

        # Shared state
        self.shared_state = SharedIntelligenceState()

        # Create CAMEL-AI Workforce
        self.coordinator_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="Coordinator",
                content="Coordinate OSINT intelligence gathering and ensure structured outputs",
            ),
            model=self.model,
        )

        self.task_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="TaskPlanner",
                content="Plan and decompose OSINT reconnaissance tasks",
            ),
            model=self.model,
        )

        self.workforce = Workforce(
            name="Palentir OSINT Workforce",
            coordinator_agent=self.coordinator_agent,
            task_agent=self.task_agent,
            mode=WorkforceMode.PIPELINE,
        )

        logger.info("CAMEL-AI Workforce initialized")

    def add_agent(self, name: str, role: str, description: str) -> ChatAgent:
        """Add an agent to the workforce.

        Args:
            name: Agent name
            role: Agent role
            description: Agent description

        Returns:
            Created ChatAgent
        """
        agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name=role,
                content=description,
            ),
            model=self.model,
        )

        self.workforce.add_single_agent_worker(name, agent)
        logger.info(f"Added agent: {name}")

        return agent

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Process a task using CAMEL-AI workforce.

        Args:
            task: CAMEL-AI Task to process

        Returns:
            Task result
        """
        logger.info(f"Processing task: {task.task_id}")

        try:
            # Process task through workforce
            result = await self.workforce.process_task_async(task)
            return {
                "task_id": task.task_id,
                "status": "completed",
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            return {
                "task_id": task.task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def add_graph_fact(self, fact: CompanyFact) -> None:
        """Add a fact to the knowledge graph.

        Args:
            fact: CompanyFact to add
        """
        try:
            # Add to shared state
            key = f"{fact.company_name}:{fact.fact_type}:{fact.timestamp}"
            self.shared_state.facts[key] = fact

            # Add to Neo4j graph
            subject = f"COMPANY:{fact.company_name}"
            obj = f"FACT:{fact.fact_type}:{fact.content[:50]}"
            relation = "HAS_FACT"

            self.graph.add_triplet(subj=subject, obj=obj, rel=relation)
            logger.info(f"Added fact to graph: {key}")

        except Exception as e:
            logger.error(f"Error adding fact to graph: {e}")

    def add_graph_connection(
        self,
        source: str,
        target: str,
        relation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a connection to the knowledge graph.

        Args:
            source: Source entity
            target: Target entity
            relation: Relationship type
            metadata: Additional metadata
        """
        try:
            self.graph.add_triplet(subj=source, obj=target, rel=relation)

            # Track in shared state
            edge = {
                "source": source,
                "target": target,
                "relation": relation,
                "metadata": metadata or {},
            }
            self.shared_state.graph_edges.append(edge)

            logger.info(f"Added connection: {source} -> {target}")

        except Exception as e:
            logger.error(f"Error adding connection: {e}")

    def get_shared_state(self) -> SharedIntelligenceState:
        """Get shared intelligence state.

        Returns:
            Current shared state
        """
        return self.shared_state

    async def run_pipeline(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """Run a pipeline of tasks.

        Args:
            tasks: List of tasks to process

        Returns:
            List of results
        """
        logger.info(f"Running pipeline with {len(tasks)} tasks")

        results = []
        for task in tasks:
            result = await self.process_task(task)
            results.append(result)

        logger.info("Pipeline completed")
        return results

    async def close(self) -> None:
        """Close workforce resources."""
        logger.info("Closing CAMEL-AI Workforce")
        try:
            self.graph.close()
        except Exception as e:
            logger.error(f"Error closing graph: {e}")
