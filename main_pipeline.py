#!/usr/bin/env python3
"""Palentir OSINT - Pipeline Workforce with MCP Server.

Demonstrates CAMEL-AI pipeline fork/join with social media intelligence.
"""

import asyncio
import logging
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import get_settings
from workforce.pipeline_workforce import PalentirPipelineWorkforce
from agents.social_media_agent import SocialMediaIntelligenceAgent
from camel.tasks import Task


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global workforce instance
workforce: PalentirPipelineWorkforce = None


@click.group()
def cli():
    """Palentir OSINT - Pipeline Workforce with Social Media Intelligence."""
    load_dotenv()


@cli.command()
@click.option("--company", prompt="Company name", help="Company to investigate")
@click.option("--depth", default="full", help="Investigation depth: quick or full")
async def investigate_company(company: str, depth: str):
    """Run company investigation with pipeline fork/join.

    Args:
        company: Company name
        depth: Investigation depth
    """
    global workforce

    logger.info(f"Starting company investigation: {company}")

    settings = get_settings()

    # Initialize pipeline workforce
    workforce = PalentirPipelineWorkforce(
        neo4j_url=settings.neo4j_uri,
        neo4j_user=settings.neo4j_username,
        neo4j_password=settings.neo4j_password,
    )

    # Add social media agent
    social_agent = workforce.add_agent(
        "SocialMediaIntelligence",
        "SocialMediaIntelligenceSpecialist",
        "Gather social media intelligence from LinkedIn, Facebook, Instagram",
    )

    # Create main task
    main_task = Task(
        content=f"Investigate company: {company}",
        id=f"task_company_{company}",
    )

    # Define subtask generator
    def generate_subtasks(summary):
        """Generate parallel subtasks based on main task summary."""
        return [
            Task(
                content=f"Search LinkedIn for {company} employees and key persons",
                id=f"task_linkedin_{company}",
            ),
            Task(
                content=f"Search Facebook for {company} official pages and presence",
                id=f"task_facebook_{company}",
            ),
            Task(
                content=f"Search Instagram for {company} profiles and accounts",
                id=f"task_instagram_{company}",
            ),
            Task(
                content=f"Analyze company structure and hierarchy from social profiles",
                id=f"task_hierarchy_{company}",
            ),
            Task(
                content=f"Extract connections and relationships for {company}",
                id=f"task_connections_{company}",
            ),
        ]

    # Execute pipeline
    logger.info("Executing pipeline with fork/join pattern")
    result = await workforce.process_pipeline(main_task, generate_subtasks)

    logger.info(f"Investigation completed: {company}")
    logger.info(f"Result: {result}")

    # Cleanup
    await workforce.close()


@cli.command()
@click.option("--person", prompt="Person name", help="Person to investigate")
async def investigate_person(person: str):
    """Run person investigation with social media toolkit.

    Args:
        person: Person name
    """
    logger.info(f"Starting person investigation: {person}")

    # Initialize social media agent
    agent = SocialMediaIntelligenceAgent()

    # Investigate person
    results = await agent.investigate_person(person)

    logger.info(f"Investigation completed: {person}")
    logger.info(f"Results: {results}")

    # Generate report
    report = await agent.generate_intelligence_report(results)
    logger.info(f"Intelligence Report:\n{report}")


@cli.command()
@click.option("--company", prompt="Company name", help="Company to investigate")
async def identify_key_persons(company: str):
    """Identify key persons in a company.

    Args:
        company: Company name
    """
    logger.info(f"Identifying key persons in: {company}")

    # Initialize social media agent
    agent = SocialMediaIntelligenceAgent()

    # Identify key persons
    key_persons = await agent.identify_key_persons(company)

    logger.info(f"Found {len(key_persons)} key persons:")
    for person in key_persons:
        logger.info(f"  - {person['name']} ({person['headline']})")


@cli.command()
def mcp_server():
    """Start Palentir OSINT as MCP server.

    Converts the workforce to an MCP server for client integration.
    """
    logger.info("Starting Palentir OSINT as MCP server")

    settings = get_settings()

    # Initialize pipeline workforce
    workforce_instance = PalentirPipelineWorkforce(
        neo4j_url=settings.neo4j_uri,
        neo4j_user=settings.neo4j_username,
        neo4j_password=settings.neo4j_password,
    )

    # Add agents
    workforce_instance.add_agent(
        "SocialMediaIntelligence",
        "SocialMediaIntelligenceSpecialist",
        "Gather social media intelligence",
    )

    try:
        # Convert to MCP server
        logger.info("Converting workforce to MCP server...")
        mcp_server_instance = workforce_instance.workforce.to_mcp(
            name="Palentir-OSINT",
            description="OSINT Intelligence Platform with Social Media Toolkit",
            port=8001,
        )

        logger.info("MCP Server started on port 8001")
        logger.info("Press Ctrl+C to stop")

        # Run MCP server
        mcp_server_instance.run()

    except KeyboardInterrupt:
        logger.info("MCP Server stopped")
    except Exception as e:
        logger.error(f"MCP Server error: {e}")


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
