"""Unit tests for Palentir OSINT pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.workforce.pipeline_mode import (
    PipelineMode,
    PipelineStage,
    PipelineDefinition,
    PipelineExecutor,
)
from src.workforce.task_system import OSINTTaskType


class TestPipelineMode:
    """Test PipelineMode enum."""

    @pytest.mark.unit
    def test_pipeline_mode_values(self):
        """Test PipelineMode enum values."""
        assert PipelineMode.SEQUENTIAL.value == "sequential"
        assert PipelineMode.PARALLEL.value == "parallel"
        assert PipelineMode.FORK_JOIN.value == "fork_join"
        assert PipelineMode.PIPELINE.value == "pipeline"


class TestPipelineStage:
    """Test PipelineStage class."""

    @pytest.mark.unit
    def test_stage_creation(self):
        """Test creating a PipelineStage."""
        stage = PipelineStage(
            stage_id="stage_1",
            name="Network Analysis",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["NetworkAnalyzerAgent", "DomainAnalyzerAgent"],
        )
        assert stage.stage_id == "stage_1"
        assert stage.name == "Network Analysis"
        assert len(stage.agents) == 2

    @pytest.mark.unit
    def test_stage_defaults(self):
        """Test PipelineStage default values."""
        stage = PipelineStage(
            stage_id="stage_1",
            name="Test Stage",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1"],
        )
        assert stage.mode == PipelineMode.PARALLEL
        assert stage.depends_on == []
        assert stage.status == "pending"
        assert stage.results == []

    @pytest.mark.unit
    def test_stage_with_dependencies(self):
        """Test PipelineStage with dependencies."""
        stage = PipelineStage(
            stage_id="stage_2",
            name="Analysis Stage",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1"],
            depends_on=["stage_1"],
        )
        assert stage.depends_on == ["stage_1"]

    @pytest.mark.unit
    def test_stage_to_dict(self):
        """Test converting stage to dictionary."""
        stage = PipelineStage(
            stage_id="stage_1",
            name="Test Stage",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1"],
        )
        stage_dict = stage.to_dict()
        assert stage_dict["stage_id"] == "stage_1"
        assert stage_dict["name"] == "Test Stage"
        assert "created_at" in stage_dict


class TestPipelineDefinition:
    """Test PipelineDefinition class."""

    @pytest.mark.unit
    def test_pipeline_creation(self):
        """Test creating a PipelineDefinition."""
        pipeline = PipelineDefinition(
            pipeline_id="pipeline_1",
            name="Company Analysis",
            description="Full company OSINT analysis",
        )
        assert pipeline.pipeline_id == "pipeline_1"
        assert pipeline.name == "Company Analysis"
        assert pipeline.stages == []

    @pytest.mark.unit
    def test_add_stage(self):
        """Test adding stages to pipeline."""
        pipeline = PipelineDefinition(
            pipeline_id="pipeline_1",
            name="Test Pipeline",
        )

        stage = PipelineStage(
            stage_id="stage_1",
            name="Stage 1",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1"],
        )
        pipeline.add_stage(stage)

        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].stage_id == "stage_1"

    @pytest.mark.unit
    def test_get_stage(self):
        """Test getting stage from pipeline."""
        pipeline = PipelineDefinition(
            pipeline_id="pipeline_1",
            name="Test Pipeline",
        )

        stage = PipelineStage(
            stage_id="stage_1",
            name="Stage 1",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1"],
        )
        pipeline.add_stage(stage)

        retrieved = pipeline.get_stage("stage_1")
        assert retrieved is not None
        assert retrieved.stage_id == "stage_1"

    @pytest.mark.unit
    def test_get_nonexistent_stage(self):
        """Test getting nonexistent stage."""
        pipeline = PipelineDefinition(
            pipeline_id="pipeline_1",
            name="Test Pipeline",
        )

        stage = pipeline.get_stage("nonexistent")
        assert stage is None

    @pytest.mark.unit
    def test_pipeline_to_dict(self):
        """Test converting pipeline to dictionary."""
        pipeline = PipelineDefinition(
            pipeline_id="pipeline_1",
            name="Test Pipeline",
        )

        pipeline_dict = pipeline.to_dict()
        assert pipeline_dict["pipeline_id"] == "pipeline_1"
        assert pipeline_dict["name"] == "Test Pipeline"
        assert "stages" in pipeline_dict


class TestPipelineExecutor:
    """Test PipelineExecutor class."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """Test executor initialization."""
        executor = PipelineExecutor()
        assert executor.pipelines == {}
        assert executor.stage_results == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_pipeline_empty(self):
        """Test executing empty pipeline."""
        executor = PipelineExecutor()
        pipeline = PipelineDefinition(
            pipeline_id="pipeline_1",
            name="Empty Pipeline",
        )

        context = {}
        agent_executor = AsyncMock(return_value={"status": "completed"})

        result = await executor.execute_pipeline(
            pipeline, context, agent_executor
        )

        assert result["pipeline_id"] == "pipeline_1"
        assert result["status"] == "completed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_sequential_stage(self):
        """Test executing sequential stage."""
        executor = PipelineExecutor()

        stage = PipelineStage(
            stage_id="stage_1",
            name="Sequential Stage",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1", "Agent2"],
            mode=PipelineMode.SEQUENTIAL,
        )

        context = {}
        agent_executor = AsyncMock(return_value={"status": "completed"})

        results = await executor._execute_sequential_stage(
            stage, context, agent_executor
        )

        assert len(results) == 2
        assert agent_executor.call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_parallel_stage(self):
        """Test executing parallel stage."""
        executor = PipelineExecutor()

        stage = PipelineStage(
            stage_id="stage_1",
            name="Parallel Stage",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1", "Agent2"],
            mode=PipelineMode.PARALLEL,
        )

        context = {}
        agent_executor = AsyncMock(return_value={"status": "completed"})

        results = await executor._execute_parallel_stage(
            stage, context, agent_executor
        )

        assert len(results) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_fork_join_stage(self):
        """Test executing fork/join stage."""
        executor = PipelineExecutor()

        stage = PipelineStage(
            stage_id="stage_1",
            name="Fork/Join Stage",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["Agent1", "Agent2"],
            mode=PipelineMode.FORK_JOIN,
        )

        context = {}
        agent_executor = AsyncMock(return_value={"status": "completed"})

        results = await executor._execute_fork_join_stage(
            stage, context, agent_executor
        )

        assert len(results) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_tasks_from_query_company(self):
        """Test generating tasks from company query."""
        executor = PipelineExecutor()

        tasks = await executor.generate_tasks_from_query(
            "Analyze Apple Inc.",
            {},
        )

        assert len(tasks) > 0
        assert any("company" in t.title.lower() for t in tasks)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_tasks_from_query_person(self):
        """Test generating tasks from person query."""
        executor = PipelineExecutor()

        tasks = await executor.generate_tasks_from_query(
            "Find information about Steve Jobs",
            {},
        )

        assert len(tasks) > 0
        assert any("person" in t.title.lower() for t in tasks)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_tasks_from_query_domain(self):
        """Test generating tasks from domain query."""
        executor = PipelineExecutor()

        tasks = await executor.generate_tasks_from_query(
            "Analyze apple.com domain",
            {},
        )

        assert len(tasks) > 0
        assert any("domain" in t.title.lower() for t in tasks)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_tasks_from_query_technology(self):
        """Test generating tasks from technology query."""
        executor = PipelineExecutor()

        tasks = await executor.generate_tasks_from_query(
            "Detect technologies used by company",
            {},
        )

        assert len(tasks) > 0
        assert any("technology" in t.title.lower() for t in tasks)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_find_missing_information(self):
        """Test finding missing information."""
        executor = PipelineExecutor()

        graph_context = {
            "nodes": [
                {"id": "node_1", "type": "Company"},
                {"id": "node_2", "type": "Person"},
            ]
        }

        missing = await executor.find_missing_information(graph_context)
        assert isinstance(missing, list)


@pytest.mark.pipeline
class TestPipelineIntegration:
    """Integration tests for pipeline."""

    @pytest.mark.asyncio
    async def test_complete_pipeline_execution(self):
        """Test complete pipeline execution."""
        executor = PipelineExecutor()

        # Create pipeline
        pipeline = PipelineDefinition(
            pipeline_id="pipeline_1",
            name="Company Analysis",
        )

        # Add stages
        stage1 = PipelineStage(
            stage_id="stage_1",
            name="Network Analysis",
            task_type=OSINTTaskType.NETWORK_ANALYSIS,
            agents=["NetworkAnalyzerAgent"],
        )
        pipeline.add_stage(stage1)

        stage2 = PipelineStage(
            stage_id="stage_2",
            name="Social Intelligence",
            task_type=OSINTTaskType.SOCIAL_INTELLIGENCE,
            agents=["SocialFinderAgent"],
            depends_on=["stage_1"],
        )
        pipeline.add_stage(stage2)

        # Execute
        context = {}
        agent_executor = AsyncMock(return_value={"status": "completed"})

        result = await executor.execute_pipeline(
            pipeline, context, agent_executor
        )

        assert result["status"] == "completed"
        assert "stage_1" in result["stages"]
        assert "stage_2" in result["stages"]

    @pytest.mark.asyncio
    async def test_pipeline_with_task_generation(self):
        """Test pipeline with task generation."""
        executor = PipelineExecutor()

        # Generate tasks from query
        tasks = await executor.generate_tasks_from_query(
            "Analyze Apple Inc. and its employees",
            {},
        )

        assert len(tasks) > 0

        # Find missing information
        missing = await executor.find_missing_information(
            {"nodes": []}
        )

        assert isinstance(missing, list)
