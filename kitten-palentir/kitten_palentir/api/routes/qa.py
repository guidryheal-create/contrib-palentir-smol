"""Palentir OSINT - Question Answering API Routes.

Provides REST API endpoints for question answering over the knowledge graph.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from kitten_palentir.api.models.schemas import (
    QARequest,
    QAResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/qa", tags=["qa"])

# Global services (would be injected via dependency injection in production)
_workforce = None
_graph_service = None


def set_services(workforce=None, graph_service=None):
    """Set service instances.

    Args:
        workforce: Workforce instance (optional)
        graph_service: Graph service instance (optional)
    """
    global _workforce, _graph_service
    _workforce = workforce
    _graph_service = graph_service
    logger.info("Services set for QA router")


@router.post("/ask", response_model=QAResponse)
async def ask_question(request: QARequest) -> QAResponse:
    """Answer a question using the knowledge graph and workforce.

    Args:
        request: Question answering request

    Returns:
        Answer response
    """
    try:
        if not _workforce and not _graph_service:
            raise HTTPException(
                status_code=503,
                detail="QA service not available. Workforce or graph service required.",
            )

        logger.info(f"Processing question: {request.question[:50]}...")

        # Use workforce to process the question
        if _workforce:
            result = await _workforce.process_task(request.question)
            
            answer_content = ""
            if isinstance(result, dict):
                answer_content = result.get("result", {}).get("content", str(result))
            else:
                answer_content = str(result)

            sources = []
            if isinstance(result, dict) and result.get("result"):
                sources.append({
                    "type": "workforce",
                    "content": str(result.get("result")),
                })

            return QAResponse(
                answer=answer_content[:1000] if len(answer_content) > 1000 else answer_content,
                confidence=0.8,  # Default confidence
                sources=sources,
                metadata={
                    "question": request.question,
                    "max_results": request.max_results,
                    "context": request.context,
                },
            )

        # Fallback: Use graph service if available
        elif _graph_service:
            # Simple graph-based answer (would be enhanced with actual QA logic)
            graph_data = await _graph_service.get_graphistry_data(query=request.question)
            
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])

            answer = f"Found {len(nodes)} nodes and {len(edges)} relationships related to your question."

            sources = [
                {
                    "type": "graph",
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                }
            ]

            return QAResponse(
                answer=answer,
                confidence=0.6,
                sources=sources,
                metadata={
                    "question": request.question,
                    "nodes_found": len(nodes),
                    "edges_found": len(edges),
                },
            )

        else:
            raise HTTPException(status_code=503, detail="No service available for QA")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to answer question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


@router.get("/search")
async def search_knowledge(
    query: str = Query(..., description="Search query", min_length=1),
    max_results: int = Query(10, description="Maximum number of results", ge=1, le=50),
) -> dict:
    """Search the knowledge graph.

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        Search results
    """
    try:
        if not _graph_service:
            raise HTTPException(
                status_code=503,
                detail="Graph service not available for search.",
            )

        logger.info(f"Searching knowledge graph: {query[:50]}...")

        graph_data = await _graph_service.get_graphistry_data(query=query)

        nodes = graph_data.get("nodes", [])[:max_results]
        edges = graph_data.get("edges", [])[:max_results]

        return {
            "query": query,
            "results": {
                "nodes": nodes,
                "edges": edges,
            },
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search knowledge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search knowledge: {str(e)}")

