import logging
from typing_extensions import Literal
import json

from langgraph.errors import NodeInterrupt
from langsmith import traceable
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage

from app.graph.state import GraphState


# Configure logger
logger = logging.getLogger(__name__)


@traceable(name="Decomposer Node", run_type="chain")
def decomposer_node(state: GraphState) -> GraphState:
    logger.info(f"Executing Decomposer Node")

    try:
        response = state["chains"].decomposer_chain.invoke(
            {
                "instruction": state["instruction"],
                "sheet_state": state["current_sheet_state"],
            }
        )
    except Exception as e:
        logger.error("Decomposer chain failed", exc_info=True)
        raise NodeInterrupt(str(e))

    return {
        "subtasks": response.subtasks,
        "messages": [
            AIMessage(content=f"Decomposed into subtasks: {response.subtasks}")
        ],
    }


@traceable(name="Actor Node", run_type="chain")
def actor_node(state: GraphState) -> GraphState:
    logger.info(f"Executing Actor Node Step {state['step']}")

    try:
        if state.get("code_success", None) is not False:
            response = state["chains"].actor_chain.invoke(
                {
                    "subtasks": state["subtasks"],
                    "failed_code": "",
                    "errors_or_issues": "",
                }
            )
        else:
            failed_code_string = (
                f"\nPrevious Code-Snippet:\n{state.get('code_snippet','')}\n"
            )
            errors_or_issues_string = (
                f"Errors or Issues:\n{state.get('errors_or_issues','')}"
            )
            response = state["chains"].actor_chain.invoke(
                {
                    "subtasks": state["subtasks"],
                    "failed_code": failed_code_string,
                    "errors_or_issues": errors_or_issues_string,
                }
            )

    except Exception as e:
        logger.error("Actor chain failed", exc_info=True)
        raise NodeInterrupt(str(e))

    return {
        "messages": [response],
        "step": state["step"] + 1,
    }


@traceable(name="Reflector Node", run_type="chain")
def reflector_node(state: GraphState) -> GraphState:
    logger.info(f"Executing Reflector Node Step{state['step']}")
    try:
        response = state["chains"].reflector_chain.invoke(
            {
                "code_snippet": state["code_snippet"],
                "previous_sheet_state": state["previous_sheet_state"],
                "current_sheet_state": state["current_sheet_state"],
                "subtasks": state["subtasks"],
            }
        )

        content = "Reflector full verdict JSON:\n" + json.dumps(
            response.model_dump(), indent=2
        )
        msg = AIMessage(content=content)
        
    except Exception as e:
        logger.error("Reflector chain failed", exc_info=True)
        raise NodeInterrupt(str(e))

    return {
        "messages": [msg],
        "is_solved": response.is_solved,
        "errors_or_issues": response.issues,
        "code_success": response.is_solved,
    }


def routing_after_actor(state: GraphState) -> Literal["reflector", "actor", END]:
    if state["code_success"] is False and state["step"] < state["max_retries"]:
        return "actor"
    elif state["code_success"] is True and state["step"] < state["max_retries"]:
        return "reflector"
    elif state["code_success"] is True and state["step"] == state["max_retries"]:
        return "reflector"
    else:
        return END


def routing_after_reflector(state: GraphState) -> Literal["actor", END]:
    if state["is_solved"] is False and state["step"] < state["max_retries"]:
        return "actor"
    else:
        return END
