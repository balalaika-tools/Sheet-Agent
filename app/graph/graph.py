"""
LangGraph implementation for SheetAgent.

This module defines the GraphState model and node functions for the LangGraph workflow.
It includes LangSmith integration for tracing and monitoring.
"""

from typing import Dict, List, Any
from pathlib import Path
import logging
from fastapi import HTTPException

from langgraph.graph import StateGraph, START, END
from langsmith import traceable
from langgraph.errors import NodeInterrupt

from langgraph.prebuilt import ToolNode
from app.core.sandbox import Sandbox
from app.graph.tools import python_executor
from app.graph.nodes import (
    decomposer_node,
    actor_node,
    reflector_node,
    routing_after_actor,
    routing_after_reflector,
)
from app.graph.state import GraphState
from app.graph.chains import GraphRunnables

# Configure logger
logger = logging.getLogger(__name__)


class SheetAgentGraph:
    """
    A wrapper class for the StateGraph that provides a simplified interface for execution.

    This class encapsulates the graph construction and execution, providing a clean
    interface for the analysis service to use. It integrates with LangSmith for
    tracing and monitoring of the agent's execution.
    """

    def __init__(
        self, output_dir: Path, sandbox: Sandbox, instruction: str, max_retries: int = 5
    ):
        self.output_dir = output_dir
        self.sandbox = sandbox
        self.max_retries = max_retries
        self.instruction = instruction

        # Initialize the chains
        logger.info("Initializing GraphRunnables")
        self.chains = GraphRunnables()

        # Build Graph
        self.graph = self.build_graph()

    def build_graph(self) -> StateGraph:
        """
        Builds and returns the StateGraph for the agent workflow.

        This function constructs the StateGraph with the appropriate nodes and edges

        Returns:
            The compiled StateGraph.
        """
        graph = StateGraph(GraphState)

        graph.add_node("decomposer", decomposer_node)
        graph.add_node("actor", actor_node)
        graph.add_node("tool", ToolNode([python_executor]))
        graph.add_node("reflector", reflector_node)

        graph.add_edge(START, "decomposer")
        graph.add_edge("decomposer", "actor")
        graph.add_edge("actor", "tool")
        graph.add_conditional_edges(
            "tool",
            routing_after_actor,
            {
                "actor": "actor",
                "reflector": "reflector",
                END: END,
            },
        )
        graph.add_conditional_edges(
            "reflector",
            routing_after_reflector,
            {
                "actor": "actor",
                END: END,
            },
        )
        graph.set_finish_point("reflector")

        graph = graph.compile()
        return graph

    def create_initial_state(self) -> GraphState:
        """
        Creates the initial state for the graph execution.

        Returns:
            An instance of GraphState with the initial values set.
        """
        return GraphState(
            sandbox=self.sandbox,
            chains=self.chains,
            instruction=self.instruction,
            output_dir=self.output_dir,
            max_retries=self.max_retries,
            subtasks=[],
            step=0,
            messages=[],
            code_snippet=None,
            code_success=None,
            is_solved=False,
            errors_or_issues="",
            previous_sheet_state=self.sandbox.get_sheet_state(),
            current_sheet_state=self.sandbox.get_sheet_state(),
        )

    @traceable(name="SheetAgent", run_type="chain")
    def run(self) -> GraphState:

        logger.info("Starting SheetAgentGraph execution")

        # Create the initial state
        logger.info("Creating initial state")
        initial_state = self.create_initial_state()

        # Run the graph
        logger.info("Invoking graph")
        final_state = self.graph.invoke(initial_state)

        # Output HTTP exeption when the graph execution exceeds the maximum retries
        if final_state["is_solved"] is False:
            logger.error("Maximum retries exceeded and the problem could not be solved.")
            raise HTTPException(status_code=400, detail="Failed to solve the problem after maximum retries.")

        logger.info(f"Graph execution completed after {final_state['step']} steps")

        # Save the final state of the workbook
        logger.info(f"Saving final workbook state to {self.output_dir}")
        self.sandbox.save(self.output_dir)

        return final_state
