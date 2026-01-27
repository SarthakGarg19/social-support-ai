# Running the Streamlit Chat UI

## Quick Start

### 1. Start Ollama (Required!)

```bash
# In a separate terminal
ollama serve
```

Make sure llama3.2 model is installed:
```bash
ollama pull llama3.2
```

### 2. Run the Streamlit App

```bash
# Navigate to project directory
cd "c:\Users\Sarthak\OneDrive\Desktop\Resume, Work and Policies\DGE Assignment\social-support-ai"

# Run Streamlit
streamlit run src/ui/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Features

### 🤖 Chat Interface
- Natural language conversation with AI assistant
- Ask questions about the application process
- Get guidance on required documents

### 📄 Document Upload
Upload any combination of:
- **Bank Statement** (PDF/TXT) - For income analysis
- **Resume** (PDF/DOCX/TXT) - For employment status
- **Assets/Liabilities** (Excel/TXT) - For financial position
- **Credit Report** (PDF/TXT) - For credit score
- **Emirates ID** (Image/PDF) - For identity verification

### 🚀 Application Processing
1. Fill in basic information in the sidebar
2. Upload your documents
3. Click "Process Application"
4. Watch the AI agents work in real-time
5. View results with explanation and recommendations

### 📊 Results Display
- **Decision**: APPROVED / UNDER_REVIEW / DECLINED
- **Eligibility Score**: 0-100 with breakdown
- **Recommendations**: Personalized program suggestions
- **Next Steps**: Actionable items
- **Download**: JSON file with complete results

### 📈 Workflow Visualization
- Click "Export Workflow Graph" to save the LangGraph workflow
- File saved to: `docs/stategraph.mmd`
- Can be visualized using Mermaid tools

---

## Workflow Behind the Scenes

When you click "Process Application", the following happens:

```
START
  ↓
1. Data Extraction Agent
   - Extracts text from PDFs
   - Parses Excel files
   - OCR for images
   ↓
2. Data Validation Agent
   - Checks completeness (80%+ required)
   - Validates ranges
   - LLM semantic validation
   ↓
3. Eligibility Check Agent
   - Multi-factor scoring (100 points)
   - Income, employment, family, assets, credit
   - LLM generates explanation
   ↓
4. Recommendation Agent
   - Matches to programs (job matching, upskilling, counseling)
   - Prioritizes based on need
   - LLM generates personalized advice
   ↓
5. Finalize
   - Saves to database
   - Returns final decision
   ↓
END
```

---

## Sample Test Case

Use the demo data generator or create your own:

**Basic Info:**
- Name: Ahmed Al-Mansouri
- Emirates ID: 784-XXXX-XXXXXXX-X
- Family Size: 4
- Email: applicant@example.com

**Create Sample Documents:**
```bash
python -c "from demo import create_sample_documents; create_sample_documents()"
```

Then upload the files from `data/synthetic/` folder.

---

## Troubleshooting

### Ollama Not Running
**Error:** "I'm having trouble connecting to the AI model"

**Solution:**
```bash
ollama serve
ollama pull llama3.2
```

### Import Errors
**Error:** "ModuleNotFoundError: No module named 'X'"

**Solution:**
```bash
pip install chromadb langchain langgraph ollama pdfplumber PyPDF2 python-docx pandas openpyxl streamlit python-dotenv
```

### Streamlit Not Found
**Solution:**
```bash
pip install streamlit
```

### Database Errors
The app automatically creates SQLite and ChromaDB databases on first run.

If you see issues:
```bash
# Clear databases
rm -rf data/social_support.db data/chroma_db/
```

---

## Advanced: Visualizing the Workflow Graph

After exporting the stategraph, you can visualize it:

**Option 1: Online Mermaid Editor**
1. Go to https://mermaid.live
2. Paste contents of `docs/stategraph.mmd`
3. View and export as PNG

**Option 2: VS Code Extension**
1. Install "Markdown Preview Mermaid Support" extension
2. Open `docs/stategraph.mmd`
3. Preview in VS Code

**Option 3: CLI (if mermaid-cli installed)**
```bash
mmdc -i docs/stategraph.mmd -o docs/stategraph.png
```

---

## Architecture Highlights

- **Local LLM**: All processing happens on your machine (Ollama)
- **Privacy-First**: No data sent to external APIs
- **ReAct Pattern**: Each agent reasons before acting
- **LangGraph**: Stateful workflow orchestration
- **Vector Search**: ChromaDB for semantic document search
- **Persistent Storage**: SQLite for structured data

---

## Next Steps After Approval

1. **Review Results**: Check the decision and reasoning
2. **View Recommendations**: See personalized programs
3. **Download JSON**: Keep record of the assessment
4. **Follow Next Steps**: Complete enrollment in recommended programs
5. **Contact Support**: If decision needs clarification

---

## Demo vs Production

**Current Demo Features:**
- Simplified document parsing (regex-based)
- Mock OCR for Emirates ID
- Local-only deployment
- SQLite database

**Production Enhancements:**
- Advanced NLP/LLM extraction
- Real OCR with pytesseract/vision models
- PostgreSQL database
- API authentication
- Multi-tenancy support
- Langfuse observability
- Kubernetes deployment

---

Enjoy the Social Support AI Assistant! 🤖
