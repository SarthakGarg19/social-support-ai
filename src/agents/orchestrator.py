"""
Master Orchestrator Agent using LangGraph

This is the CORE of the agentic AI system. It coordinates all specialized agents
in a stateful workflow graph using LangGraph.

LangGraph Workflow:
1. Data Extraction → 2. Data Validation → 3. Eligibility Check → 4. Recommendation → 5. Final Decision

Each node in the graph represents an agent, and edges define the flow.
The orchestrator maintains state across the entire workflow.
"""

from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator
from datetime import datetime

from .base_agent import BaseAgent, AgentState, AgentResponse
from .data_extraction import data_extraction_agent
from .data_validation import data_validation_agent
from .eligibility_check import eligibility_check_agent
from .recommendation import recommendation_agent
from ..database import db_manager
from ..utils import log_workflow_state, flush_langfuse


# Define the state structure for the workflow
class WorkflowState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    
    This state is passed between agents and updated at each step.
    LangGraph manages the state transitions automatically.
    """
    applicant_id: str
    applicant_name: str
    applicant_data: Dict[str, Any]
    documents: List[Dict[str, Any]]
    extracted_data: Dict[str, Any]
    validation_results: Dict[str, Any]
    eligibility_results: Dict[str, Any]
    recommendations: Dict[str, Any]
    final_decision: Dict[str, Any]
    errors: Annotated[List[str], operator.add]  # Accumulate errors
    stage: str
    metadata: Dict[str, Any]


class OrchestratorAgent(BaseAgent):
    """
    Master Orchestrator Agent using LangGraph for multi-agent workflow.
    
    This agent:
    1. Manages the overall application processing workflow
    2. Coordinates specialized agents (extraction, validation, eligibility, recommendation)
    3. Maintains state across the workflow using LangGraph
    4. Handles errors and retries
    5. Provides end-to-end observability
    
    Architecture:
    - Uses StateGraph from LangGraph for workflow definition
    - Each agent is a node in the graph
    - Conditional edges handle decision points
    - State is maintained and passed between nodes
    """
    
    def __init__(self):
        super().__init__(
            name="OrchestratorAgent",
            description="Master orchestrator coordinating all agents using LangGraph"
        )
        self.workflow = self._build_workflow()
    
    def reason(self, state: AgentState) -> str:
        """
        High-level orchestration reasoning.
        
        Determines the overall workflow strategy.
        """
        return """
        Orchestration Strategy:
        
        1. EXTRACT: Process all uploaded documents
        2. VALIDATE: Ensure data quality and consistency
        3. ASSESS: Determine eligibility based on criteria
        4. RECOMMEND: Provide economic enablement recommendations
        5. DECIDE: Make final decision and store results
        
        Using LangGraph for stateful multi-agent coordination.
        Each agent operates independently but shares state through the graph.
        """
    
    def act(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the workflow using LangGraph.
        """
        # This is handled by the workflow graph
        return {
            'action': 'orchestrate_workflow',
            'success': True,
            'message': 'Workflow managed by LangGraph'
        }
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        This defines the complete agent workflow as a directed graph:
        
        START → extract_documents → validate_data → check_eligibility → generate_recommendations → finalize → END
        
        Each node is an agent function that processes the state.
        """
        # Initialize the workflow graph with our state structure
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agents) to the graph
        workflow.add_node("extract_documents", self._extract_documents_node)
        workflow.add_node("validate_data", self._validate_data_node)
        workflow.add_node("check_eligibility", self._check_eligibility_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define the edges (workflow flow)
        workflow.set_entry_point("extract_documents")
        
        # Linear flow with conditional branching
        workflow.add_edge("extract_documents", "validate_data")
        
        # Conditional edge: only proceed if validation passes
        workflow.add_conditional_edges(
            "validate_data",
            self._should_proceed_after_validation,
            {
                "proceed": "check_eligibility",
                "end": END  # End early if validation fails critically
            }
        )
        
        workflow.add_edge("check_eligibility", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _extract_documents_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 1: Document Extraction
        
        Processes all uploaded documents and extracts structured data.
        """
        print(f"\n[ORCHESTRATOR] Stage 1: Extracting documents for applicant {state['applicant_id']}")
        
        state['stage'] = 'extraction'
        extracted_data = {}
        
        # Process each document
        for doc in state.get('documents', []):
            try:
                # Call data extraction agent
                result = data_extraction_agent.execute({
                    'applicant_id': state['applicant_id'],
                    'doc_type': doc['type'],
                    'file_path': doc['path']
                })
                
                if result['result']['success']:
                    # Merge extracted data
                    doc_data = result['result']['extracted_data']
                    extracted_data.update(doc_data)
                    
                    print(f"  ✓ Extracted {doc['type']}: {doc_data.get('summary', 'Success')}")
                else:
                    error_msg = f"Failed to extract {doc['type']}: {result['result'].get('error', 'Unknown error')}"
                    state['errors'].append(error_msg)
                    print(f"  ✗ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Exception extracting {doc.get('type', 'unknown')}: {str(e)}"
                state['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
        
        # Add defaults from applicant data if extraction failed
        if not extracted_data.get('monthly_income') and state['applicant_data'].get('monthly_income'):
            extracted_data['monthly_income'] = state['applicant_data']['monthly_income']
        
        if not extracted_data.get('employment_status') and state['applicant_data'].get('employment_status'):
            extracted_data['employment_status'] = state['applicant_data']['employment_status']
        
        if not extracted_data.get('total_assets') and state['applicant_data'].get('total_assets'):
            extracted_data['total_assets'] = state['applicant_data']['total_assets']
        
        if not extracted_data.get('total_liabilities') and state['applicant_data'].get('total_liabilities'):
            extracted_data['total_liabilities'] = state['applicant_data']['total_liabilities']
        
        if not extracted_data.get('credit_score') and state['applicant_data'].get('credit_score'):
            extracted_data['credit_score'] = state['applicant_data']['credit_score']
        
        state['extracted_data'] = extracted_data
        
        # Update workflow state in database
        db_manager.update_workflow_state(
            state['applicant_id'],
            'extraction_complete',
            {'extracted_data': extracted_data}
        )
        
        return state
    
    def _validate_data_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 2: Data Validation
        
        Validates extracted data for completeness and consistency.
        """
        print(f"\n[ORCHESTRATOR] Stage 2: Validating data")
        
        state['stage'] = 'validation'
        
        try:
            # Call data validation agent
            result = data_validation_agent.execute({
                'applicant_id': state['applicant_id'],
                'extracted_data': state['extracted_data']
            })
            
            validation_results = result['result']['validation_results']
            state['validation_results'] = validation_results
            
            print(f"  Completeness: {validation_results['completeness_score']*100:.0f}%")
            print(f"  Valid: {validation_results['is_valid']}")
            
            if validation_results['warnings']:
                print(f"  Warnings: {len(validation_results['warnings'])}")
                for warning in validation_results['warnings']:
                    print(f"    - {warning}")
            
            if validation_results['issues']:
                print(f"  Issues: {len(validation_results['issues'])}")
                for issue in validation_results['issues']:
                    print(f"    - {issue}")
                    state['errors'].append(f"Validation: {issue}")
            
            # Update workflow state
            db_manager.update_workflow_state(
                state['applicant_id'],
                'validation_complete',
                {'validation_results': validation_results}
            )
            
        except Exception as e:
            error_msg = f"Validation exception: {str(e)}"
            state['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
            state['validation_results'] = {
                'is_valid': False,
                'completeness_score': 0.0,
                'issues': [error_msg]
            }
        
        return state
    
    def _should_proceed_after_validation(self, state: WorkflowState) -> str:
        """
        Conditional edge: Decide whether to proceed after validation.
        Ends workflow if validation fails or requires user action (e.g., employment/income mismatch).
        """
        validation_results = state.get('validation_results', {})
        # End if requires_user_action is set (critical validation failure)
        if validation_results.get('requires_user_action', False):
            print("\n[ORCHESTRATOR] ⚠️  User action required - ending workflow early")
            return "end"
        # Proceed only if validation passed
        if validation_results.get('is_valid', False):
            return "proceed"
        else:
            print("\n[ORCHESTRATOR] ⚠️  Insufficient data - ending workflow early")
            return "end"
    
    def _check_eligibility_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 3: Eligibility Check
        
        Determines eligibility for social support.
        """
        print(f"\n[ORCHESTRATOR] Stage 3: Checking eligibility")
        
        state['stage'] = 'eligibility'
        
        try:
            # Prepare applicant data
            applicant_data = {
                'applicant_name': state["applicant_name"] if "applicant_name" in state else "Unknown",
                'monthly_income': state['extracted_data'].get('monthly_income', 0),
                'employment_status': state['extracted_data'].get('employment_status', 'unknown'),
                'family_size': state['applicant_data'].get('family_size', 1),
                'total_assets': state['extracted_data'].get('total_assets', 0),
                'total_liabilities': state['extracted_data'].get('total_liabilities', 0),
                'asset_liability_ratio': state['extracted_data'].get('asset_liability_ratio', 0),
                'credit_score': state['extracted_data'].get('credit_score', 0)
            }
            
            # Call eligibility check agent
            result = eligibility_check_agent.execute({
                'applicant_data': applicant_data
            })
            
            eligibility_results = result['result']
            state['eligibility_results'] = eligibility_results
            
            print(f"  Score: {eligibility_results['eligibility_score']}/100")
            print(f"  Decision: {eligibility_results['decision']}")
            print(f"  Confidence: {eligibility_results['confidence']}")
            
            # Update workflow state
            db_manager.update_workflow_state(
                state['applicant_id'],
                'eligibility_complete',
                {'eligibility_results': eligibility_results}
            )
            
        except Exception as e:
            error_msg = f"Eligibility check exception: {str(e)}"
            state['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
            state['eligibility_results'] = {
                'eligibility_score': 0,
                'decision': 'ERROR',
                'confidence': 'NONE'
            }
        
        return state
    
    def _generate_recommendations_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 4: Generate Recommendations
        
        Provides personalized economic enablement recommendations.
        """
        print(f"\n[ORCHESTRATOR] Stage 4: Generating recommendations")
        
        state['stage'] = 'recommendations'
        
        try:
            # Prepare data
            applicant_data = {
                'applicant_name': state["applicant_name"] if "applicant_name" in state else "Unknown",
                'monthly_income': state['extracted_data'].get('monthly_income', 0),
                'employment_status': state['extracted_data'].get('employment_status', 'unknown'),
                'family_size': state['applicant_data'].get('family_size', 1)
            }
            
            # Call recommendation agent
            result = recommendation_agent.execute({
                'applicant_data': applicant_data,
                'eligibility_result': state['eligibility_results']
            })
            
            recommendations = result['result']['recommendations']
            state['recommendations'] = recommendations
            
            print(f"  Total programs: {result['result']['total_programs']}")
            for program in recommendations.get('priority_programs', []):
                print(f"  - {program['category']} ({program['priority']} priority)")
            
            # Update workflow state
            db_manager.update_workflow_state(
                state['applicant_id'],
                'recommendations_complete',
                {'recommendations': recommendations}
            )
            
        except Exception as e:
            error_msg = f"Recommendation exception: {str(e)}"
            state['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
            state['recommendations'] = {
                'priority_programs': [],
                'personalized_advice': 'Unable to generate recommendations'
            }
        
        return state
    
    def _finalize_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 5: Finalize Decision
        
        Creates final assessment and stores in database.
        """
        print(f"\n[ORCHESTRATOR] Stage 5: Finalizing decision")
        
        state['stage'] = 'finalized'
        
        # Compile final decision
        final_decision = {
            'applicant_id': state['applicant_id'],
            'applicant_name': state['applicant_data'].get('name', 'Unknown'),
            'eligibility_score': state['eligibility_results'].get('eligibility_score', 0),
            'decision': state['eligibility_results'].get('decision', 'PENDING'),
            'reasoning': state['eligibility_results'].get('explanation', ''),
            'recommendations': state['recommendations'],
            'completed_at': datetime.now().isoformat(),
            'has_errors': len(state.get('errors', [])) > 0,
            'errors': state.get('errors', [])
        }
        
        state['final_decision'] = final_decision
        
        # Save assessment to database
        try:
            assessment_id = db_manager.save_assessment({
                'applicant_id': state['applicant_id'],
                'eligibility_score': final_decision['eligibility_score'],
                'decision': final_decision['decision'],
                'reasoning': final_decision['reasoning'],
                'recommendations': state['recommendations']
            })
            
            print(f"  ✓ Assessment saved: {assessment_id}")
            print(f"  Final Decision: {final_decision['decision']}")
            
            # Update workflow state
            db_manager.update_workflow_state(
                state['applicant_id'],
                'completed',
                {'final_decision': final_decision}
            )
            
            # Log workflow completion to Langfuse
            try:
                log_workflow_state(
                    applicant_id=state['applicant_id'],
                    workflow_stage='completed',
                    stage_data={
                        'final_decision': final_decision['decision'],
                        'eligibility_score': final_decision['eligibility_score'],
                        'recommendation_count': len(state['recommendations']),
                        'workflow_errors': len(state.get('errors', []))
                    }
                )
                # Flush all pending traces to Langfuse
                flush_langfuse()
            except Exception as log_err:
                # Langfuse logging should not fail the workflow
                pass
            
        except Exception as e:
            error_msg = f"Failed to save assessment: {str(e)}"
            state['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
        
        return state
    
    def process_application(
        self,
        applicant_id: str,
        applicant_data: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main entry point for processing an application.
        
        This initiates the LangGraph workflow.
        
        Args:
            applicant_id: Unique applicant identifier
            applicant_data: Basic applicant information (name, family size, etc.)
            documents: List of uploaded documents with type and path
            
        Returns:
            Final decision and recommendations
        """
        print(f"\n{'='*60}")
        print(f"ORCHESTRATOR: Processing application {applicant_id}")
        print(f"{'='*60}")

        # Initialize workflow state
        initial_state: WorkflowState = {
            'applicant_id': applicant_id,
            'applicant_name': applicant_data.get('name', 'Unknown'),
            'applicant_data': applicant_data,
            'documents': documents,
            'extracted_data': {},
            'validation_results': {},
            'eligibility_results': {},
            'recommendations': {},
            'final_decision': {},
            'errors': [],
            'stage': 'initiated',
            'metadata': {
                'started_at': datetime.now().isoformat(),
                'workflow_version': '1.0'
            }
        }
        
        # Log workflow initiation to Langfuse
        try:
            log_workflow_state(
                applicant_id=applicant_id,
                workflow_stage='initiated',
                stage_data={
                    'documents_count': len(documents),
                    'applicant_data_keys': list(applicant_data.keys())
                }
            )
        except Exception as log_err:
            # Langfuse logging should not fail the workflow
            pass
        
        # Run the workflow
        try:
            from langfuse.langchain import CallbackHandler
            langfuse_handler = CallbackHandler()
            
            final_state = self.workflow.invoke(initial_state, config={
                'callbacks': [langfuse_handler]})
            
            print(f"\n{'='*60}")
            print(f"WORKFLOW COMPLETE")
            print(f"{'='*60}")
            print(f"Stages completed: {final_state['stage']}")
            print(f"Decision: {final_state['final_decision'].get('decision', 'UNKNOWN')}")
            print(f"Errors: {len(final_state.get('errors', []))}")
            
            return final_state['final_decision'], final_state['errors']
            
        except Exception as e:
            print(f"\nX WORKFLOW FAILED: {str(e)}")
            return {
                'applicant_id': applicant_id,
                'decision': 'ERROR',
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }


    def export_stategraph_mermaid(self) -> str:
        """
        Export the LangGraph workflow as a Mermaid diagram.
        
        Args:
            output_path: Path to save the mermaid file
            
        Returns:
            Path to the saved file
        """

        png_data = self.workflow.get_graph().draw_mermaid_png()
        output_filename = "docs/stategraph_mermaid_output.png"
        try:
            with open(output_filename, 'wb') as f:
                f.write(png_data)
            print(f"Image successfully saved to {output_filename}")
        except IOError as e:
            print(f"Error saving image: {e}")

# Global orchestrator instance
orchestrator = OrchestratorAgent()
