"""Palentir OSINT - Task Orchestrator Example.

Demonstrates the Task Orchestrator Agent with CAMEL-AI Workforce.
"""

import asyncio
import logging
from typing import Dict, Any

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.societies.workforce import Workforce

from src.agents.task_orchestrator_agent import (
    TaskOrchestratorAgent,
    ExecutionMode,
    TaskExecutionStatus,
)
from src.services.task_generation_service import TaskGenerationService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_sample_workforce() -> Workforce:
    """Create a sample CAMEL-AI Workforce with agents.

    Returns:
        Workforce instance
    """
    logger.info("Creating sample workforce...")

    # Create workforce
    workforce = Workforce(description="OSINT Investigation Team")

    # Create Social Media Agent
    social_media_msg = BaseMessage.make_assistant_message(
        role_name="SocialMediaIntelligenceAgent",
        content=(
            "You are a Social Media Intelligence Agent. Your role is to search for and analyze "
            "information about people and companies across social media platforms including "
            "LinkedIn, Twitter, Facebook, and Instagram. You provide insights about social "
            "connections, public profiles, and online presence."
        ),
    )
    social_media_agent = ChatAgent(system_message=social_media_msg)
    workforce.add_single_agent_worker(
        description="Social Media Intelligence Agent",
        worker=social_media_agent,
    )

    # Create Domain Analysis Agent
    domain_msg = BaseMessage.make_assistant_message(
        role_name="DomainAnalysisAgent",
        content=(
            "You are a Domain Analysis Agent. Your role is to analyze domains, perform DNS lookups, "
            "check SSL certificates, and identify technologies used on websites. You provide "
            "comprehensive domain intelligence."
        ),
    )
    domain_agent = ChatAgent(system_message=domain_msg)
    workforce.add_single_agent_worker(
        description="Domain Analysis Agent",
        worker=domain_agent,
    )

    # Create Network Analyzer Agent
    network_msg = BaseMessage.make_assistant_message(
        role_name="NetworkAnalyzerAgent",
        content=(
            "You are a Network Analyzer Agent. Your role is to analyze network infrastructure, "
            "identify IP addresses, detect open ports, and identify services running on networks. "
            "You provide network reconnaissance intelligence."
        ),
    )
    network_agent = ChatAgent(system_message=network_msg)
    workforce.add_single_agent_worker(
        description="Network Analyzer Agent",
        worker=network_agent,
    )

    # Create Company Intelligence Agent
    company_msg = BaseMessage.make_assistant_message(
        role_name="CompanyIntelligenceAgent",
        content=(
            "You are a Company Intelligence Agent. Your role is to research companies, identify "
            "leadership teams, analyze business information, and provide company intelligence. "
            "You gather comprehensive organizational data."
        ),
    )
    company_agent = ChatAgent(system_message=company_msg)
    workforce.add_single_agent_worker(
        description="Company Intelligence Agent",
        worker=company_agent,
    )

    # Create Relationship Builder Agent
    relationship_msg = BaseMessage.make_assistant_message(
        role_name="RelationshipBuilderAgent",
        content=(
            "You are a Relationship Builder Agent. Your role is to identify connections between "
            "entities, build relationship graphs, and analyze organizational structures. You "
            "create comprehensive relationship intelligence."
        ),
    )
    relationship_agent = ChatAgent(system_message=relationship_msg)
    workforce.add_single_agent_worker(
        description="Relationship Builder Agent",
        worker=relationship_agent,
    )

    logger.info(f"Workforce created with {len(workforce.workers)} agents")
    return workforce


