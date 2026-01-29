"""Palentir OSINT - FastAPI Main Application.

Main FastAPI application with all routes and middleware.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from kitten_palentir.config.settings import Settings, get_settings
from kitten_palentir.api.routes import orchestration, tasks, workforce, graph, qa
from kitten_palentir.api.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    ErrorHandlingMiddleware,
)
from kitten_palentir.agents.task_orchestrator_agent import TaskOrchestratorAgent
from kitten_palentir.workforce.camel_integrated_workforce import PalentirCAMELWorkforce
from kitten_palentir.services.graph_visualization import GraphVisualizationService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Palentir OSINT API...")
    logger.info(f"Environment: {settings.environment or settings.app_env}")
    logger.info(f"Debug: {settings.debug}")

    try:
        logger.info("Initializing services...")
        
        # Initialize services
        settings = get_settings()
        
        # Initialize task orchestrator
        try:
            orchestrator = TaskOrchestratorAgent(skip_agent_init=False)
            orchestration.set_orchestrator(orchestrator)
            tasks.set_orchestrator(orchestrator)
            logger.info("Task orchestrator initialized")
        except Exception as e:
            logger.warning(f"Task orchestrator initialization failed: {e}")
        
        # Initialize workforce
        try:
            workforce_instance = PalentirCAMELWorkforce(
                description="Palentir OSINT Workforce",
                enable_mcp=False,
                share_memory=True,
                neo4j_url=settings.effective_neo4j_uri,
                neo4j_username=settings.neo4j_username,
                neo4j_password=settings.neo4j_password,
            )
            workforce.set_workforce(workforce_instance)
            qa.set_services(workforce=workforce_instance)
            logger.info("Workforce initialized")
        except Exception as e:
            logger.warning(f"Workforce initialization failed: {e}")
        
        # Initialize graph service
        try:
            graph_service = GraphVisualizationService()
            graph.set_graph_service(graph_service)
            qa.set_services(graph_service=graph_service)
            logger.info("Graph service initialized")
        except Exception as e:
            logger.warning(f"Graph service initialization failed: {e}")
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Palentir OSINT API...")
    try:
        logger.info("Cleaning up resources...")
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


# Create FastAPI application
app = FastAPI(
    title="Palentir OSINT API",
    description="Advanced OSINT Intelligence Platform with Multi-Agent Orchestration",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# Add middleware (order matters - last added is first executed)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)


# Include routers
app.include_router(orchestration.router)
app.include_router(tasks.router)
app.include_router(workforce.router)
app.include_router(graph.router)
app.include_router(qa.router)


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Palentir OSINT API",
        "version": "2.0.0",
    }


@app.get("/api/health")
async def api_health_check() -> Dict[str, Any]:
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "Palentir OSINT API",
        "version": "2.0.0",
        "environment": settings.environment or settings.app_env,
    }


@app.get("/api/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    try:
        return {
            "ready": True,
            "service": "Palentir OSINT API",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e),
        }


@app.get("/api/info")
async def api_info() -> Dict[str, Any]:
    """API information endpoint."""
    return {
        "name": "Palentir OSINT API",
        "version": "2.0.0",
        "description": "Advanced OSINT Intelligence Platform",
        "environment": settings.environment or settings.app_env,
        "debug": settings.debug,
        "endpoints": {
            "tasks": "/api/v1/tasks",
            "workforce": "/api/v1/workforce",
            "graph": "/api/v1/graph",
            "qa": "/api/v1/qa",
            "orchestration": "/api/v1/orchestration",
        },
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json",
        },
    }


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "message": "Welcome to Palentir OSINT API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/health",
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "kitten_palentir.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
