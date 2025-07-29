"""Tool wrapper functions for SheetAgent action executors.

This module provides LangChain tool wrappers for the SheetAgent action executors.
Each function is decorated with @tool.
"""
import logging
from typing import Annotated

from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


from app.graph.state import GraphState
from app.utils.enumeration import EXEC_CODE

logger = logging.getLogger(__name__)

@tool("python_executor", parse_docstring=True)
def python_executor(
    code_snippet: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[GraphState, InjectedState],
) -> dict:
    """Execute Python code in a sandboxed environment.

    This tool allows you to execute Python code to analyze, manipulate, and visualize
    data in the workbook.

    Args:
        code_snippet: The Python code to execute.
    """
    
    logger.info(f"Executing Python_Executor Tool Step {state['step']}")
    
    # Load previous sheetState, Run code and update sheet state
    previous_sheet_state = state["current_sheet_state"]
    response = state["sandbox"].step(code_snippet)    
    current_sheet_state = state["sandbox"].get_sheet_state()
    
    if response.code == EXEC_CODE.SUCCESS:
        content = "Code Executed Successfully"
        error = ''
        code_success = True
    else: 
        content = f"An error occured when excecuting the code: {response.msg}"
        error = response.msg
        code_success = False
        
    update={
            "current_sheet_state": current_sheet_state,
            "previous_sheet_state": previous_sheet_state,
            "code_snippet":code_snippet,
            "code_success": code_success,
            "errors_or_issues": error,
            "messages": [
                ToolMessage(
                    content=content,
                    tool_call_id=tool_call_id,
                    name="python_executor",
                )
            ],
        }
    return Command(update=update)


