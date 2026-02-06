# Social Support AI Application

**AI-Powered Workflow Automation for Government Social Security Assessment**

This application automates the social support application process using **Agentic AI with LangGraph orchestration**, reducing processing time from 5-20 days to minutes with 99% automation.

---

## 🎯 Overview

A multi-agent AI system that:
- **Extracts** data from multimodal documents (PDF, Excel, images)
- **Validates** data for consistency and completeness
- **Assesses** eligibility for social support
- **Recommends** personalized economic enablement programs
- **Decides** with LLM-powered reasoning

### Key Features

✅ **Local LLM** - Uses Ollama for privacy and control  
✅ **Multi-Agent System** - 5 specialized agents with ReAct pattern  
✅ **LangGraph Orchestration** - Stateful workflow management  
✅ **Multimodal Processing** - Text, images, and tabular data  
✅ **Persistent Storage** - SQLite for structured data  

---

## 🏗️ Architecture

### Agent System (ReAct Pattern)

```
┌─────────────────────────────────────────────────────────┐
│              MASTER ORCHESTRATOR (LangGraph)            │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌────────────┐   │
│  │   Data      │ ─→ │    Data     │ ─→ │ Eligibility│   │
│  │ Extraction  │    │ Validation  │    │   Check    │   │
│  └─────────────┘    └─────────────┘    └────────────┘   │
│                                             │           │
│                                             ↓           │
│                                      ┌────────────────┐ │
│                                      │Recommendation  │ │
│                                      │    Agent       │ │
│                                      └────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11+ | Core development |
| **LLM** | Ollama (llama3.2) | Local language model |
| **Orchestration** | LangGraph | Multi-agent workflow |
| **Relational DB** | SQLite | Structured data |
| **Document Processing** | PyPDF2, pdfplumber, openpyxl | Data extraction |
| **ML** | scikit-learn | Classification |
| **Observability** | Langfuse (optional) | Agent tracing |

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **Ollama** installed and running with llama3.2 model
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3.2
   ollama serve
   ```

### Installation

#### Option 1: Automated Setup (Windows)

```bash
setup.bat
```

#### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env if needed
```

### Running the Demo

```bash
# Make sure Ollama is running!
ollama serve

# Run the demo
python demo.py
```

The demo will:
1. Create a sample applicant
2. Process mock documents through all agents
3. Show the LangGraph workflow in action
4. Display the final decision and recommendations

---

## 📁 Project Structure

```
social-support-ai/
├── src/
│   ├── agents/               # 🤖 AI Agents (ReAct pattern)
│   │   ├── base_agent.py     # Base agent with ReAct implementation
│   │   ├── orchestrator.py   # Master orchestrator (LangGraph)
│   │   ├── data_extraction.py
│   │   ├── data_validation.py
│   │   ├── eligibility_check.py
│   │   └── recommendation.py
│   ├── database/             # 💾 Data storage
│   │   └── sqlite_db.py      # SQLite manager
│   └── config.py             # Configuration
├── data/                     # Data storage
│   ├── uploads/              # Uploaded documents
│   ├── synthetic/            # Sample data
│   └── chroma_db/            # Vector embeddings
├── docs/                     # Documentation
├── requirements.txt          # Dependencies
├── setup.bat                 # Setup script
├── demo.py                   # Demo application
└── README.md                 # This file
```

---

## 🤖 Agent Architecture Explained

### 1. **Data Extraction Agent**

**Purpose:** Extracts structured information from multimodal documents

**ReAct Pattern:**
- **Reason:** Analyzes document type and selects extraction method
- **Act:** Applies appropriate parser (PDF, Excel, OCR)
- **Observe:** Validates extraction completeness

**Capabilities:**
- Bank statement parsing (income calculation)
- Emirates ID OCR
- Resume analysis (employment status)
- Excel financial data extraction
- Credit report parsing

### 2. **Data Validation Agent**

**Purpose:** Ensures data quality and cross-document consistency

**ReAct Pattern:**
- **Reason:** Identifies validation rules and completeness requirements
- **Act:** Cross-references data, checks ranges, uses LLM for semantic validation
- **Observe:** Reports issues and warnings

**Features:**
- Completeness scoring
- Range validation
- LLM-powered semantic validation
- Cross-document consistency checks

### 3. **Eligibility Check Agent**

**Purpose:** Determines social support eligibility

**ReAct Pattern:**
- **Reason:** Analyzes financial profile against eligibility criteria
- **Act:** Calculates multi-factor score, queries knowledge base
- **Observe:** Generates LLM explanation

**Criteria:**
- Income threshold (30 points)
- Employment status (20 points)
- Family size (20 points)
- Financial need (20 points)
- Credit score (10 points)

**Decision Thresholds:**
- 80-100: APPROVED (High confidence)
- 70-80: APPROVED (Medium confidence)
- 60-70: UNDER_REVIEW
- 0-60: DECLINED

### 4. **Recommendation Agent**

**Purpose:** Provides personalized economic enablement programs

**ReAct Pattern:**
- **Reason:** Assesses needs based on employment and financial situation
- **Act:** Matches to programs, prioritizes, generates LLM advice
- **Observe:** Creates actionable next steps

**Programs:**
- Upskilling (Digital Skills, Financial Literacy, Vocational Training)
- Job Matching (Government Portal, Job Fairs, Freelance Platform)
- Career Counseling (Resume Building, Interview Prep)

### 5. **Master Orchestrator (LangGraph)**

**Purpose:** Coordinates all agents in a stateful workflow

**LangGraph Workflow:**
```python
START 
  ↓
