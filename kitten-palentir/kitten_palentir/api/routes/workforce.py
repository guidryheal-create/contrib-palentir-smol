"""Palentir OSINT - Workforce API Routes.

Provides REST API endpoints for workforce management.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from kitten_palentir.api.models.schemas import (
    WorkforceInfo,
    AgentInfo,
    ErrorResponse,
)
from kitten_palentir.workforce.camel_integrated_workforce import PalentirCAMELWorkforce

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workforce", tags=["workforce"])

# Global workforce instance (would be injected via dependency injection in production)
_workforce: Optional[PalentirCAMELWorkforce] = None


def set_workforce(wf: PalentirCAMELWorkforce):
    """Set the workforce instance.

    Args:
        wf: Palentir CAMEL Workforce instance
    """
    global _workforce
    _workforce = wf
    logger.info("Workforce instance set for workforce router")


def get_workforce() -> PalentirCAMELWorkforce:
    """Get the workforce instance.

    Returns:
        Palentir CAMEL Workforce instance

    Raises:
        HTTPException: If workforce is not initialized
    """
    if _workforce is None:
        raise HTTPException(
            status_code=503,
            detail="Workforce not initialized. Please wait for service to be ready.",
        )
    return _workforce


@router.get("/info", response_model=WorkforceInfo)
async def get_workforce_info() -> WorkforceInfo:
    """Get workforce information.

    Returns:
        Workforce information
    """
    try:
        workforce = get_workforce()

        info = workforce.get_workforce_info()

        return WorkforceInfo(
            description=info.get("description", "Palentir OSINT Workforce"),
            agent_count=info.get("agent_count", 0),
            agents=info.get("agents", []),
            share_memory=True,  # Default from workforce
            mcp_enabled=False,  # Would need to check workforce state
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workforce info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get workforce info: {str(e)}")


@router.get("/agents", response_model=List[str])
async def list_agents() -> List[str]:
    """List all available agents.

    Returns:
        List of agent names
    """
    try:
        workforce = get_workforce()

        agents = workforce.list_agents()

        return agents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/agents/{agent_name}", response_model=AgentInfo)
async def get_agent_info(agent_name: str = Path(..., description="Agent name")) -> AgentInfo:
    """Get information about a specific agent.

    Args:
        agent_name: Name of the agent

    Returns:
        Agent information
    """
    try:
        workforce = get_workforce()

        agent = workforce.get_agent(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        tools = workforce.get_agent_tools(agent_name)

        return AgentInfo(
            name=agent_name,
            description=f"Agent: {agent_name}",
            tools_count=len(tools),
            tools=[str(tool) for tool in tools[:20]],  # Limit to first 20 tools
            status="active",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")


@router.get("/agents/{agent_name}/tools", response_model=List[dict])
async def get_agent_tools(agent_name: str = Path(..., description="Agent name")) -> List[dict]:
    """Get tools available to a specific agent.

    Args:
        agent_name: Name of the agent

    Returns:
        List of tool information
    """
    try:
        workforce = get_workforce()

        agent = workforce.get_agent(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        tools = workforce.get_agent_tools(agent_name)

        # Convert tools to dict format
        tool_list = []
        for tool in tools:
            if isinstance(tool, dict):
                tool_list.append(tool)
            else:
                tool_list.append({"name": str(tool), "type": type(tool).__name__})

        return tool_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agent tools: {str(e)}")


@router.post("/agents/{agent_name}/process")
async def process_with_agent(
    agent_name: str = Path(..., description="Agent name"),
    query: str = Query(..., description="Query to process", min_length=1),
) -> dict:
    """Process a query using a specific agent.

    Args:
        agent_name: Name of the agent
        query: Query to process

    Returns:
        Processing result
    """
    try:
        workforce = get_workforce()

        agent = workforce.get_agent(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        logger.info(f"Processing query with agent {agent_name}: {query[:50]}...")

        result = await workforce.process_task(query, agent_name=agent_name)

        return {
            "agent": agent_name,
            "query": query,
            "result": result,
            "status": result.get("status", "unknown"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

