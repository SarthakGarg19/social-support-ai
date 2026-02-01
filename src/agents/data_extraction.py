"""
Data Extraction Agent

This agent is responsible for extracting information from various document types:
- Bank statements (PDF)
- Emirates ID (Image + OCR)
- Resume (PDF/DOCX)
- Assets/Liabilities (Excel)
- Credit reports (PDF)

Uses ReAct pattern for intelligent document processing.
"""

from typing import Dict, Any, List
import PyPDF2
import pdfplumber
from docx import Document
import pandas as pd
from pathlib import Path
import re

from .base_agent import BaseAgent, AgentState, AgentResponse
from ..database import db_manager

class DataExtractionAgent(BaseAgent):
    """
    Agent specialized in extracting structured data from multimodal documents.
    
    Capabilities:
    - PDF text extraction
    - Excel data parsing
    - Document classification
    - Key information extraction
    
    Reasoning: Determines which extraction method to use based on document type
    Action: Extracts relevant data fields
    Observation: Validates extraction completeness
    """
    
    def __init__(self):
        super().__init__(
            name="DataExtractionAgent",
            description="Extracts structured information from uploaded documents"
        )
    
    def reason(self, state: AgentState) -> str:
        """
        Determine extraction strategy based on document type.
        
        ReAct Reasoning:
        - Analyze document type
        - Select appropriate extraction method
        - Identify key fields to extract
        """
        doc_type = state.context.get('doc_type', 'unknown')
        file_path = state.context.get('file_path', '')
        
        reasoning = f"""
        Document Analysis:
        - Type: {doc_type}
        - Path: {file_path}
        
        Extraction Strategy:
        """
        
        if doc_type == 'bank_statement':
            reasoning += """
            - Extract transaction history
            - Calculate average monthly income
            - Identify recurring expenses
            - Extract account balance
            """
        elif doc_type == 'emirates_id':
            reasoning += """
            - Extract ID number
            - Extract name
            - Extract date of birth
            - Extract expiry date
            """
        elif doc_type == 'resume':
            reasoning += """
            - Extract employment history
            - Identify current/recent positions
            - Extract skills and qualifications
            - Determine employment status
            """
        elif doc_type == 'assets_liabilities':
            reasoning += """
            - Parse Excel structure
            - Extract asset values
            - Extract liability amounts
            - Calculate net worth
            - Calculate asset-to-liability ratio
            """
        elif doc_type == 'credit_report':
            reasoning += """
            - Extract credit score
            - Identify outstanding loans
            - Check payment history
            - Analyze credit utilization
            """
        else:
            reasoning += "- Generic text extraction for unknown type"
        
        return reasoning
    
    def act(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute document extraction based on reasoning.
        
        ReAct Action:
        - Apply selected extraction method
        - Parse and structure data
        - Store results
        """
        doc_type = state.context.get('doc_type')
        file_path = state.context.get('file_path')
        applicant_id = state.context.get('applicant_id')
        
        try:
            # Route to appropriate extraction method
            if doc_type == 'bank_statement':
                extracted_data = self._extract_bank_statement(file_path)
            elif doc_type == 'emirates_id':
                extracted_data = self._extract_emirates_id(file_path)
            elif doc_type == 'resume':
                extracted_data = self._extract_resume(file_path)
            elif doc_type == 'assets_liabilities':
                extracted_data = self._extract_assets_liabilities(file_path)
            elif doc_type == 'credit_report':
                extracted_data = self._extract_credit_report(file_path)
            else:
                extracted_data = self._extract_generic(file_path)
            
            # Store document in database
            doc_id = db_manager.save_document({
                'applicant_id': applicant_id,
                'doc_type': doc_type,
                'file_path': file_path,
                'extracted_data': extracted_data,
                'validation_status': 'pending'
            })
            
            
            result = {
                'action': 'extract_document',
                'success': True,
                'doc_id': doc_id,
                'extracted_data': extracted_data,
                'doc_type': doc_type
            }
            return result
        
        except Exception as e:
            result = {
                'action': 'extract_document',
                'success': False,
                'error': str(e),
                'doc_type': doc_type
            }
            return result
    
    def _extract_bank_statement(self, file_path: str) -> Dict[str, Any]:
        """Extract data from bank statement PDF.
        
        Extracts:
        - Salary deposits with amounts
        - Freelance income with amounts
        - Monthly income calculation
        - Transaction details with dates and balances
        
        Pattern: Date Description +/-Amount Balance
        Example: 05-Jan-2026 Salary Deposit +11,000.00 56,000.00
        """
        text = self._extract_pdf_text(file_path)
        
        # Initialize tracking
        salary_deposits = []
        freelance_income = []
        all_transactions = []
        
        # Split text into lines for better pattern matching
        lines = text.split('\n')
        
        # Primary pattern: Date Description +/-Amount Balance
        # Matches: 05-Jan-2026 Salary Deposit +11,000.00 56,000.00
        transaction_pattern = r'(\d{2}-\w+-\d{4})\s+(.+?)\s+([+-][\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
        
        for line in lines:
            # Try to match transaction line with primary pattern
            match = re.search(transaction_pattern, line)
            if match:
                date = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3)
                balance_str = match.group(4)
                
                try:
                    # Extract amount (remove +/- prefix and commas)
                    amount = float(amount_str.replace('+', '').replace(',', ''))
                    balance = float(balance_str.replace(',', ''))
                    
                    # Only track positive amounts (income)
                    if amount > 0:
                        transaction = {
                            'date': date,
                            'description': description,
                            'amount': amount,
                            'balance': balance
                        }
                        all_transactions.append(transaction)
                        
                        # Check if it's salary deposit
                        desc_lower = description.lower()
                        if any(kw in desc_lower for kw in ['salary', 'salary deposit', 'payroll', 'monthly salary', 'salary payment']):
                            salary_deposits.append(amount)
                        
                        # Check if it's freelance income
                        elif any(kw in desc_lower for kw in ['freelance', 'freelance income', 'contract', 'freelance payment', 'project']):
                            freelance_income.append(amount)
                
                except ValueError:
                    # Skip lines that can't be parsed as numbers
                    continue
        
        # Calculate totals
        total_salary = sum(salary_deposits) if salary_deposits else 0.0
        total_freelance = sum(freelance_income) if freelance_income else 0.0
        total_income = total_salary + total_freelance
        
        return {
            'raw_text': text,
            'monthly_income': float(total_income),
            'salary_deposits': float(total_salary),
            'salary_deposit_count': len(salary_deposits),
            'salary_deposit_list': salary_deposits,
            'freelance_income': float(total_freelance),
            'freelance_income_count': len(freelance_income),
            'freelance_income_list': freelance_income,
            'total_transactions': len(all_transactions),
            'transactions': all_transactions[:15],  # Return first 15 transactions
            'summary': f'Salary: AED {total_salary:,.2f} ({len(salary_deposits)} deposits), '
                      f'Freelance: AED {total_freelance:,.2f} ({len(freelance_income)} income), '
                      f'Total Monthly Income: AED {total_income:,.2f}'
        }
    
    def _extract_emirates_id(self, file_path: str) -> Dict[str, Any]:
        """Extract data from Emirates ID image."""
        # In production, use OCR (pytesseract) or vision LLM
        # For prototype, return mock data
        
        return {
            'raw_text': 'Emirates ID Document',
            'id_number': '784-XXXX-XXXXXXX-X',
            'name': 'Sample Applicant',
            'summary': 'Emirates ID information extracted'
        }
    
    def _extract_resume(self, file_path: str) -> Dict[str, Any]:
        """Extract data from resume PDF/DOCX using LLM for employment status and job details."""
        if file_path.endswith('.pdf'):
            text = self._extract_pdf_text(file_path)
        elif file_path.endswith('.docx'):
            text = self._extract_docx_text(file_path)
        else:
            text = ""

        llm_result = self._llm_validate(text)
        employment_status = llm_result.get('employment_status', 'unknown')
        current_job_title = llm_result.get('current_job_title')
        current_employer = llm_result.get('current_employer')
        current_job_period = llm_result.get('current_job_period')
        summary = f"Resume processed, status: {employment_status}"
        if current_job_title:
            summary += f" | Current Job: {current_job_title}"
        if current_employer:
            summary += f" at {current_employer}"
        if current_job_period:
            summary += f" ({current_job_period})"
        if 'reasoning' in llm_result:
            summary += f" | Reasoning: {llm_result['reasoning']}"
        if 'llm_error' in llm_result:
            summary += f" | LLM error: {llm_result['llm_error']}"

        return {
            'raw_text': text,
            'employment_status': employment_status,
            'current_job_title': current_job_title,
            'current_employer': current_employer,
            'current_job_period': current_job_period,
            'text_length': len(text),
            'summary': summary
        }

    def _llm_validate(self, resume_text: str) -> dict:
        """
        Use local LLM to extract employment status and job details from resume text.
        Returns a dict with keys: employment_status, current_job_title, current_employer, current_job_period.
        """
        try:
            import ollama
            from ..config import settings
            prompt = f"""
You are an expert resume parser. Given the following resume text, extract the following fields as JSON:
- employment_status: 'employed' or 'unemployed'
- current_job_title: (if employed, the most recent/current job title, else null)
- current_employer: (if employed, the most recent/current employer, else null)
- current_job_period: (if employed, the period for the current job, else null)
- reasoning: brief explanation of how you determined the employment status

Resume text:
{resume_text}

Respond ONLY with a JSON object.
"""
            response = ollama.generate(
                model=settings.ollama_model,
                prompt=prompt
            )
            import json
            return json.loads(response['response'])
        except Exception as e:
            return {
                'employment_status': 'unknown',
                'current_job_title': None,
                'current_employer': None,
                'current_job_period': None,
                'llm_error': str(e)
            }

    def _extract_assets_liabilities(self, file_path: str) -> Dict[str, Any]:
        """Extract data from assets/liabilities Excel file (custom row-label format).
        Handles files where assets and liabilities are row labels, not columns.
        """
        try:
            df = pd.read_excel(file_path, header=None)
            raw_text = df.to_string()
            total_assets = 0.0
            total_liabilities = 0.0
            net_worth = None
            asset_liability_ratio = None
            assets = {}
            liabilities = {}
            # Find section indices
            assets_start = liabilities_start = assets_end = liabilities_end = None

            for i, row in df.iterrows():
                label = str(row[0]).strip().upper() if pd.notnull(row[0]) else ""
                if label == "ASSETS":
                    assets_start = i + 1
                elif label == "LIABILITIES":
                    liabilities_start = i + 1
                elif label.startswith("TOTAL ASSET"):
                    assets_end = i
                elif label.startswith("TOTAL LIABILIT"):
                    liabilities_end = i
                elif label == "NET WORTH":
                    try:
                        net_worth = float(row[1])
                    except Exception:
                        pass
                elif label.startswith("ASSET-LIABILITY"):
                    try:
                        asset_liability_ratio = float(row[1])
                    except Exception:
                        pass
            # Extract assets
            if assets_start is not None and assets_end is not None:
                for i in range(assets_start, assets_end):
                    label = str(df.iloc[i, 0]).strip()
                    value = df.iloc[i, 1]
                    if label and pd.notnull(value):
                        try:
                            assets[label] = float(value)
                        except Exception:
                            continue
                total_assets = sum(assets.values())
            # Extract liabilities
            if liabilities_start is not None and liabilities_end is not None:
                for i in range(liabilities_start, liabilities_end):
                    label = str(df.iloc[i, 0]).strip()
                    value = df.iloc[i, 1]
                    if label and pd.notnull(value):
                        try:
                            liabilities[label] = float(value)
                        except Exception:
                            continue
                total_liabilities = sum(liabilities.values())
            # Fallback: try to get totals from TOTAL rows if present
            for i, row in df.iterrows():
                label = str(row[0]).strip().upper() if pd.notnull(row[0]) else ""
                if label.startswith("TOTAL ASSET"):
                    try:
                        total_assets = float(row[1])
                    except Exception:
                        pass
                if label.startswith("TOTAL LIABILIT"):
                    try:
                        total_liabilities = float(row[1])
                    except Exception:
                        pass
            # Calculate net worth and ratio if not found
            if net_worth is None:
                net_worth = total_assets - total_liabilities
            if asset_liability_ratio is None:
                asset_liability_ratio = total_assets / total_liabilities if total_liabilities > 0 else float('inf')
            return {
                'raw_text': raw_text,
                'assets': assets,
                'liabilities': liabilities,
                'total_assets': float(total_assets),
                'total_liabilities': float(total_liabilities),
                'net_worth': float(net_worth),
                'asset_liability_ratio': float(asset_liability_ratio),
                'summary': f'Assets: AED {total_assets:,.2f}, Liabilities: AED {total_liabilities:,.2f}, Net Worth: AED {net_worth:,.2f}, Ratio: {asset_liability_ratio:.2f}'
            }
        except Exception as e:
            return {
                'raw_text': '',
                'assets': {},
                'liabilities': {},
                'total_assets': 0.0,
                'total_liabilities': 0.0,
                'net_worth': 0.0,
                'asset_liability_ratio': 0.0,
                'error': str(e),
                'summary': 'Error parsing Excel file'
            }
    
    def _extract_credit_report(self, file_path: str) -> Dict[str, Any]:
        """Extract data from credit report PDF."""
        text = self._extract_pdf_text(file_path)
        
        # Extract credit score (common patterns)
        credit_score = 0
        score_match = re.search(r'(?:score|rating)[:\s]*(\d{3})', text, re.IGNORECASE)
        if score_match:
            credit_score = int(score_match.group(1))
        else:
            # Default mock score for prototype
            credit_score = 650
        
        return {
            'raw_text': text,
            'credit_score': credit_score,
            'summary': f'Credit score: {credit_score}'
        }
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except Exception:
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    return text
            except Exception:
                return ""
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception:
            return ""
    
    def _extract_generic(self, file_path: str) -> Dict[str, Any]:
        """Generic text extraction for unknown file types."""
        if file_path.endswith('.pdf'):
            text = self._extract_pdf_text(file_path)
        elif file_path.endswith('.docx'):
            text = self._extract_docx_text(file_path)
        else:
            text = ""
        
        return {
            'raw_text': text,
            'summary': 'Generic text extraction completed'
        }


# Global instance
data_extraction_agent = DataExtractionAgent()
