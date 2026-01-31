"""
Langfuse Integration Utilities

Provides observability and tracing for LLM calls and agent execution.
"""

from langfuse import Langfuse
from typing import Optional, Dict, Any
from ..config import settings

# Initialize Langfuse client
langfuse_client: Optional[Langfuse] = None


def init_langfuse():
    """Initialize Langfuse client with credentials from settings."""
    global langfuse_client
    
    try:
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            langfuse_client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host
            )
            return langfuse_client
        else:
            return None
    except Exception:
        return None

def trace_llm_call(agent_name: str, prompt: str, model: str = "llama3.2"):
    """
    Decorator to trace LLM calls with Langfuse.
    
    Usage:
        @trace_llm_call("DataValidationAgent", "prompt_text")
        def my_llm_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not langfuse_client:
                return func(*args, **kwargs)
            
            try:
                # Log the LLM call
                trace = langfuse_client.trace(
                    name=f"{agent_name}_llm_call",
                    user_id=kwargs.get('applicant_id', 'unknown'),
                    metadata={
                        "agent": agent_name,
                        "model": model,
                    }
                )
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Log completion
                if isinstance(result, dict):
                    trace.update(
                        output=result,
                        status_code=200
                    )
                
                return result
                
            except Exception as e:
                if langfuse_client:
                    trace.update(
                        output={"error": str(e)},
                        status_code=500
                    )
                raise
        
        return wrapper
    return decorator


def log_agent_execution(
    agent_name: str,
    applicant_id: str,
    stage: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    success: bool = True,
    error: Optional[str] = None
):
    """
    Log agent execution to Langfuse.
    
    Args:
        agent_name: Name of the agent
        applicant_id: Applicant identifier
        stage: Processing stage
        input_data: Input data to the agent
        output_data: Output data from the agent
        success: Whether execution was successful
        error: Error message if failed
    """
    if not langfuse_client:
        return
    
    try:
        span = langfuse_client.start_span(
            name=f"{agent_name}_{stage}",
            metadata={
                "agent": agent_name,
                "stage": stage,
                "applicant_id": applicant_id,
                "success": success,
            },
            input=input_data
        )
        
        span.end(
            output=output_data,
            level="INFO" if success else "ERROR"
        )
        
    except Exception:
        pass


def log_workflow_state(
    applicant_id: str,
    workflow_stage: str,
    stage_data: Dict[str, Any]
):
    """
    Log workflow state transitions to Langfuse.
    
    Args:
        applicant_id: Applicant identifier
        workflow_stage: Current workflow stage
        stage_data: Stage-specific data
    """
    if not langfuse_client:
        return
    
    try:
        event = langfuse_client.create_event(
            name=f"workflow_transition",
            metadata={
                "applicant_id": applicant_id,
                "stage": workflow_stage,
                **stage_data
            }
        )
    except Exception:
        pass


def log_eligibility_decision(
    applicant_id: str,
    decision: str,
    reasoning: str,
    scores: Dict[str, Any]
):
    """
    Log eligibility decision to Langfuse.
    
    Args:
        applicant_id: Applicant identifier
        decision: APPROVED, DECLINED, or UNDER_REVIEW
        reasoning: Decision reasoning
        scores: Scoring breakdown
    """
    if not langfuse_client:
        return
    
    try:
        span = langfuse_client.start_span(
            name="eligibility_decision",
            metadata={
                "applicant_id": applicant_id,
                "decision": decision,
                "scores": str(scores)
            },
            input={"applicant_id": applicant_id}
        )
        
        span.end(
            output={"decision": decision, "reasoning": reasoning}
        )
        
    except Exception as e:
        print(f"[LANGFUSE] Failed to log eligibility decision: {e}")


def flush_langfuse():
    """Flush any pending traces to Langfuse."""
    if langfuse_client:
        try:
            langfuse_client.flush()
        except Exception as e:
            print(f"[LANGFUSE] Failed to flush traces: {e}")


# Initialize on module import
init_langfuse()
