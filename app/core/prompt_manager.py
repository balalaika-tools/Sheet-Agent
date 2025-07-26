"""
Prompt manager module for SheetAgent.

This module provides a centralized class for managing prompt templates for the planner model.
It loads system prompts and few-shot examples from the prompt directory.
"""

import os

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate

from app.utils.utils import load_config


class PromptManager:
    """
    A class that centralizes the management of prompt templates for different model types.

    This class contains all prompt string constants and methods for loading few-shot examples
    and creating prompt templates for planner model.
    """

    def __init__(self):
        # Get the current path of the prompt directory and load prompt templates for each Runnable
        self.prompt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")
        
        # Define propmt templates for each runnable agent
        self.decomposer_prompt = type(self).get_prompt_template(os.path.join(self.prompt_dir, "decomposer.yaml"))
        self.actor_prompt = type(self).get_prompt_template(os.path.join(self.prompt_dir, "actor.yaml"))
        self.reflector_prompt = type(self).get_prompt_template(os.path.join(self.prompt_dir, "reflector.yaml"))
        
    @staticmethod
    def get_prompt_template(prompt_path: str) -> ChatPromptTemplate:
        prompt = load_config(prompt_path)
        system_prompt = SystemMessagePromptTemplate.from_template(prompt.get("system"))
        user_prompt = HumanMessagePromptTemplate.from_template(prompt.get("user"))
        return ChatPromptTemplate.from_messages([system_prompt, user_prompt])
    



