"""
AI Agents Module for Social Support Application

This module contains all specialized agents implementing the ReAct pattern
and orchestrated using LangGraph for multi-agent coordination.

Agents:
- DataExtractionAgent: Extracts information from multimodal documents
- DataValidationAgent: Validates data consistency and completeness
- EligibilityCheckAgent: Determines social support eligibility
- RecommendationAgent: Provides economic enablement recommendations
- OrchestratorAgent: Master coordinator using LangGraph workflow

Architecture Pattern: ReAct (Reasoning and Acting)
Orchestration Framework: LangGraph (StateGraph)
LLM Integration: Ollama (local)
"""

from .base_agent import BaseAgent, AgentState, AgentResponse, AgentTool
from .data_extraction import DataExtractionAgent, data_extraction_agent
from .data_validation import DataValidationAgent, data_validation_agent
from .eligibility_check import EligibilityCheckAgent, eligibility_check_agent
from .recommendation import RecommendationAgent, recommendation_agent
from .orchestrator import OrchestratorAgent, orchestrator, WorkflowState

__all__ = [
    # Base classes
    'BaseAgent',
    'AgentState',
    'AgentResponse',
    'AgentTool',
    
    # Agent classes
    'DataExtractionAgent',
    'DataValidationAgent',
    'EligibilityCheckAgent',
    'RecommendationAgent',
    'OrchestratorAgent',
    
    # Agent instances
    'data_extraction_agent',
    'data_validation_agent',
    'eligibility_check_agent',
    'recommendation_agent',
    'orchestrator',
    
    # Workflow
    'WorkflowState'
]
