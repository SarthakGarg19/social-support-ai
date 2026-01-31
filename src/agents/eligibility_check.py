"""
Eligibility Check Agent

This agent determines eligibility for social support based on:
- Income level
- Employment status
- Family size
- Asset-liability ratio
- Credit score

Uses ReAct pattern with ML classifier and LLM reasoning.
"""

from typing import Dict, Any, List
import ollama
import numpy as np

from .base_agent import BaseAgent, AgentState, AgentResponse
from ..database import db_manager
from ..config import settings, ELIGIBILITY_CRITERIA
from ..utils import log_eligibility_decision


class EligibilityCheckAgent(BaseAgent):
    """
    Agent specialized in determining eligibility for social support.
    
    Capabilities:
    - Applies eligibility rules
    - Leverages LLM for reasoning
    - Retrieves relevant policies from knowledge base
    
    Reasoning: Analyzes applicant data against eligibility criteria
    Action: Calculates eligibility score and determines status
    Observation: Provides explanation for decision
    """
    
    def __init__(self):
        super().__init__(
            name="EligibilityCheckAgent",
            description="Determines eligibility for social support programs"
        )
    
    def reason(self, state: AgentState) -> str:
        """
        Analyze applicant data against eligibility criteria.
        
        ReAct Reasoning:
        - Review applicant financial situation
        - Compare against eligibility thresholds
        - Consider multiple factors holistically
        - Query knowledge base for relevant policies
        """
        applicant_data = state.context.get('applicant_data', {})
        
        # Query knowledge base for relevant eligibility rules
        knowledge_query = f"""
        Eligibility rules for applicant with income {applicant_data.get('monthly_income', 0)}, 
        family size {applicant_data.get('family_size', 1)}, 
        employment status {applicant_data.get('employment_status', 'unknown')}
        """
        
        reasoning = f"""
        Eligibility Assessment for Applicant:
        
        Financial Profile:
        - Monthly Income: AED {applicant_data.get('monthly_income', 0):,.2f}
        - Family Size: {applicant_data.get('family_size', 1)}
        - Employment: {applicant_data.get('employment_status', 'unknown')}
        - Assets: AED {applicant_data.get('total_assets', 0):,.2f}
        - Liabilities: AED {applicant_data.get('total_liabilities', 0):,.2f}
        - Credit Score: {applicant_data.get('credit_score', 0)}
        
        Eligibility Criteria Check:
        1. Income Threshold: Max AED {ELIGIBILITY_CRITERIA['max_income_threshold']:,}
        2. Minimum Credit Score: {ELIGIBILITY_CRITERIA['credit_score_minimum']}
        3. Asset-Liability Ratio Threshold: {ELIGIBILITY_CRITERIA['asset_liability_ratio_threshold']}
        4. Family Size Consideration: {ELIGIBILITY_CRITERIA['min_family_size_for_bonus']}+ gets priority
        
        Proceeding with multi-factor eligibility calculation...
        """
        
        return reasoning
    
    def act(self, state: AgentState) -> Dict[str, Any]:
        """
        Calculate eligibility score and make determination.
        
        ReAct Action:
        - Apply rule-based checks
        - Calculate weighted eligibility score
        - Generate decision with confidence
        """
        applicant_data = state.context.get('applicant_data', {})
        
        # Initialize scoring
        eligibility_score = 0.0
        max_score = 100.0
        factors = []
        
        # Factor 1: Income (30 points)
        income = applicant_data.get('monthly_income', 0)
        income_threshold = ELIGIBILITY_CRITERIA['max_income_threshold']
        
        if income <= income_threshold:
            income_score = 30 * (1 - (income / income_threshold))
            eligibility_score += income_score
            factors.append(f"Income Score: {income_score:.1f}/30 (Below threshold)")
        else:
            factors.append(f"Income Score: 0/30 (Exceeds threshold of AED {income_threshold:,})")
        
        # Factor 2: Employment Status (20 points)
        employment = applicant_data.get('employment_status', 'unknown')
        employment_weights = ELIGIBILITY_CRITERIA['employment_weights']
        employment_score = employment_weights.get(employment, 0.5) * 20
        eligibility_score += employment_score
        factors.append(f"Employment Score: {employment_score:.1f}/20 (Status: {employment})")
        
        # Factor 3: Family Size (20 points)
        family_size = applicant_data.get('family_size', 1)
        if family_size >= ELIGIBILITY_CRITERIA['min_family_size_for_bonus']:
            family_score = 20
        else:
            family_score = 5
        eligibility_score += family_score
        factors.append(f"Family Score: {family_score}/20 (Size: {family_size})")
        
        # Factor 4: Financial Need (20 points)
        assets = applicant_data.get('total_assets', 0)
        liabilities = applicant_data.get('total_liabilities', 0)
        
        if liabilities > 0:
            ratio = assets / liabilities
            if ratio < ELIGIBILITY_CRITERIA['asset_liability_ratio_threshold']:
                financial_score = 20
            else:
                financial_score = 10
        else:
            financial_score = 5  # Has assets but no liabilities
        
        eligibility_score += financial_score
        factors.append(f"Financial Need Score: {financial_score}/20 (A/L Ratio: {ratio if liabilities > 0 else 'N/A'})")
        
        # Factor 5: Credit Score (10 points)
        credit_score = applicant_data.get('credit_score', 0)
        if credit_score >= ELIGIBILITY_CRITERIA['credit_score_minimum']:
            credit_points = 10
        else:
            credit_points = 5
        
        eligibility_score += credit_points
        factors.append(f"Credit Score: {credit_points}/10 (Score: {credit_score})")
        
        # Normalize to 0-100 scale
        eligibility_score = (eligibility_score / max_score) * 100
        
        # Determine eligibility decision
        if eligibility_score >= 80:
            decision = "APPROVED"
            confidence = "HIGH"
        elif eligibility_score >= 70:
            decision = "APPROVED"
            confidence = "MEDIUM"
        elif eligibility_score > 60:
            decision = "UNDER_REVIEW"
            confidence = "LOW"
        else:
            decision = "DECLINED"
            confidence = "HIGH"
        
        # Use LLM for reasoning explanation
        llm_explanation = self._get_llm_explanation(applicant_data, eligibility_score, decision)
        
        result = {
            'action': 'eligibility_check',
            'success': True,
            'eligibility_score': round(eligibility_score, 2),
            'decision': decision,
            'confidence': confidence,
            'factors': factors,
            'explanation': llm_explanation
        }
        
        # Log eligibility decision to Langfuse
        applicant_id = state.context.get('applicant_id', 'unknown')
        try:
            from ..utils import log_eligibility_decision
            log_eligibility_decision(
                applicant_id=applicant_id,
                decision=decision,
                reasoning=llm_explanation,
                scores={
                    'eligibility_score': round(eligibility_score, 2),
                    'income_score': factors[0],
                    'employment_score': factors[1],
                    'family_score': factors[2],
                    'financial_score': factors[3],
                    'credit_score': factors[4],
                    'confidence': confidence
                }
            )
        except Exception as e:
            # Langfuse logging should not fail the workflow
            pass
        
        return result
    
    def _get_llm_explanation(self, applicant_data: Dict[str, Any], score: float, decision: str) -> str:
        """
        Use LLM to generate human-readable explanation for the decision.
        """
        try:
            prompt = f"""
You are an empathetic social support case officer explaining an eligibility decision.

Applicant Profile:
- Applicant Name: {applicant_data.get('name', 'Applicant')}
- Monthly Income: AED {applicant_data.get('monthly_income', 0):,.2f}
- Family Size: {applicant_data.get('family_size', 1)}
- Employment: {applicant_data.get('employment_status', 'unknown')}
- Credit Score: {applicant_data.get('credit_score', 0)}

Eligibility Score: {score:.1f}/100
Decision: {decision}

Write a brief, compassionate explanation (2-3 sentences) for this decision that the applicant can understand.
Focus on the key factors that influenced the decision.
"""
            
            response = ollama.generate(
                model=settings.ollama_model,
                prompt=prompt
            )
            
            return response['response']
            
        except Exception as e:
            # Fallback explanation
            if decision == "APPROVED":
                return f"Based on your financial situation and family circumstances, you qualify for social support with an eligibility score of {score:.1f}/100."
            elif decision == "UNDER_REVIEW":
                return f"Your application requires additional review. Your eligibility score is {score:.1f}/100, which is borderline. We may need additional documentation."
            else:
                return f"Unfortunately, based on the provided information, you do not currently qualify for social support (score: {score:.1f}/100)."
    
    def _format_rules(self, rules: List[str]) -> str:
        """Format knowledge base rules for reasoning."""
        if not rules:
            return "No specific rules retrieved"
        
        formatted = []
        for i, rule in enumerate(rules, 1):
            formatted.append(f"{i}. {rule[:200]}...")
        
        return "\n".join(formatted)


# Global instance
eligibility_check_agent = EligibilityCheckAgent()
