"""Palentir OSINT - Advanced Pipeline Workforce with Fork/Join.

Uses CAMEL-AI[all] native classes with pipeline mode for parallel task execution.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.tasks import Task
from camel.societies.workforce import Workforce, WorkforceMode
from camel.storages import Neo4jGraph
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class TaskSummary(BaseModel):
    """Summary of completed task."""

    task_id: str
    content: str
    result: str
    duration_seconds: float
    timestamp: str


class PipelineExecutionContext(BaseModel):
    """Context for pipeline execution."""

    main_task_id: str
    subtasks: List[str] = Field(default_factory=list)
    results: Dict[str, str] = Field(default_factory=dict)
    summaries: List[TaskSummary] = Field(default_factory=list)
    mode: str = "sequential"


class PalentirPipelineWorkforce:
    """Advanced CAMEL-AI Workforce with pipeline fork/join capabilities."""

    def __init__(
        self,
        name: str = "Palentir OSINT Pipeline Workforce",
        neo4j_url: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
    ):
        """Initialize pipeline workforce.

        Args:
            name: Workforce name
            neo4j_url: Neo4j connection URL
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        # Create model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4,
        )

        # Initialize Neo4j graph
        self.graph = Neo4jGraph(
            url=neo4j_url,
            username=neo4j_user,
            password=neo4j_password,
        )

        # Create coordinator agent
        self.coordinator_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="PipelineCoordinator",
                content=(
                    "You are a pipeline coordinator. Orchestrate parallel tasks "
                    "and ensure proper synchronization. Provide summaries of "
                    "completed work before generating new tasks."
                ),
            ),
            model=self.model,
        )

        # Create task planning agent
        self.task_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="TaskPlanner",
                content=(
                    "You are a task planning agent. Analyze task summaries and "
                    "generate appropriate subtasks. Decide whether to use "
                    "sequential, fork, or join execution modes."
                ),
            ),
            model=self.model,
        )

        # Create CAMEL-AI Workforce in PIPELINE mode
        self.workforce = Workforce(
            name=name,
            coordinator_agent=self.coordinator_agent,
            task_agent=self.task_agent,
            mode=WorkforceMode.PIPELINE,
        )

        logger.info(f"Pipeline Workforce initialized: {name}")

    def add_agent(self, name: str, role: str, description: str) -> ChatAgent:
        """Add an agent to the workforce.

        Args:
            name: Agent name
            role: Agent role
            description: Agent description

        Returns:
            Created ChatAgent
        """
        agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name=role,
                content=description,
            ),
            model=self.model,
        )

        self.workforce.add_single_agent_worker(name, agent)
        logger.info(f"Added agent to pipeline: {name}")

        return agent

    async def process_task_sequential(self, task: Task) -> Dict[str, Any]:
        """Process task sequentially.

        Args:
            task: Task to process

        Returns:
            Task result
        """
        logger.info(f"Processing task sequentially: {task.id}")

        try:
            result = await self.workforce.process_task_async(task)
            return {
                "task_id": task.id,
                "status": "completed",
                "mode": "sequential",
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Sequential task failed: {e}")
            return {
                "task_id": task.id,
                "status": "failed",
                "mode": "sequential",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def process_tasks_parallel(
        self,
        tasks: List[Task],
    ) -> List[Dict[str, Any]]:
        """Process multiple tasks in parallel (fork).

        Args:
            tasks: List of tasks to process in parallel

        Returns:
            List of results
        """
        logger.info(f"Processing {len(tasks)} tasks in parallel (fork)")

        # Create coroutines for all tasks
        coroutines = [
            self.workforce.process_task_async(task)
            for task in tasks
        ]

        # Execute in parallel
        try:
            results = await asyncio.gather(*coroutines)
            return [
                {
                    "task_id": task.id,
                    "status": "completed",
                    "mode": "parallel",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                for task, result in zip(tasks, results)
            ]
        except Exception as e:
            logger.error(f"Parallel task execution failed: {e}")
            return [
                {
                    "task_id": task.id,
                    "status": "failed",
                    "mode": "parallel",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                for task in tasks
            ]

    async def process_pipeline(
        self,
        main_task: Task,
        subtasks_generator: callable,
    ) -> Dict[str, Any]:
        """Process task with pipeline fork/join pattern.

        Args:
            main_task: Main task to process
            subtasks_generator: Function that generates subtasks

        Returns:
            Pipeline result
        """
        logger.info(f"Starting pipeline execution: {main_task.id}")

        context = PipelineExecutionContext(main_task_id=main_task.id)

        try:
            # Step 1: Process main task
            logger.info("Step 1: Processing main task")
            main_result = await self.workforce.process_task_async(main_task)

            # Create summary of main task
            main_summary = TaskSummary(
                task_id=main_task.id,
                content=main_task.content,
                result=str(main_result)[:500],
                duration_seconds=0.0,
                timestamp=datetime.utcnow().isoformat(),
            )
            context.summaries.append(main_summary)

            # Step 2: Generate subtasks based on main task result
            logger.info("Step 2: Generating subtasks based on main task summary")
            subtasks = subtasks_generator(main_summary)
            context.subtasks = [t.id for t in subtasks]
            context.mode = "fork"

            # Step 3: Process subtasks in parallel (fork)
            logger.info(f"Step 3: Forking into {len(subtasks)} parallel tasks")
            subtask_results = await self.process_tasks_parallel(subtasks)

            # Store results
            for result in subtask_results:
                context.results[result["task_id"]] = result.get("result", "")

            # Step 4: Join results and synthesize
            logger.info("Step 4: Joining results and synthesizing")
            synthesis_task = Task(
                content=f"Synthesize results from {len(subtasks)} parallel tasks",
                id=f"{main_task.id}_synthesis",
            )

            synthesis_result = await self.workforce.process_task_async(
                synthesis_task
            )

            context.results[synthesis_task.id] = str(synthesis_result)

            return {
                "status": "completed",
                "main_task_id": main_task.id,
                "context": context.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return {
                "status": "failed",
                "main_task_id": main_task.id,
                "error": str(e),
                "context": context.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def build_pipeline_definition(
        self,
        initial_task: str,
        fork_tasks: List[str],
        join_task: str,
    ) -> None:
        """Build a pipeline definition using CAMEL-AI pipeline methods.

        Args:
            initial_task: Initial task description
            fork_tasks: List of tasks to fork
            join_task: Join task description
        """
        logger.info("Building pipeline definition")

        try:
            # Use CAMEL-AI pipeline builder
            self.workforce.pipeline_add(initial_task).pipeline_fork(
                fork_tasks
            ).pipeline_join(join_task).pipeline_build()

            logger.info("Pipeline definition built successfully")

        except Exception as e:
            logger.error(f"Error building pipeline: {e}")

    def add_graph_result(
        self,
        task_id: str,
        result_summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add task result to knowledge graph.

        Args:
            task_id: Task ID
            result_summary: Result summary
            metadata: Additional metadata
        """
        try:
            subject = f"TASK:{task_id}"
            obj = f"RESULT:{result_summary[:100]}"
            relation = "HAS_RESULT"

            self.graph.add_triplet(subj=subject, obj=obj, rel=relation)
            logger.info(f"Added result to graph: {task_id}")

        except Exception as e:
            logger.error(f"Error adding result to graph: {e}")

    async def close(self) -> None:
        """Close workforce resources."""
        logger.info("Closing Pipeline Workforce")
        try:
            self.graph.close()
        except Exception as e:
            logger.error(f"Error closing graph: {e}")
