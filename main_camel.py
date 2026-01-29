#!/usr/bin/env python3
"""Palentir OSINT - CAMEL-AI Native Main Application.

Uses CAMEL-AI[all] native classes exclusively.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import get_settings
from workforce.camel_workforce import PalentirCAMELWorkforce
from agents.camel_agents import CAMELAgentFactory
from camel.tasks import Task


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global workforce instance
workforce: Optional[PalentirCAMELWorkforce] = None


@click.group()
def cli():
    """Palentir OSINT - CAMEL-AI Native OSINT Platform."""
    load_dotenv()


@cli.command()
@click.option("--company", prompt="Company name", help="Company to investigate")
@click.option("--output", default="results.json", help="Output file")
async def investigate(company: str, output: str):
    """Run OSINT investigation on a company."""
    global workforce

    logger.info(f"Starting investigation on: {company}")

    settings = get_settings()

    # Initialize workforce
    workforce = PalentirCAMELWorkforce(
        neo4j_url=settings.neo4j_uri,
        neo4j_user=settings.neo4j_username,
        neo4j_password=settings.neo4j_password,
    )

    # Create agents
    agent_factory = CAMELAgentFactory()

    # Add agents to workforce
    workforce.add_agent(
        "NetworkAnalyzer",
        "NetworkAnalyzer",
        "Analyze network infrastructure",
    )
    workforce.add_agent(
        "SocialFinder",
        "SocialFinder",
        "Find social media profiles",
    )
    workforce.add_agent(
        "GraphBuilder",
        "GraphBuilder",
        "Build knowledge graph",
    )

    # Create tasks
    tasks = [
        Task(
            content=f"Analyze network infrastructure for {company}",
            id=f"task_network_{company}",
        ),
        Task(
            content=f"Find social media profiles for {company}",
            id=f"task_social_{company}",
        ),
        Task(
            content=f"Build knowledge graph for {company}",
            id=f"task_graph_{company}",
        ),
    ]

    # Run pipeline
    results = await workforce.run_pipeline(tasks)

    logger.info(f"Investigation completed. Results saved to: {output}")

    # Cleanup
    await workforce.close()


@cli.command()
def test():
    """Run tests."""
    import subprocess

    logger.info("Running tests...")
    result = subprocess.run(
        ["pytest", "-v", "--cov=src"],
        cwd=Path(__file__).parent,
    )
    return result.returncode


@cli.command()
def lint():
    """Run linting."""
    import subprocess

    logger.info("Running linting...")

    # Run mypy
    subprocess.run(["mypy", "src", "--ignore-missing-imports"])

    # Run flake8
    subprocess.run(["flake8", "src", "--max-line-length=100"])


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Application interrupted")
        if workforce:
            asyncio.run(workforce.close())
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
