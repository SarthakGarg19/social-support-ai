"""
Streamlit Chat UI for Social Support AI Application

This provides a user-friendly interface to:
- Chat with the AI assistant
- Upload documents for processing
- View application status and results
- Visualize the workflow
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
import threading
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents import orchestrator
from src.database import db_manager
from src.config import settings
import ollama

# Ensure directories exist
settings.ensure_directories()

# Page config
st.set_page_config(
    page_title="Social Support AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'applicant_id' not in st.session_state:
    st.session_state.applicant_id = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'decision' not in st.session_state:
    st.session_state.decision = None
if 'errors' not in st.session_state:
    st.session_state.errors = None


def chat_with_llm(prompt):
    """Send a message to the local LLM for conversation."""
    try:
        response = ollama.generate(
            model=settings.ollama_model,
            prompt=f"""You are a helpful AI assistant for a government social support application system.
            
User message: {prompt}

Provide a helpful, empathetic response. If the user asks about the application process, explain that they can:
1. Upload required documents (bank statements, resume, Emirates ID, assets/liabilities, credit report)
2. Fill in basic information
3. Click "Process Application" to run the AI assessment

Keep responses brief and friendly."""
        )
        return response['response']
    except Exception as e:
        return f"I'm having trouble connecting to the AI model. Please ensure Ollama is running with the llama3.2 model. Error: {str(e)}"


def process_application_background(applicant_data, documents):
    """Process application in background."""
    try:
        st.session_state.processing = True
        
        # Create applicant in database
        applicant_id = db_manager.create_applicant(applicant_data)
        st.session_state.applicant_id = applicant_id
        
        # Process through orchestrator
        final_decision, errors = orchestrator.process_application(
            applicant_id=applicant_id,
            applicant_data=applicant_data,
            documents=documents
        )
        
        st.session_state.decision = final_decision
        st.session_state.errors = errors
        st.session_state.processing = False
        
    except Exception as e:
        st.session_state.processing = False
        st.session_state.decision = {
            'decision': 'ERROR',
            'error': str(e)
        }
        st.session_state.errors = {
            'errors': 'Not processed due to error',
            'error': str(e)
        }


# Header
st.title("🤖 Social Support AI Assistant")
st.caption("AI-Powered Social Support Application Processing")

# Sidebar for document upload and application form
with st.sidebar:
    st.header("📄 Document Upload")
    
    # Basic Information
    st.subheader("Basic Information")
    name = st.text_input("Full Name", value="Ahmed Al-Mansouri")
    emirates_id = st.text_input("Emirates ID", value="784-XXXX-XXXXXXX-X")
    family_size = st.number_input("Family Size", min_value=1, max_value=20, value=4)
    email = st.text_input("Email", value="applicant@example.com")
    phone = st.text_input("Phone", value="+971-XX-XXX-XXXX")
    
    st.divider()
    
    # Document Upload
    st.subheader("Upload Documents")
    
    bank_statement = st.file_uploader("Bank Statement (PDF/TXT)", type=['pdf', 'txt'])
    resume = st.file_uploader("Resume (PDF/DOCX/TXT)", type=['pdf', 'docx', 'txt'])
    assets_liabilities = st.file_uploader("Assets/Liabilities (Excel/TXT)", type=['xlsx', 'xls', 'txt'])
    credit_report = st.file_uploader("Credit Report (PDF/TXT)", type=['pdf', 'txt'])
    emirates_id_doc = st.file_uploader("Emirates ID (Image/PDF)", type=['pdf', 'jpg', 'png'])
    
    st.divider()
    
    # Process Application Button
    process_btn = st.button("🚀 Process Application", type="primary", disabled=st.session_state.processing, use_container_width=True)
    
    if process_btn:
        # Save uploaded files
        documents = []
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_mappings = {
            'bank_statement': bank_statement,
            'resume': resume,
            'assets_liabilities': assets_liabilities,
            'credit_report': credit_report,
            'emirates_id': emirates_id_doc
        }
        
        for doc_type, uploaded_file in file_mappings.items():
            if uploaded_file:
                # Save file
                file_path = upload_dir / f"{doc_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{uploaded_file.name.split('.')[-1]}"
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                documents.append({
                    'type': doc_type,
                    'path': str(file_path)
                })
        
        if not documents:
            st.error("Please upload at least one document!")
        else:
            # Create applicant data
            applicant_data = {
                'name': name,
                'emirates_id': emirates_id,
                'family_size': family_size,
                'employment_status': 'unknown',  # Will be extracted
                'monthly_income': 0,  # Will be extracted
                'contact_info': {
                    'email': email,
                    'phone': phone
                }
            }
            
            # Start processing in a thread
            with st.spinner("Processing your application... This may take a minute."):
                process_application_background(applicant_data, documents)
            
            st.success("✅ Application submitted! Check the results below.")
            st.rerun()
    
    # Export Stategraph
    st.divider()
    if st.button("📊 Export Workflow Graph", use_container_width=True):
        orchestrator.export_stategraph_mermaid()
        st.success("✅ Workflow graph saved to docs/stategraph.mmd")

# Main chat area
st.header("💬 Chat with AI Assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about the application process..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Check if user wants to process application
    if any(keyword in prompt.lower() for keyword in ['process', 'submit', 'apply', 'check eligibility']):
        response = "I can help you process your application! Please:\n1. Fill in your basic information in the sidebar\n2. Upload the required documents\n3. Click the '🚀 Process Application' button\n\nI'll analyze everything using our AI agents and provide you with a decision and recommendations."
    else:
        # Get response from LLM
        response = chat_with_llm(prompt)
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

# Display application results if available
if st.session_state.decision:
    st.divider()
    st.header("📊 Application Results")
    
    decision = st.session_state.decision
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Decision", decision.get('decision', 'N/A'))
    
    with col2:
        score = decision.get('eligibility_score', 0)
        st.metric("Eligibility Score", f"{score:.1f}/100")
    
    with col3:
        applicant_id = decision.get('applicant_id', st.session_state.applicant_id)
        st.metric("Application ID", applicant_id if applicant_id else "N/A")
    
    # Explanation
    if decision.get('reasoning'):
        st.subheader("📝 Explanation")
        st.info(decision['reasoning'])
    
    # Recommendations
    recommendations = decision.get('recommendations', {})
    if recommendations.get('priority_programs'):
        st.subheader("🎯 Recommended Programs")
        
        for program in recommendations['priority_programs']:
            with st.expander(f"{program['category']} - {program['priority']} Priority"):
                for prog_name in program['programs']:
                    st.write(f"• {prog_name}")
    
    # Personalized Advice
    if recommendations.get('personalized_advice'):
        st.subheader("💡 Personalized Advice")
        st.success(recommendations['personalized_advice'])
    
    # Next Steps
    if recommendations.get('next_steps'):
        st.subheader("✅ Next Steps")
        for step in recommendations['next_steps']:
            st.write(step)
    
    # Errors/Warnings
    if decision.get('errors'):
        st.subheader("⚠️ Warnings")
        for error in decision['errors']:
            st.warning(error)
    
    # Download Results
    st.download_button(
        label="📥 Download Results (JSON)",
        data=json.dumps(decision, indent=2),
        file_name=f"application_results_{applicant_id}.json",
        mime="application/json"
    )

# Display errors if available and non-empty
if st.session_state.errors:
    errors = st.session_state.errors
    # If errors is a dict with 'errors' key as a list or string
    error_list = []
    if isinstance(errors, dict):
        if isinstance(errors.get('errors'), list):
            error_list = errors['errors']
        elif isinstance(errors.get('errors'), str):
            error_list = [errors['errors']]
        else:
            # If errors dict itself is a list
            if isinstance(errors, list):
                error_list = errors
    elif isinstance(errors, list):
        error_list = errors
    # Only display if non-empty
    if error_list:
        st.divider()
        st.header("❌ Application Errors")
        for error in error_list:
            st.error(error)
    # Also show any top-level error string
    if isinstance(errors, dict) and errors.get('error'):
        st.divider()
        st.header("❌ Application Error Detail")
        st.error(errors['error'])

# Processing indicator
if st.session_state.processing:
    with st.spinner("🔄 Processing application through AI agents..."):
        time.sleep(1)  # Small delay to show spinner
        st.rerun()

# Footer
st.divider()
st.caption("Powered by Agentic AI with LangGraph • Local LLM via Ollama • Privacy-First Architecture")