extract_documents 
  ↓
validate_data 
  ↓ (conditional: check completeness)
check_eligibility 
  ↓
generate_recommendations 
  ↓
finalize 
  ↓
END
```

**Key Features:**
- State management across workflow
- Conditional branching
- Error handling and recovery
- Workflow observability

---

## 🔬 Key Technical Highlights

### 1. ReAct Pattern Implementation

Each agent implements **Reasoning and Acting**:

```python
class BaseAgent(ABC):
    def reason(self, state) -> str:
        """Analyze state and determine what to do"""
        
    def act(self, state) -> Dict:
        """Execute the determined action"""
        
    def observe(self, state, result) -> str:
        """Process and record results"""
```

### 2. LangGraph Orchestration

**Why LangGraph?**
- Stateful workflow management
- Conditional branching
- Built-in error handling
- Agent coordination

```python
workflow = StateGraph(WorkflowState)
workflow.add_node("extract_documents", extract_func)
workflow.add_conditional_edges("validate_data", should_proceed)
workflow = workflow.compile()
```

### 3. Local LLM Integration

**Benefits:**
- Privacy (no data leaves local system)
- No API costs
- Full control over model
- Works offline

```python
response = ollama.generate(
    model="llama3.2",
    prompt=reasoning_prompt
)
```

### 4. Hybrid Storage

**SQLite:** Structured data (applicants, assessments)  
**ChromaDB:** Vector embeddings for semantic search  
**File System:** Original documents

---

## 📊 Sample Output

```
============================================================
ORCHESTRATOR: Processing application APP_20260127001
============================================================

[ORCHESTRATOR] Stage 1: Extracting documents
  ✓ Extracted bank_statement: avg income: AED 8,500.00
  ✓ Extracted resume: Status - unemployed
  ✓ Extracted assets_liabilities: Assets: AED 50,000, Liabilities: AED 120,000

[ORCHESTRATOR] Stage 2: Validating data
  Completeness: 80%
  Valid: True
  
[ORCHESTRATOR] Stage 3: Checking eligibility
  Score: 78.5/100
  Decision: APPROVED
  Confidence: HIGH
  
[ORCHESTRATOR] Stage 4: Generating recommendations
  Total programs: 2
  - Job Matching (HIGH priority)
  - Upskilling (MEDIUM priority)
  
[ORCHESTRATOR] Stage 5: Finalizing decision
  ✓ Assessment saved: ASS_20260127001
  Final Decision: APPROVED

============================================================
WORKFLOW COMPLETE
============================================================
```

---

## 🎓 For the Interview/Demo

### Key Points to Highlight

1. **Agentic AI Architecture**
   - 5 specialized agents with clear responsibilities
   - ReAct pattern for reasoning
   - LangGraph for orchestration

2. **Technical Sophistication**
   - Local LLM integration (Ollama)
   - Multimodal data processing
   - Stateful workflow management

3. **Practical Benefits**
   - 5-20 days → Minutes
   - 99% automation target
   - Consistent decision-making
   - Audit trail and explainability

4. **Scalability Considerations**
   - Modular agent design
   - Database-agnostic architecture
   - Easy to add new agents
   - Production-ready patterns

---

## 🔧 Troubleshooting

### Ollama not running
```bash
# Start Ollama
ollama serve

# Verify model is available
ollama list
ollama pull llama3.2
```

### ImportError with dependencies
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### ChromaDB permission errors
```bash
# Clear ChromaDB data
rm -rf data/chroma_db
# Restart application
```

---

## 📝 Future Enhancements

- [ ] FastAPI REST API
- [ ] ML classifier for eligibility scoring
- [ ] Real OCR for Emirates ID
- [ ] Production database (PostgreSQL)
- [ ] Kubernetes deployment
- [ ] API authentication

---

## 📄 License

This is a prototype for the DGE Assessment.

---

## 👤 Author

**Assignment Submission for Digital Government Excellence Role**

Focus: Agentic AI Architecture with LangGraph Orchestration
