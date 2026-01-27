"""
Social Support AI - Demo Application

This script demonstrates the complete agentic AI workflow:
1. Data Extraction Agent
2. Data Validation Agent
3. Eligibility Check Agent
4. Recommendation Agent
5. Master Orchestrator (LangGraph)

Run this to see the multi-agent system in action!
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.agents import orchestrator
from src.database import db_manager
from src.config import settings

# Create sample data directory
settings.ensure_directories()


def create_sample_documents():
    """
    Create sample documents for demonstration.
    In a real system, these would be actual uploaded files.
    """
    data_dir = Path("data/synthetic")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample bank statement (simple text file simulating PDF)
    bank_statement = data_dir / "bank_statement_sample.txt"
    bank_statement.write_text("""
    BANK STATEMENT
    Account Holder: Ahmed Al-Mansouri
    Period: January 2026
    
    Transactions:
    01/01/2026    Salary Credit         AED 8,500.00
    05/01/2026    Rent Payment         -AED 2,500.00
    10/01/2026    Groceries            -AED 600.00
    15/01/2026    Utilities            -AED 300.00
    20/01/2026    School Fees          -AED 1,200.00
    
    Closing Balance: AED 3,900.00
    Average Income: AED 8,500.00
    """)
    
    # Sample resume
    resume = data_dir / "resume_sample.txt"
    resume.write_text("""
    RESUME
    Name: Ahmed Al-Mansouri
    
    WORK EXPERIENCE:
    Currently seeking employment
    Previous: Sales Associate at RetailCo (2020-2023)
    
    EDUCATION:
    Bachelor's in Business Administration
    
    SKILLS:
    - Customer Service
    - Sales
    - Team Leadership
    """)
    
    # Sample assets/liabilities (simple text simulating Excel)
    assets = data_dir / "assets_liabilities.txt"
    assets.write_text("""
    FINANCIAL STATEMENT
    
    ASSETS:
    Savings Account: AED 30,000
    Vehicle: AED 20,000
    Total Assets: AED 50,000
    
    LIABILITIES:
    Personal Loan: AED 80,000
    Credit Card: AED 15,000
    Car Loan: AED 25,000
    Total Liabilities: AED 120,000
    
    Net Worth: -AED 70,000
    Asset/Liability Ratio: 0.42
    """)
    
    # Sample credit report
    credit_report = data_dir / "credit_report.txt"
    credit_report.write_text("""
    CREDIT REPORT
    Name: Ahmed Al-Mansouri
    
    Credit Score: 620
    Credit Rating: Fair
    
    Payment History: Some late payments
    Total Debt: AED 120,000
    Credit Utilization: 75%
    """)
    
    return {
        'bank_statement': str(bank_statement),
        'resume': str(resume),
        'assets_liabilities': str(assets),
        'credit_report': str(credit_report)
    }


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_section(title):
    """Print a section header."""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")


def run_demo():
    """Run the complete demo workflow."""
    
    print_header("🤖 SOCIAL SUPPORT AI - AGENTIC WORKFLOW DEMO")
    
    print("This demo showcases a multi-agent AI system that automates")
    print("social support applications using:")
    print("  • ReAct Pattern (Reasoning and Acting)")
    print("  • LangGraph Orchestration")
    print("  • Local LLM (Ollama)")
    print("  • Vector Search (ChromaDB)")
    print("  • SQLite Database")
    
    print("\n⚠️  NOTE: Make sure Ollama is running with llama3.2 model!")
    print("   Run: ollama serve (in another terminal)\n")
    
    input("Press Enter to start the demo...")
    
    # Step 1: Create sample documents
    print_section("📄 Step 1: Creating Sample Documents")
    
    doc_paths = create_sample_documents()
    print("✓ Created sample documents:")
    for doc_type, path in doc_paths.items():
        print(f"  • {doc_type}: {path}")
    
    # Step 2: Create applicant
    print_section("👤 Step 2: Creating Sample Applicant")
    
    applicant_id = f"APP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    applicant_data = {
        'id': applicant_id,
        'name': 'Ahmed Al-Mansouri',
        'emirates_id': '784-XXXX-XXXXXXX-X',
        'family_size': 4,  # Spouse + 2 children
        'employment_status': 'unemployed',
        'monthly_income': 0,  # Will be extracted from documents
        'contact_info': {
            'email': 'ahmed.almansouri@example.com',
            'phone': '+971-XX-XXX-XXXX'
        }
    }
    
    # Save to database
    db_manager.create_applicant(applicant_data)
    
    print(f"✓ Created applicant: {applicant_data['name']}")
    print(f"  ID: {applicant_id}")
    print(f"  Family Size: {applicant_data['family_size']}")
    print(f"  Status: {applicant_data['employment_status']}")
    
    # Step 3: Prepare documents for processing
    print_section("📋 Step 3: Preparing Documents for Processing")
    
    documents = [
        {'type': 'bank_statement', 'path': doc_paths['bank_statement']},
        {'type': 'resume', 'path': doc_paths['resume']},
        {'type': 'assets_liabilities', 'path': doc_paths['assets_liabilities']},
        {'type': 'credit_report', 'path': doc_paths['credit_report']}
    ]
    
    print(f"✓ Prepared {len(documents)} documents for processing")
    
    # Step 4: Run the orchestrator
    print_section("🚀 Step 4: Initiating LangGraph Workflow")
    
    print("\nThe Master Orchestrator will now coordinate all agents:")
    print("  1. Data Extraction Agent → Extract from documents")
    print("  2. Data Validation Agent → Validate completeness")
    print("  3. Eligibility Check Agent → Calculate score")
    print("  4. Recommendation Agent → Generate programs")
    print("  5. Finalize → Store results\n")
    
    input("Press Enter to start the workflow...")
    
    # Process application through orchestrator
    final_decision = orchestrator.process_application(
        applicant_id=applicant_id,
        applicant_data=applicant_data,
        documents=documents
    )
    
    # Step 5: Display results
    print_section("📊 Step 5: Final Results")
    
    print(f"\n✅ Application Processing Complete!")
    print(f"\nApplicant: {applicant_data['name']}")
    print(f"Application ID: {applicant_id}")
    print(f"\n{'─'*50}")
    print(f"DECISION: {final_decision.get('decision', 'UNKNOWN')}")
    print(f"ELIGIBILITY SCORE: {final_decision.get('eligibility_score', 0):.1f}/100")
    print(f"{'─'*50}")
    
    if final_decision.get('reasoning'):
        print(f"\nExplanation:")
        print(f"  {final_decision['reasoning']}")
    
    # Display recommendations
    recommendations = final_decision.get('recommendations', {})
    if recommendations.get('priority_programs'):
        print(f"\n📚 Recommended Programs:")
        for program in recommendations['priority_programs']:
            print(f"\n  {program['category']} (Priority: {program['priority']})")
            for prog_name in program['programs']:
                print(f"    • {prog_name}")
    
    if recommendations.get('next_steps'):
        print(f"\n🎯 Next Steps:")
        for step in recommendations['next_steps']:
            print(f"  {step}")
    
    if recommendations.get('personalized_advice'):
        print(f"\n💬 Personalized Advice:")
        print(f"  {recommendations['personalized_advice']}")
    
    # Display any errors
    if final_decision.get('errors'):
        print(f"\n⚠️  Warnings/Issues:")
        for error in final_decision['errors']:
            print(f"  • {error}")
    
    # Step 6: Show data persistence
    print_section("💾 Step 6: Data Persistence")
    
    print("\n✓ Data stored in:")
    print(f"  • SQLite Database: {settings.sqlite_db_path}")
    print(f"  • Vector Store: {settings.chroma_persist_dir}")
    
    # Retrieve and show stored data
    stored_applicant = db_manager.get_applicant(applicant_id)
    stored_assessment = db_manager.get_assessment(applicant_id)
    workflow_state = db_manager.get_workflow_state(applicant_id)
    
    print(f"\n✓ Stored records:")
    print(f"  • Applicant record: {applicant_id}")
    print(f"  • Assessment record: {stored_assessment['id'] if stored_assessment else 'N/A'}")
    print(f"  • Workflow state: {workflow_state['current_stage'] if workflow_state else 'N/A'}")
    
    # Summary
    print_header("🎉 DEMO COMPLETE")
    
    print("This demo showcased:")
    print("  ✓ Agentic AI architecture with ReAct pattern")
    print("  ✓ LangGraph stateful workflow orchestration")
    print("  ✓ Multi-agent coordination")
    print("  ✓ Local LLM integration (Ollama)")
    print("  ✓ Vector search with ChromaDB")
    print("  ✓ Persistent storage with SQLite")
    print("  ✓ End-to-end application processing")
    
    print("\n📖 For more details, see:")
    print("  • README.md - Full documentation")
    print("  • src/agents/ - Agent implementations")
    print("  • src/agents/orchestrator.py - LangGraph workflow")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error running demo: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Make sure Ollama is running: ollama serve")
        print("  2. Ensure llama3.2 model is installed: ollama pull llama3.2")
        print("  3. Check that dependencies are installed: pip install -r requirements.txt")
        print("\nFor more help, see README.md")
        sys.exit(1)