async def demonstrate_sequential_execution():
    """Demonstrate sequential task execution."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATION 1: Sequential Task Execution")
    logger.info("=" * 80)

    # Create workforce
    workforce = await create_sample_workforce()

    # Create services
    task_gen_service = TaskGenerationService()

    # Create orchestrator
    orchestrator = TaskOrchestratorAgent(
        workforce=workforce,
        task_generation_service=task_gen_service,
    )

    # Register callbacks
    async def on_task_start(task: Dict[str, Any]):
        logger.info(f"[CALLBACK] Task started: {task['task_id']}")

    async def on_task_complete(result):
        logger.info(f"[CALLBACK] Task completed: {result.task_id} ({result.execution_time:.2f}s)")

    async def on_task_failed(result):
        logger.error(f"[CALLBACK] Task failed: {result.task_id} - {result.error}")

    orchestrator.register_on_task_start(on_task_start)
    orchestrator.register_on_task_complete(on_task_complete)
    orchestrator.register_on_task_failed(on_task_failed)

    # Process query
    query = "Investigate company Tech Corp"
    logger.info(f"Processing query: {query}")

    results = await orchestrator.process_user_query(
        query=query,
        execution_mode=ExecutionMode.SEQUENTIAL,
    )

    # Display results
    logger.info(f"\nSequential Execution Results: {len(results)} tasks")
    for result in results:
        logger.info(f"  - {result.task_id}: {result.status.value} ({result.execution_time:.2f}s)")

    # Display status
    status = orchestrator.get_status()
    logger.info(f"\nOrchestrator Status:")
    logger.info(f"  - Queued: {status['queued_tasks']}")
    logger.info(f"  - Executing: {status['executing_tasks']}")
    logger.info(f"  - Completed: {status['completed_tasks']}")
    logger.info(f"  - Failed: {status['failed_tasks']}")


async def demonstrate_parallel_execution():
    """Demonstrate parallel task execution."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATION 2: Parallel Task Execution")
    logger.info("=" * 80)

    # Create workforce
    workforce = await create_sample_workforce()

    # Create services
    task_gen_service = TaskGenerationService()

    # Create orchestrator
    orchestrator = TaskOrchestratorAgent(
        workforce=workforce,
        task_generation_service=task_gen_service,
    )

    # Process query
    query = "Find person John Doe"
    logger.info(f"Processing query: {query}")

    results = await orchestrator.process_user_query(
        query=query,
        execution_mode=ExecutionMode.PARALLEL,
    )

    # Display results
    logger.info(f"\nParallel Execution Results: {len(results)} tasks")
    for result in results:
        logger.info(f"  - {result.task_id}: {result.status.value} ({result.execution_time:.2f}s)")

    # Display status
    status = orchestrator.get_status()
    logger.info(f"\nOrchestrator Status:")
    logger.info(f"  - Queued: {status['queued_tasks']}")
    logger.info(f"  - Executing: {status['executing_tasks']}")
    logger.info(f"  - Completed: {status['completed_tasks']}")
    logger.info(f"  - Failed: {status['failed_tasks']}")


async def demonstrate_fork_join_execution():
    """Demonstrate fork/join task execution."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATION 3: Fork/Join Task Execution")
    logger.info("=" * 80)

    # Create workforce
    workforce = await create_sample_workforce()

    # Create services
    task_gen_service = TaskGenerationService()

    # Create orchestrator
    orchestrator = TaskOrchestratorAgent(
        workforce=workforce,
        task_generation_service=task_gen_service,
    )

    # Process query
    query = "Analyze domain example.com"
    logger.info(f"Processing query: {query}")

    results = await orchestrator.process_user_query(
        query=query,
        execution_mode=ExecutionMode.FORK_JOIN,
    )

    # Display results
    logger.info(f"\nFork/Join Execution Results: {len(results)} tasks")
    for result in results:
        logger.info(f"  - {result.task_id}: {result.status.value} ({result.execution_time:.2f}s)")

    # Display status
    status = orchestrator.get_status()
    logger.info(f"\nOrchestrator Status:")
    logger.info(f"  - Queued: {status['queued_tasks']}")
    logger.info(f"  - Executing: {status['executing_tasks']}")
    logger.info(f"  - Completed: {status['completed_tasks']}")
    logger.info(f"  - Failed: {status['failed_tasks']}")


async def demonstrate_task_cancellation():
    """Demonstrate task cancellation."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATION 4: Task Cancellation")
    logger.info("=" * 80)

    # Create workforce
    workforce = await create_sample_workforce()

    # Create services
    task_gen_service = TaskGenerationService()

    # Create orchestrator
    orchestrator = TaskOrchestratorAgent(
        workforce=workforce,
        task_generation_service=task_gen_service,
    )

    # Process query
    query = "Investigate company Tech Corp"
    logger.info(f"Processing query: {query}")

    # Get queued tasks
    queued = orchestrator.get_queued_tasks()
    logger.info(f"Queued tasks: {len(queued)}")

    if queued:
        task_id = queued[0]["task_id"]
        logger.info(f"Cancelling task: {task_id}")

        cancelled = await orchestrator.cancel_task(task_id)
        logger.info(f"Task cancelled: {cancelled}")

    # Cancel all
    logger.info("Cancelling all tasks...")
    await orchestrator.cancel_all_tasks()

    status = orchestrator.get_status()
    logger.info(f"Remaining tasks: {status['total_tasks']}")


async def main():
    """Run all demonstrations."""
    logger.info("Starting Task Orchestrator Demonstrations")

    try:
        # Run demonstrations
        await demonstrate_sequential_execution()
        await demonstrate_parallel_execution()
        await demonstrate_fork_join_execution()
        await demonstrate_task_cancellation()

        logger.info("\n" + "=" * 80)
        logger.info("All demonstrations completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Demonstration failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
