"""Palentir OSINT - Graph API Routes.

Provides REST API endpoints for graph visualization and querying.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from kitten_palentir.api.models.schemas import (
    GraphNodeResponse,
    GraphEdgeResponse,
    GraphDataResponse,
    GraphFilterRequest,
    ErrorResponse,
)
from kitten_palentir.services.graph_visualization import GraphVisualizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

# Global graph service instance (would be injected via dependency injection in production)
_graph_service: Optional[GraphVisualizationService] = None


def set_graph_service(service: GraphVisualizationService):
    """Set the graph visualization service instance.

    Args:
        service: Graph Visualization Service instance
    """
    global _graph_service
    _graph_service = service
    logger.info("Graph service instance set for graph router")


def get_graph_service() -> GraphVisualizationService:
    """Get the graph visualization service instance.

    Returns:
        Graph Visualization Service instance

    Raises:
        HTTPException: If service is not initialized
    """
    if _graph_service is None:
        raise HTTPException(
            status_code=503,
            detail="Graph service not initialized. Please wait for service to be ready.",
        )
    return _graph_service


@router.get("/data", response_model=GraphDataResponse)
async def get_graph_data(
    query: Optional[str] = Query(None, description="Optional query to filter graph"),
    node_types: Optional[str] = Query(None, description="Comma-separated list of node types to filter"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold", ge=0.0, le=1.0),
) -> GraphDataResponse:
    """Get graph data for visualization.

    Args:
        query: Optional query to filter graph
        node_types: Optional comma-separated node types filter
        min_confidence: Minimum confidence threshold

    Returns:
        Graph data response
    """
    try:
        service = get_graph_service()

        # Get graphistry data
        graph_data = await service.get_graphistry_data(query=query)

        nodes_data = graph_data.get("nodes", [])
        edges_data = graph_data.get("edges", [])

        # Apply filters
        if node_types:
            node_type_list = [nt.strip() for nt in node_types.split(",")]
            nodes_data = [n for n in nodes_data if n.get("type") in node_type_list]

        if min_confidence > 0.0:
            nodes_data = [n for n in nodes_data if n.get("confidence", 0.0) >= min_confidence]
            edges_data = [e for e in edges_data if e.get("confidence", 0.0) >= min_confidence]

        # Convert to response models
        nodes = [
            GraphNodeResponse(
                node_id=node.get("id", node.get("node_id", "")),
                label=node.get("label", node.get("name", "")),
                node_type=node.get("type", "unknown"),
                properties=node.get("properties", {}),
                metadata=node.get("metadata"),
                confidence=node.get("confidence", 0.5),
                created_at=node.get("created_at"),
            )
            for node in nodes_data
        ]

        edges = [
            GraphEdgeResponse(
                edge_id=edge.get("id", edge.get("edge_id", "")),
                source_id=edge.get("source", edge.get("source_id", "")),
                target_id=edge.get("target", edge.get("target_id", "")),
                relationship_type=edge.get("type", edge.get("relationship_type", "related")),
                strength=edge.get("strength", 0.5),
                properties=edge.get("properties", {}),
                confidence=edge.get("confidence", 0.5),
                created_at=edge.get("created_at"),
            )
            for edge in edges_data
        ]

        return GraphDataResponse(
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get graph data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {str(e)}")


@router.get("/nodes", response_model=List[GraphNodeResponse])
async def get_nodes(
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    min_confidence: float = Query(0.0, description="Minimum confidence", ge=0.0, le=1.0),
    limit: int = Query(100, description="Maximum number of nodes", ge=1, le=1000),
) -> List[GraphNodeResponse]:
    """Get graph nodes.

    Args:
        node_type: Optional node type filter
        min_confidence: Minimum confidence threshold
        limit: Maximum number of nodes to return

    Returns:
        List of graph nodes
    """
    try:
        service = get_graph_service()

        filters = {}
        if node_type:
            filters["node_type"] = node_type
        if min_confidence > 0.0:
            filters["min_confidence"] = min_confidence

        nodes = await service.get_nodes(filters=filters if filters else None)

        # Limit results
        nodes = nodes[:limit]

        # Convert to response models
        return [
            GraphNodeResponse(
                node_id=node.node_id,
                label=node.label,
                node_type=node.node_type,
                properties=node.properties,
                metadata=node.metadata,
                confidence=getattr(node, "confidence", 0.5),
                created_at=node.to_dict().get("created_at"),
            )
            for node in nodes
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get nodes: {str(e)}")


@router.get("/nodes/{node_id}", response_model=GraphNodeResponse)
async def get_node_details(node_id: str = Path(..., description="Node ID")) -> GraphNodeResponse:
    """Get detailed information about a specific node.

    Args:
        node_id: Node identifier

    Returns:
        Node details
    """
    try:
        service = get_graph_service()

        node_details = await service.get_node_details(node_id)

        if not node_details:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        return GraphNodeResponse(
            node_id=node_details.get("id", node_id),
            label=node_details.get("label", ""),
            node_type=node_details.get("type", "unknown"),
            properties=node_details.get("properties", {}),
            metadata=node_details.get("metadata"),
            confidence=node_details.get("confidence", 0.5),
            created_at=node_details.get("created_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get node details: {str(e)}")


@router.get("/edges", response_model=List[GraphEdgeResponse])
async def get_edges(
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    source_id: Optional[str] = Query(None, description="Filter by source node ID"),
    target_id: Optional[str] = Query(None, description="Filter by target node ID"),
    limit: int = Query(100, description="Maximum number of edges", ge=1, le=1000),
) -> List[GraphEdgeResponse]:
    """Get graph edges/relationships.

    Args:
        relationship_type: Optional relationship type filter
        source_id: Optional source node ID filter
        target_id: Optional target node ID filter
        limit: Maximum number of edges to return

    Returns:
        List of graph edges
    """
    try:
        service = get_graph_service()

        filters = {}
        if relationship_type:
            filters["relationship_type"] = relationship_type
        if source_id:
            filters["source_id"] = source_id
        if target_id:
            filters["target_id"] = target_id

        relationships = await service.get_relationships(filters=filters if filters else None)

        # Limit results
        relationships = relationships[:limit]

        # Convert to response models
        return [
            GraphEdgeResponse(
                edge_id=rel.rel_id,
                source_id=rel.source_id,
                target_id=rel.target_id,
                relationship_type=rel.rel_type,
                strength=rel.strength,
                properties=rel.properties,
                confidence=getattr(rel, "confidence", 0.5),
                created_at=rel.created_at,
            )
            for rel in relationships
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get edges: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get edges: {str(e)}")


@router.get("/path/{source_id}/{target_id}")
async def get_path(
    source_id: str = Path(..., description="Source node ID"),
    target_id: str = Path(..., description="Target node ID"),
    max_depth: int = Query(5, description="Maximum path depth", ge=1, le=10),
) -> dict:
    """Get path between two nodes.

    Args:
        source_id: Source node ID
        target_id: Target node ID
        max_depth: Maximum path depth

    Returns:
        Path information
    """
    try:
        service = get_graph_service()

        path_data = await service.get_relationship_path(source_id, target_id)

        if not path_data:
            raise HTTPException(
                status_code=404,
                detail=f"Path not found between {source_id} and {target_id}",
            )

        return path_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get path: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get path: {str(e)}")


@router.post("/filter", response_model=GraphDataResponse)
async def filter_graph(filter_request: GraphFilterRequest) -> GraphDataResponse:
    """Filter graph data based on criteria.

    Args:
        filter_request: Filter criteria

    Returns:
        Filtered graph data
    """
    try:
        service = get_graph_service()

        filter_dict = {
            "node_types": filter_request.node_types,
            "min_confidence": filter_request.min_confidence,
            "max_depth": filter_request.max_depth,
            "source_id": filter_request.source_id,
            "relationship_types": filter_request.relationship_types,
        }

        filtered_data = await service.filter_graph(**{k: v for k, v in filter_dict.items() if v is not None})

        # Convert to response models
        nodes = [
            GraphNodeResponse(
                node_id=node.get("id", ""),
                label=node.get("label", ""),
                node_type=node.get("type", "unknown"),
                properties=node.get("properties", {}),
                metadata=node.get("metadata"),
                confidence=node.get("confidence", 0.5),
                created_at=node.get("created_at"),
            )
            for node in filtered_data.get("nodes", [])
        ]

        edges = [
            GraphEdgeResponse(
                edge_id=edge.get("id", ""),
                source_id=edge.get("source", ""),
                target_id=edge.get("target", ""),
                relationship_type=edge.get("type", "related"),
                strength=edge.get("strength", 0.5),
                properties=edge.get("properties", {}),
                confidence=edge.get("confidence", 0.5),
                created_at=edge.get("created_at"),
            )
            for edge in filtered_data.get("edges", [])
        ]

        return GraphDataResponse(
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to filter graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to filter graph: {str(e)}")


@router.get("/statistics")
async def get_graph_statistics() -> dict:
    """Get graph statistics.

    Returns:
        Graph statistics
    """
    try:
        service = get_graph_service()

        graph_data = await service.get_graphistry_data()

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Calculate statistics
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        relationship_types = {}
        for edge in edges:
            rel_type = edge.get("type", "unknown")
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

        avg_node_confidence = (
            sum(node.get("confidence", 0.5) for node in nodes) / len(nodes) if nodes else 0.0
        )
        avg_edge_strength = (
            sum(edge.get("strength", 0.5) for edge in edges) / len(edges) if edges else 0.0
        )

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": node_types,
            "relationship_types": relationship_types,
            "avg_node_confidence": round(avg_node_confidence, 3),
            "avg_edge_strength": round(avg_edge_strength, 3),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get graph statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get graph statistics: {str(e)}")

