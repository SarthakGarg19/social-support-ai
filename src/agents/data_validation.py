"""
Data Validation Agent

This agent validates extracted data for:
- Completeness
- Consistency across documents
- Data quality
- Cross-referencing

Uses ReAct pattern for intelligent validation with LLM reasoning.
"""

from typing import Dict, Any, List, Optional
import ollama

from .base_agent import BaseAgent, AgentState, AgentResponse
from ..database import db_manager, vector_store
from ..config import settings
from ..utils import log_agent_execution


class DataValidationAgent(BaseAgent):
    """
    Agent specialized in validating extracted data for consistency and completeness.
    
    Capabilities:
    - Cross-document validation
    - Data completeness checks
    - Consistency verification
    - Anomaly detection
    
    Reasoning: Uses LLM to identify inconsistencies and missing data
    Action: Validates data across documents
    Observation: Reports validation results and issues
    """
    
    def __init__(self):
        super().__init__(
            name="DataValidationAgent",
            description="Validates data consistency and completeness across documents"
        )
    
    def reason(self, state: AgentState) -> str:
        """
        Analyze data for validation needs.
        
        ReAct Reasoning:
        - Identify required fields
        - Check for cross-document consistency
        - Determine validation rules
        """
        applicant_id = state.context.get('applicant_id')
        extracted_data = state.context.get('extracted_data', {})
        
        reasoning = f"""
        Validation Analysis for Applicant {applicant_id}:
        
        Required Data Points:
        1. Personal Information (from Emirates ID)
        2. Income Information (from Bank Statement)
        3. Employment Status (from Resume)
        4. Financial Position (from Assets/Liabilities)
        5. Credit Score (from Credit Report)
        
        Validation Checks:
        - Are all required documents present?
        - Is the data complete within each document?
        - Are there inconsistencies across documents?
        - Are values within reasonable ranges?
        - Check if employment status aligns with income reported.
        - Verify asset/liability ratios.
        - Flag any anomalies or missing information.
        
        Using LLM to perform deep semantic validation...
        """
        
        return reasoning
    
    def act(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute validation checks.
        
        ReAct Action:
        - Check data completeness
        - Cross-reference information
        - Use LLM for semantic validation
        - Flag inconsistencies
        """
        applicant_id = state.context.get('applicant_id')
        extracted_data = state.context.get('extracted_data', {})
        
        validation_results = {
            'is_valid': True,
            'completeness_score': 0.0,
            'issues': [],
            'warnings': [],
            'validated_data': {},
            'requires_user_action': False  # New flag for critical user action
        }
        
        # Check completeness
        required_fields = [
            'monthly_income',
            'employment_status',
            'total_assets',
            'total_liabilities',
            'credit_score'
        ]
        
        present_fields = 0
        missing_fields = []
        
        for field in required_fields:
            if field in extracted_data and extracted_data[field] is not None:
                present_fields += 1
                validation_results['validated_data'][field] = extracted_data[field]
            else:
                missing_fields.append(field)
        
        validation_results['completeness_score'] = present_fields / len(required_fields)
        
        # Validate data ranges
        if 'monthly_income' in extracted_data:
            income = extracted_data['monthly_income']
            if income < 0:
                validation_results['issues'].append("Monthly income cannot be negative")
                validation_results['is_valid'] = False
            elif income > 1000000:
                validation_results['warnings'].append("Unusually high monthly income")
        
        if 'credit_score' in extracted_data:
            score = extracted_data['credit_score']
            if score < 300 or score > 850:
                validation_results['warnings'].append(f"Credit score {score} outside typical range (300-850)")
        
        if 'asset_liability_ratio' in extracted_data:
            ratio = extracted_data['asset_liability_ratio']
            if ratio < 0:
                validation_results['issues'].append("Asset-liability ratio cannot be negative")
                validation_results['is_valid'] = False

        # Employment/Income mismatch check
        # If income is reported but employment status is not employed, flag for user action
        employment_status = extracted_data.get('employment_status', '').lower()
        has_income = extracted_data.get('monthly_income', 0) > 0
        if has_income and employment_status not in ['employed', 'self-employed', 'business owner']:
            validation_results['issues'].append(
                "Income detected but employment status is not 'employed'. Please upload an updated resume or clarify employment status."
            )
            validation_results['is_valid'] = False
            validation_results['requires_user_action'] = True
        
        # Use LLM for semantic validation
        if validation_results['completeness_score'] > 0.5:
            llm_validation = self._llm_validate(extracted_data)
            validation_results['llm_insights'] = llm_validation
        
        # Mark as critical if completeness is too low
        if validation_results['completeness_score'] < 0.5:
            validation_results['is_valid'] = False
            validation_results['issues'].append(
                f"Insufficient data: only {validation_results['completeness_score']*100:.0f}% complete"
            )
        else:
            # Allow processing with warnings if at least 50% of data is present
            validation_results['is_valid'] = True
        
        # Log to Langfuse
        applicant_id = state.context.get('applicant_id', 'unknown')
        log_agent_execution(
            agent_name=self.name,
            applicant_id=applicant_id,
            stage='validation',
            input_data=extracted_data,
            output_data=validation_results,
            success=validation_results['is_valid'],
            error=None if validation_results['is_valid'] else ' | '.join(validation_results['issues'])
        )
        
        return {
            'action': 'validate_data',
            'success': True,
            'validation_results': validation_results
        }
    
    def _llm_validate(self, extracted_data: Dict[str, Any]) -> str:
        """
        Use local LLM to perform semantic validation.
        
        This demonstrates LLM integration for intelligent data validation.
        """
        try:
            # Prepare prompt for LLM
            prompt = f"""
You are a data validation expert for a social support application system.

Review the following extracted applicant data and identify any inconsistencies, anomalies, or concerns:

Data:
{self._format_data_for_llm(extracted_data)}

Provide a brief validation assessment covering:
1. Data consistency
2. Any red flags or anomalies
3. Data quality assessment
4. Recommendations for missing information

Keep your response concise (2-3 sentences).
"""
            
            # Call local Ollama LLM
            response = ollama.generate(
                model=settings.ollama_model,
                prompt=prompt
            )
            
            return response['response']
            
        except Exception as e:
            return f"LLM validation unavailable: {str(e)}"
    
    def _format_data_for_llm(self, data: Dict[str, Any]) -> str:
        """Format extracted data for LLM prompt."""
        formatted = []
        
        if 'monthly_income' in data:
            formatted.append(f"- Monthly Income: AED {data['monthly_income']:,.2f}")
        if 'employment_status' in data:
            formatted.append(f"- Employment Status: {data['employment_status']}")
        if 'total_assets' in data:
            formatted.append(f"- Total Assets: AED {data['total_assets']:,.2f}")
        if 'total_liabilities' in data:
            formatted.append(f"- Total Liabilities: AED {data['total_liabilities']:,.2f}")
        if 'asset_liability_ratio' in data:
            formatted.append(f"- Asset/Liability Ratio: {data['asset_liability_ratio']:.2f}")
        if 'credit_score' in data:
            formatted.append(f"- Credit Score: {data['credit_score']}")
        if 'family_size' in data:
            formatted.append(f"- Family Size: {data['family_size']}")
        
        return "\n".join(formatted) if formatted else "No data available"

# Global instance
data_validation_agent = DataValidationAgent()
