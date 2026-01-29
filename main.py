#!/usr/bin/env python3
"""
Palentir OSINT - Main Application Entry Point

This module serves as the main entry point for the Palentir OSINT platform.
It initializes the application, sets up logging, and starts the appropriate
service based on command-line arguments.
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import Settings, setup_logging


logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set logging level",
)
def cli(debug: bool, log_level: str) -> None:
    """Palentir OSINT - Advanced OSINT Intelligence Platform."""
    load_dotenv()
    setup_logging(debug=debug, log_level=log_level)
    logger.info("Palentir OSINT initialized")


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="API host",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="API port",
)
@click.option(
    "--workers",
    type=int,
    default=4,
    help="Number of workers",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload",
)
def api(host: str, port: int, workers: int, reload: bool) -> None:
    """Start FastAPI backend server."""
    import uvicorn

    logger.info(f"Starting API server on {host}:{port}")

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level="info",
    )


@cli.command()
@click.option(
    "--port",
    type=int,
    default=8501,
    help="Streamlit port",
)
def frontend(port: int) -> None:
    """Start Streamlit frontend."""
    import subprocess

    logger.info(f"Starting Streamlit frontend on port {port}")

    subprocess.run(
        [
            "streamlit",
            "run",
            "src/frontend/app.py",
            "--server.port",
            str(port),
        ]
    )


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="API host",
)
@click.option(
    "--api-port",
    type=int,
    default=8000,
    help="API port",
)
@click.option(
    "--frontend-port",
    type=int,
    default=8501,
    help="Frontend port",
)
def dev(host: str, api_port: int, frontend_port: int) -> None:
    """Start development environment (API + Frontend)."""
    import subprocess
    import time

    logger.info("Starting development environment...")

    # Start API in background
    api_process = subprocess.Popen(
        [
            sys.executable,
            __file__,
            "api",
            "--host",
            host,
            "--port",
            str(api_port),
            "--reload",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for API to start
    time.sleep(2)

    # Start frontend
    try:
        subprocess.run(
            [
                sys.executable,
                __file__,
                "frontend",
                "--port",
                str(frontend_port),
            ]
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        api_process.terminate()
        api_process.wait()


@cli.command()
def test() -> None:
    """Run tests."""
    import subprocess

    logger.info("Running tests...")
    result = subprocess.run(
        ["pytest", "-v", "--cov=src", "--cov-report=term-missing"],
        cwd=Path(__file__).parent,
    )
    sys.exit(result.returncode)


@cli.command()
def lint() -> None:
    """Run linting."""
    import subprocess

    logger.info("Running linting...")

    # Run flake8
    subprocess.run(["flake8", "src", "tests"])

    # Run mypy
    subprocess.run(["mypy", "src"])


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["json", "html"]),
    default="html",
    help="Report format",
)
def coverage(format: str) -> None:
    """Generate coverage report."""
    import subprocess

    logger.info("Generating coverage report...")

    if format == "html":
        subprocess.run(
            ["pytest", "--cov=src", "--cov-report=html"],
            cwd=Path(__file__).parent,
        )
        logger.info("Coverage report generated in htmlcov/index.html")
    else:
        subprocess.run(
            ["pytest", "--cov=src", "--cov-report=json"],
            cwd=Path(__file__).parent,
        )
        logger.info("Coverage report generated in .coverage.json")


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
