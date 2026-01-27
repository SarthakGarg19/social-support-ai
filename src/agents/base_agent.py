"""
Base Agent Classes for Social Support AI System

This module defines the foundational agent architecture using ReAct pattern
(Reasoning and Acting) for agentic AI workflows.

The ReAct pattern enables agents to:
1. Reason about the current state and task
2. Act by executing specific operations
3. Observe the results
4. Reflect and adjust their approach
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import json


class AgentState:
    """
    Represents the state of an agent during execution.
    
    This includes:
    - Current task context
    - Observations from previous actions
    - Reasoning history
    - Action history
    """
    
    def __init__(self, initial_context: Dict[str, Any] = None):
        self.context = initial_context or {}
        self.observations = []
        self.reasoning_history = []
        self.action_history = []
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "agent_calls": 0
        }
    
    def add_observation(self, observation: str, data: Any = None):
        """Add an observation from an action."""
        self.observations.append({
            "timestamp": datetime.now().isoformat(),
            "observation": observation,
            "data": data
        })
    
    def add_reasoning(self, reasoning: str):
        """Add reasoning step."""
        self.reasoning_history.append({
            "timestamp": datetime.now().isoformat(),
            "reasoning": reasoning
        })
    
    def add_action(self, action: str, result: Any = None):
        """Add action taken by agent."""
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": result
        })
        self.metadata["agent_calls"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get state summary for logging/debugging."""
        return {
            "context": self.context,
            "num_observations": len(self.observations),
            "num_reasoning_steps": len(self.reasoning_history),
            "num_actions": len(self.action_history),
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Implements the ReAct pattern:
    - Reason: Analyze current state and determine next action
    - Act: Execute the determined action
    - Observe: Collect results from the action
    
    Each specialized agent inherits from this base and implements
    specific reasoning and action logic.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent purpose/capability description
        """
        self.name = name
        self.description = description
        self.state = None
    
    @abstractmethod
    def reason(self, state: AgentState) -> str:
        """
        Reasoning step: Analyze state and determine what to do next.
        
        This implements the "Think" part of ReAct.
        
        Args:
            state: Current agent state
            
        Returns:
            Reasoning explanation
        """
        pass
    
    @abstractmethod
    def act(self, state: AgentState) -> Dict[str, Any]:
        """
        Action step: Execute the determined action.
        
        This implements the "Act" part of ReAct.
        
        Args:
            state: Current agent state
            
        Returns:
            Action result
        """
        pass
    
    def observe(self, state: AgentState, action_result: Dict[str, Any]) -> str:
        """
        Observation step: Process action results.
        
        This implements the "Observe" part of ReAct.
        
        Args:
            state: Current agent state
            action_result: Results from the action
            
        Returns:
            Observation summary
        """
        observation = f"Action completed: {action_result.get('action', 'unknown')}"
        state.add_observation(observation, action_result)
        return observation
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution loop implementing ReAct pattern.
        
        Flow:
        1. Initialize state with context
        2. Reason about what to do
        3. Act on the reasoning
        4. Observe the results
        5. Return final result
        
        Args:
            context: Input context for the agent
            
        Returns:
            Execution result
        """
        # Initialize state
        self.state = AgentState(initial_context=context)
        
        # Reason
        reasoning = self.reason(self.state)
        self.state.add_reasoning(reasoning)
        
        # Act
        action_result = self.act(self.state)
        self.state.add_action(f"{self.name} action", action_result)
        
        # Observe
        observation = self.observe(self.state, action_result)
        
        # Return result with metadata
        return {
            "agent": self.name,
            "result": action_result,
            "observation": observation,
            "reasoning": reasoning,
            "state_summary": self.state.get_summary()
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class AgentTool:
    """
    Represents a tool that agents can use.
    
    Tools are specific capabilities agents can invoke, such as:
    - Extracting text from PDFs
    - Querying databases
    - Calling external APIs
    """
    
    def __init__(self, name: str, description: str, func: callable):
        """
        Initialize agent tool.
        
        Args:
            name: Tool name
            description: What the tool does
            func: Function to execute
        """
        self.name = name
        self.description = description
        self.func = func
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given arguments."""
        return self.func(**kwargs)
    
    def __repr__(self) -> str:
        return f"AgentTool(name='{self.name}')"


class AgentResponse:
    """
    Standardized response format for agent communications.
    
    This ensures consistent communication between agents in the
    multi-agent orchestration system.
    """
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILURE"
        return f"AgentResponse({status})"
