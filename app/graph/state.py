from typing import TypedDict, Annotated, List, Optional
from pathlib import Path
from operator import add

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


from app.core.sandbox import Sandbox
from app.graph.chains import GraphRunnables

class GraphState(TypedDict):
    """
    State representation for the LangGraph workflow.
    
    This class represents the state that is passed between nodes in the graph.
    It contains all the necessary information for the workflow to execute.
    """
    # Static Variables
    sandbox: Sandbox
    chains: GraphRunnables
    instruction: str 
    output_dir: Path
    max_retries: int
    subtasks: List[str]
    
    # Variables that are getting updated during agent flow
    step: int 
    messages: Annotated[List[BaseMessage], add_messages]
    code_snippet: Optional[str] 
    code_success: Optional[bool]
    is_solved: bool
    errors_or_issues: str 
    previous_sheet_state: str
    current_sheet_state: str
    

