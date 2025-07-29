from pydantic import BaseModel, Field
from typing import Literal, List, Optional

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.core.config import get_settings, SheetAgentSettings
from app.core.prompt_manager import PromptManager


# Pydantic Model for Decomposer Structured Output
class DecomposedTask(BaseModel):
    subtasks: List[str] = Field(
        ...,
        description=(
            "An ordered list of atomic, natural-language subtasks. Each subtask must be precise and actionable, without code or commentary."
        ),
    )

# Pydantic Model for Reflector Structured Output
class ReflectorVerdict(BaseModel):
    is_solved: bool = Field(
        ..., description="True if the problem was solved, otherwise False"
    )
    issues: Optional[str] = Field(..., description="A concise explanation of any real issues, errors, or missing outputs identified during the review. If no issues were found, ignore this field")


class GraphRunnables:
    def __init__(self):
        settings = get_settings()
        # Load prompt manager
        self.prompt_manager = PromptManager()

        # Load Runnables
        self.decomposer_chain = self.get_decomposer_chain(settings)
        self.actor_chain = self.get_actor_chain(settings)
        self.reflector_chain = self.get_reflector_chain(settings)

    def get_decomposer_chain(self, settings: SheetAgentSettings) -> Runnable:
        decomposer_model = ChatOpenAI(
            model=settings.MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        ).with_structured_output(DecomposedTask, method="json_schema")
        
        return self.prompt_manager.decomposer_prompt | decomposer_model


    def get_actor_chain(self, settings: SheetAgentSettings) -> Runnable:
        # NOTE: Importing here to avoid circular import with tools.py/state.py
        from app.graph.tools import python_executor
        actor_model = ChatOpenAI(
            model=settings.MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        
        tools = [python_executor]
        actor_model = actor_model.bind_tools(tools, tool_choice="python_executor")
        
        return self.prompt_manager.actor_prompt | actor_model

    def get_reflector_chain(self, settings: SheetAgentSettings) -> Runnable:
        reflector_model = ChatOpenAI(
            model=settings.MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        ).with_structured_output(ReflectorVerdict, method="json_schema")
        
        return self.prompt_manager.reflector_prompt | reflector_model
    
    
    
    

