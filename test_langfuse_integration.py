"""
Test script to verify Langfuse integration is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.utils import init_langfuse, log_agent_execution, log_workflow_state, log_eligibility_decision, flush_langfuse

print("="*70)
print("TESTING LANGFUSE INTEGRATION")
print("="*70)

# Check configuration
print("\n1. Checking Langfuse Configuration:")
print(f"   Public Key configured: {'✓' if settings.langfuse_public_key else '✗'}")
print(f"   Secret Key configured: {'✓' if settings.langfuse_secret_key else '✗'}")
print(f"   Host: {settings.langfuse_host}")

# Initialize Langfuse
print("\n2. Initializing Langfuse client:")
client = init_langfuse()
if client:
    print("   ✓ Langfuse client initialized successfully")
else:
    print("   ✗ Failed to initialize Langfuse client (check API keys in .env)")

# Test logging functions
print("\n3. Testing Langfuse logging functions:")

# Test workflow state logging
print("   Testing log_workflow_state()...")
try:
    log_workflow_state(
        applicant_id="TEST_001",
        workflow_stage="extraction",
        stage_data={"documents_count": 5, "status": "in_progress"}
    )
    print("   ✓ log_workflow_state() called successfully")
except Exception as e:
    print(f"   ✗ log_workflow_state() failed: {e}")

# Test agent execution logging
print("   Testing log_agent_execution()...")
try:
    log_agent_execution(
        agent_name="DataExtractionAgent",
        applicant_id="TEST_001",
        stage="extraction_bank_statement",
        input_data={"doc_type": "bank_statement"},
        output_data={"transactions": 12, "monthly_income": 9700},
        success=True,
        error=None
    )
    print("   ✓ log_agent_execution() called successfully")
except Exception as e:
    print(f"   ✗ log_agent_execution() failed: {e}")

# Test eligibility decision logging
print("   Testing log_eligibility_decision()...")
try:
    log_eligibility_decision(
        applicant_id="TEST_001",
        decision="APPROVED",
        reasoning="Income below threshold, good credit score",
        scores={
            "eligibility_score": 75.5,
            "income_score": "22/30",
            "employment_score": "20/25",
            "confidence": "HIGH"
        }
    )
    print("   ✓ log_eligibility_decision() called successfully")
except Exception as e:
    print(f"   ✗ log_eligibility_decision() failed: {e}")

# Flush traces
print("\n4. Flushing traces to Langfuse cloud:")
try:
    flush_langfuse()
    print("   ✓ Traces flushed successfully")
except Exception as e:
    print(f"   ✗ Failed to flush traces: {e}")

print("\n" + "="*70)
print("LANGFUSE INTEGRATION TEST COMPLETE")
print("="*70)
print("\nNext steps:")
print("1. Visit https://cloud.langfuse.com and log in")
print("2. Check the dashboard for traces from applicant TEST_001")
print("3. Run the Streamlit app with: streamlit run src/ui/streamlit_app.py")
print("4. Process a synthetic applicant to see full workflow traces")
print("\n" + "="*70)
