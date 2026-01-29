"""Pipeline mode definitions for OSINT workflows."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class PipelineMode(str, Enum):
    """Pipeline execution mode."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    FORK_JOIN = "fork_join"
    PIPELINE = "pipeline"


class PipelineStage(BaseModel):
    """Pipeline stage definition."""

    stage_id: str
    name: str
    task_type: Any  # OSINTTaskType
    agents: List[str]
    description: str = ""
    mode: PipelineMode = PipelineMode.PARALLEL
    depends_on: List[str] = []
    status: str = "pending"
    results: List[Dict[str, Any]] = []
    created_at: Optional[str] = None
    config: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        from datetime import datetime
        return {
            "stage_id": self.stage_id,
            "name": self.name,
            "task_type": self.task_type.value if hasattr(self.task_type, 'value') else str(self.task_type),
            "agents": self.agents,
            "description": self.description,
            "mode": self.mode.value,
            "depends_on": self.depends_on,
            "status": self.status,
            "results": self.results,
            "created_at": self.created_at or datetime.utcnow().isoformat(),
            "config": self.config,
        }


class PipelineDefinition(BaseModel):
    """Pipeline definition."""

    pipeline_id: str
    name: str
    description: str = ""
    mode: PipelineMode = PipelineMode.SEQUENTIAL
    stages: List[PipelineStage] = []
    config: Dict[str, Any] = {}
    
    def add_stage(self, stage: PipelineStage) -> None:
        """Add a stage to the pipeline."""
        self.stages.append(stage)
    
    def get_stage(self, stage_id: str) -> Optional[PipelineStage]:
        """Get a stage by ID."""
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "description": self.description,
            "mode": self.mode.value,
            "stages": [stage.to_dict() for stage in self.stages],
            "config": self.config,
        }


class PipelineExecutor:
    """Pipeline executor."""

    def __init__(self, pipeline: Optional[PipelineDefinition] = None):
        """Initialize the executor."""
        self.pipeline = pipeline or PipelineDefinition(
            pipeline_id="default",
            name="Default Pipeline",
            description="Default pipeline",
        )
        self.pipelines: Dict[str, PipelineDefinition] = {}
        self.stage_results: Dict[str, List[Dict[str, Any]]] = {}

    async def execute(self) -> Dict[str, Any]:
        """Execute the pipeline."""
        return {}
    
    async def execute_pipeline(
        self,
        pipeline: PipelineDefinition,
        context: Dict[str, Any],
        agent_executor: Any,
    ) -> Dict[str, Any]:
        """Execute a pipeline."""
        results = []
        for stage in pipeline.stages:
            if stage.mode == PipelineMode.SEQUENTIAL:
                stage_results = await self._execute_sequential_stage(stage, context, agent_executor)
            elif stage.mode == PipelineMode.PARALLEL:
                stage_results = await self._execute_parallel_stage(stage, context, agent_executor)
            elif stage.mode == PipelineMode.FORK_JOIN:
                stage_results = await self._execute_fork_join_stage(stage, context, agent_executor)
            else:
                stage_results = []
            results.extend(stage_results)
        
        return {
            "pipeline_id": pipeline.pipeline_id,
            "status": "completed",
            "results": results,
            "stages": {stage.stage_id: stage.status for stage in pipeline.stages},
        }
    
    async def _execute_sequential_stage(
        self,
        stage: PipelineStage,
        context: Dict[str, Any],
        agent_executor: Any,
    ) -> List[Dict[str, Any]]:
        """Execute a sequential stage."""
        results = []
        for agent in stage.agents:
            result = await agent_executor(agent, context)
            results.append(result)
        return results
    
    async def _execute_parallel_stage(
        self,
        stage: PipelineStage,
        context: Dict[str, Any],
        agent_executor: Any,
    ) -> List[Dict[str, Any]]:
        """Execute a parallel stage."""
        import asyncio
        tasks = [agent_executor(agent, context) for agent in stage.agents]
        results = await asyncio.gather(*tasks)
        return list(results)
    
    async def _execute_fork_join_stage(
        self,
        stage: PipelineStage,
        context: Dict[str, Any],
        agent_executor: Any,
    ) -> List[Dict[str, Any]]:
        """Execute a fork/join stage."""
        import asyncio
        tasks = [agent_executor(agent, context) for agent in stage.agents]
        results = await asyncio.gather(*tasks)
        return list(results)
    
    async def generate_tasks_from_query(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> List[Any]:
        """Generate tasks from a query."""
        # Mock implementation - return tasks based on query keywords
        tasks = []
        query_lower = query.lower()
        
        if "company" in query_lower or "inc" in query_lower or "corp" in query_lower:
            from kitten_palentir.workforce.task_system import OSINTTaskType
            tasks.append(type('Task', (), {
                'title': 'Company Reconnaissance',
                'task_type': OSINTTaskType.COMPANY_RECON,
            })())
        
        if "person" in query_lower or "find" in query_lower:
            from kitten_palentir.workforce.task_system import OSINTTaskType
            tasks.append(type('Task', (), {
                'title': 'Person Reconnaissance',
                'task_type': OSINTTaskType.PERSON_RECON,
            })())
        
        if "domain" in query_lower or ".com" in query_lower:
            from kitten_palentir.workforce.task_system import OSINTTaskType
            tasks.append(type('Task', (), {
                'title': 'Domain Analysis',
                'task_type': OSINTTaskType.DOMAIN_ANALYSIS,
            })())
        
        if "technology" in query_lower or "tech" in query_lower:
            from kitten_palentir.workforce.task_system import OSINTTaskType
            tasks.append(type('Task', (), {
                'title': 'Technology Analysis',
                'task_type': OSINTTaskType.TECHNOLOGY_ANALYSIS,
            })())
        
        return tasks
    
    async def find_missing_information(self, graph_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find missing information in graph context."""
        missing = []
        # Simple implementation
        if "nodes" not in graph_context:
            missing.append({"type": "nodes", "description": "No nodes found"})
        return missing

