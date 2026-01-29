"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    """Task execution mode."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    FORK_JOIN = "fork_join"


class TaskRequest(BaseModel):
    """Task creation request."""

    query: str = Field(..., description="Task query or description", min_length=1)
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.FORK_JOIN,
        description="Execution mode for task processing",
    )
    priority: int = Field(default=0, description="Task priority (higher = more important)", ge=0, le=10)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional task metadata")


class TaskResponse(BaseModel):
    """Task response model."""

    task_id: str = Field(..., description="Unique task identifier")
    query: str = Field(..., description="Task query")
    status: TaskStatus = Field(..., description="Current task status")
    execution_mode: ExecutionMode = Field(..., description="Execution mode used")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task execution result")
    error: Optional[str] = Field(default=None, description="Error message if task failed")
    execution_time: float = Field(default=0.0, description="Execution time in seconds", ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class WorkforceInfo(BaseModel):
    """Workforce information response."""

    description: str = Field(..., description="Workforce description")
    agent_count: int = Field(..., description="Number of agents in workforce", ge=0)
    agents: List[str] = Field(default_factory=list, description="List of agent names")
    share_memory: bool = Field(default=True, description="Whether memory is shared")
    mcp_enabled: bool = Field(default=False, description="Whether MCP is enabled")


class AgentInfo(BaseModel):
    """Agent information response."""

    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(default=None, description="Agent description")
    tools_count: int = Field(default=0, description="Number of tools available", ge=0)
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    status: str = Field(default="active", description="Agent status")


class GraphNodeResponse(BaseModel):
    """Graph node response."""

    node_id: str = Field(..., description="Node identifier")
    label: str = Field(..., description="Node label")
    node_type: str = Field(..., description="Node type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Node metadata")
    confidence: float = Field(default=0.5, description="Confidence score", ge=0.0, le=1.0)
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")


class GraphEdgeResponse(BaseModel):
    """Graph edge/relationship response."""

    edge_id: str = Field(..., description="Edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Relationship type")
    strength: float = Field(default=0.5, description="Relationship strength", ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    confidence: float = Field(default=0.5, description="Confidence score", ge=0.0, le=1.0)
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")


class GraphDataResponse(BaseModel):
    """Graph data response."""

    nodes: List[GraphNodeResponse] = Field(default_factory=list, description="List of nodes")
    edges: List[GraphEdgeResponse] = Field(default_factory=list, description="List of edges")
    node_count: int = Field(default=0, description="Total node count", ge=0)
    edge_count: int = Field(default=0, description="Total edge count", ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class GraphFilterRequest(BaseModel):
    """Graph filter request."""

    node_types: Optional[List[str]] = Field(default=None, description="Filter by node types")
    min_confidence: float = Field(default=0.0, description="Minimum confidence", ge=0.0, le=1.0)
    max_depth: Optional[int] = Field(default=None, description="Maximum depth for traversal", ge=1, le=10)
    source_id: Optional[str] = Field(default=None, description="Start from specific node")
    relationship_types: Optional[List[str]] = Field(default=None, description="Filter by relationship types")


class QARequest(BaseModel):
    """Question answering request."""

    question: str = Field(..., description="Question to answer", min_length=1)
    context: Optional[str] = Field(default=None, description="Additional context")
    max_results: int = Field(default=5, description="Maximum number of results", ge=1, le=20)
    include_sources: bool = Field(default=True, description="Include source information")


class QAResponse(BaseModel):
    """Question answering response."""

    answer: str = Field(..., description="Answer to the question")
    confidence: float = Field(default=0.0, description="Confidence score", ge=0.0, le=1.0)
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")
    code: Optional[str] = Field(default=None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

