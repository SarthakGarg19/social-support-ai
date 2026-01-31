"""
Recommendation Agent

This agent provides personalized economic enablement recommendations:
- Upskilling and training programs
- Job matching services
- Career counseling
- Financial literacy programs

Uses ReAct pattern with LLM for personalized recommendations.
"""

from typing import Dict, Any, List
import ollama

from ..database import db_manager
from .base_agent import BaseAgent, AgentState, AgentResponse
from ..config import settings, ENABLEMENT_PROGRAMS
from ..utils import log_agent_execution


class RecommendationAgent(BaseAgent):
    """
    Agent specialized in providing economic enablement recommendations.
    
    Capabilities:
    - Analyzes applicant profile
    - Matches to appropriate programs
    - Provides personalized recommendations
    - Uses LLM for customized advice
    
    Reasoning: Identifies applicant needs and gaps
    Action: Generates tailored program recommendations
    Observation: Validates recommendation relevance
    """
    
    def __init__(self):
        super().__init__(
            name="RecommendationAgent",
            description="Provides personalized economic enablement recommendations"
        )
    
    def reason(self, state: AgentState) -> str:
        """
        Analyze applicant profile to determine appropriate recommendations.
        
        ReAct Reasoning:
        - Assess employment status and needs
        - Identify skills gaps
        - Consider financial literacy needs
        - Query knowledge base for relevant programs
        """
        applicant_data = state.context.get('applicant_data', {})
        eligibility_result = state.context.get('eligibility_result', {})
        
        # Query knowledge base for enablement programs
        query = f"""
        Economic enablement programs for {applicant_data.get('employment_status', 'unknown')} 
        applicant with family size {applicant_data.get('family_size', 1)}
        """
            
        reasoning = f"""
        Recommendation Analysis for Applicant:
        
        Profile Assessment:
        - Employment Status: {applicant_data.get('employment_status', 'unknown')}
        - Monthly Income: AED {applicant_data.get('monthly_income', 0):,.2f}
        - Family Size: {applicant_data.get('family_size', 1)}
        - Eligibility Decision: {eligibility_result.get('decision', 'PENDING')}
        - Eligibility Score: {eligibility_result.get('eligibility_score', 0):.1f}
        
        Needs Identification:
        """
        
        # Determine primary needs based on profile
        if applicant_data.get('employment_status') in ['unemployed', 'seeking']:
            reasoning += """
            - PRIMARY: Job placement and career development
            - SECONDARY: Skills training and upskilling
            - TERTIARY: Financial management
            """
        elif applicant_data.get('employment_status') == 'employed' and applicant_data.get('monthly_income', 0) < 8000:
            reasoning += """
            - PRIMARY: Upskilling for career advancement
            - SECONDARY: Financial literacy
            - TERTIARY: Additional income opportunities
            """
        else:
            reasoning += """
            - PRIMARY: Financial management and planning
            - SECONDARY: Career counseling
            - TERTIARY: Skills enhancement
            """
        
        reasoning += f"""
        Generating personalized recommendations using LLM...
        """
        
        return reasoning
    
    def act(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate personalized recommendations.
        
        ReAct Action:
        - Match applicant to programs
        - Prioritize recommendations
        - Use LLM for personalization
        - Create actionable plan
        """
        applicant_data = state.context.get('applicant_data', {})
        eligibility_result = state.context.get('eligibility_result', {})
        applicant_id = state.context.get('applicant_id', 'unknown')
        
        recommendations = {
            'upskilling': [],
            'job_matching': [],
            'career_counseling': [],
            'priority_programs': [],
            'personalized_advice': ''
        }
        
        employment_status = applicant_data.get('employment_status', 'unknown')
        monthly_income = applicant_data.get('monthly_income', 0)
        
        # Rule-based program matching
        if employment_status in ['unemployed', 'seeking']:
            # High priority for job matching
            recommendations['job_matching'] = ENABLEMENT_PROGRAMS['job_matching']
            recommendations['priority_programs'].append({
                'category': 'Job Matching',
                'priority': 'HIGH',
                'programs': ENABLEMENT_PROGRAMS['job_matching']
            })
            
            # Medium priority for upskilling
            recommendations['upskilling'] = ENABLEMENT_PROGRAMS['upskilling'][:2]
            recommendations['priority_programs'].append({
                'category': 'Upskilling',
                'priority': 'MEDIUM',
                'programs': ENABLEMENT_PROGRAMS['upskilling'][:2]
            })
            
            # Career counseling
            recommendations['career_counseling'] = [ENABLEMENT_PROGRAMS['career_counseling'][0]]
            
        elif employment_status == 'employed' and monthly_income < 10000:
            # Focus on upskilling for advancement
            recommendations['upskilling'] = ENABLEMENT_PROGRAMS['upskilling']
            recommendations['priority_programs'].append({
                'category': 'Upskilling',
                'priority': 'HIGH',
                'programs': ENABLEMENT_PROGRAMS['upskilling']
            })
            
            # Career counseling for advancement
            recommendations['career_counseling'] = ENABLEMENT_PROGRAMS['career_counseling'][:2]
            recommendations['priority_programs'].append({
                'category': 'Career Counseling',
                'priority': 'MEDIUM',
                'programs': ENABLEMENT_PROGRAMS['career_counseling'][:2]
            })
            
        else:
            # General support programs
            recommendations['upskilling'] = [ENABLEMENT_PROGRAMS['upskilling'][1]]  # Financial literacy
            recommendations['career_counseling'] = [ENABLEMENT_PROGRAMS['career_counseling'][0]]
            recommendations['priority_programs'].append({
                'category': 'Financial Literacy',
                'priority': 'MEDIUM',
                'programs': [ENABLEMENT_PROGRAMS['upskilling'][1]]
            })
        
        # Generate personalized advice using LLM
        personalized_advice = self._generate_personalized_advice(
            applicant_data, 
            eligibility_result, 
            recommendations
        )
        
        recommendations['personalized_advice'] = personalized_advice
        
        # Create actionable next steps
        recommendations['next_steps'] = self._create_next_steps(recommendations)
        
        result = {
            'action': 'generate_recommendations',
            'success': True,
            'recommendations': recommendations,
            'total_programs': len(recommendations['priority_programs'])
        }
        
        # Log recommendations to Langfuse
        try:
            log_agent_execution(
                agent_name=self.name,
                applicant_id=applicant_id,
                stage='recommendation',
                input_data={
                    'employment_status': employment_status,
                    'monthly_income': monthly_income,
                    'eligibility_result': eligibility_result
                },
                output_data={
                    'recommendations_count': len(recommendations['priority_programs']),
                    'priority_programs': recommendations['priority_programs'],
                    'next_steps': recommendations.get('next_steps', [])
                },
                success=True,
                error=None
            )
        except Exception as e:
            # Langfuse logging should not fail the workflow
            pass
        
        return result
    
    def _generate_personalized_advice(
        self,
        applicant_data: Dict[str, Any],
        eligibility_result: Dict[str, Any],
        recommendations: Dict[str, Any]
    ) -> str:
        """
        Use LLM to generate personalized advice.
        """
        try:
            prompt = f"""
You are a compassionate career counselor for a government social support program.

Applicant Profile:
- Applicant Name: {applicant_data.get('name', 'Unknown')}
- Employment Status: {applicant_data.get('employment_status', 'unknown')}
- Monthly Income: AED {applicant_data.get('monthly_income', 0):,.2f}
- Family Size: {applicant_data.get('family_size', 1)}
- Eligibility Decision: {eligibility_result.get('decision', 'PENDING')}

Recommended Programs:
{self._format_recommendations_for_llm(recommendations)}

Write a personalized, encouraging message (3-4 sentences) that:
1. Acknowledges the applicant's situation
2. Highlights the most relevant programs
3. Motivates them to take action
4. Provides hope and support

Be empathetic and practical.
"""
            
            response = ollama.generate(
                model=settings.ollama_model,
                prompt=prompt
            )
            
            return response['response']
            
        except Exception as e:
            # Fallback message
            return "Based on your profile, we've identified several programs that can help improve your economic situation. We encourage you to explore the upskilling and job matching opportunities available to you. Our team is here to support your journey toward financial stability."
    
    def _format_recommendations_for_llm(self, recommendations: Dict[str, Any]) -> str:
        """Format recommendations for LLM prompt."""
        formatted = []
        
        for program in recommendations.get('priority_programs', []):
            formatted.append(
                f"- {program['category']} (Priority: {program['priority']}): {', '.join(program['programs'])}"
            )
        
        return "\n".join(formatted) if formatted else "General support programs"
    
    def _format_programs(self, programs: List[str]) -> str:
        """Format knowledge base programs."""
        if not programs:
            return "Using standard program catalog"
        
        formatted = []
        for i, program in enumerate(programs, 1):
            formatted.append(f"{i}. {program[:150]}...")
        
        return "\n".join(formatted)
    
    def _create_next_steps(self, recommendations: Dict[str, Any]) -> List[str]:
        """Create actionable next steps for applicant."""
        steps = []
        
        if recommendations['priority_programs']:
            top_priority = recommendations['priority_programs'][0]
            steps.append(
                f"1. Enroll in {top_priority['programs'][0]} - This is your highest priority"
            )
        
        if len(recommendations['priority_programs']) > 1:
            second_priority = recommendations['priority_programs'][1]
            steps.append(
                f"2. Schedule {second_priority['category'].lower()} session"
            )
        
        steps.append("3. Complete your profile in the government job portal")
        steps.append("4. Follow up with your case officer within 2 weeks")
        
        return steps


# Global instance
recommendation_agent = RecommendationAgent()
