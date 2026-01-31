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
from ..database import db_manager, vector_store
from ..utils import log_agent_execution


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
            
            # Store embeddings for semantic search
            if extracted_data.get('raw_text'):
                vector_store.add_document(
                    doc_id=doc_id,
                    text=extracted_data['raw_text'],
                    metadata={
                        'applicant_id': applicant_id,
                        'doc_type': doc_type,
                        'doc_id': doc_id
                    }
                )
            
            result = {
                'action': 'extract_document',
                'success': True,
                'doc_id': doc_id,
                'extracted_data': extracted_data,
                'doc_type': doc_type
            }
            
            # Log extraction to Langfuse
            try:
                log_agent_execution(
                    agent_name=self.name,
                    applicant_id=applicant_id,
                    stage=f'extraction_{doc_type}',
                    input_data={'doc_type': doc_type, 'file_path': file_path},
                    output_data=extracted_data,
                    success=True,
                    error=None
                )
            except Exception as log_err:
                # Langfuse logging should not fail the workflow
                pass
            
            return result
            
        except Exception as e:
            result = {
                'action': 'extract_document',
                'success': False,
                'error': str(e),
                'doc_type': doc_type
            }
            
            # Log extraction failure to Langfuse
            try:
                log_agent_execution(
                    agent_name=self.name,
                    applicant_id=applicant_id,
                    stage=f'extraction_{doc_type}',
                    input_data={'doc_type': doc_type, 'file_path': file_path},
                    output_data=None,
                    success=False,
                    error=str(e)
                )
            except Exception as log_err:
                pass
            
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
        """Extract data from resume PDF/DOCX."""
        if file_path.endswith('.pdf'):
            text = self._extract_pdf_text(file_path)
        elif file_path.endswith('.docx'):
            text = self._extract_docx_text(file_path)
        else:
            text = ""
        
        # Simple keyword-based employment detection
        employment_keywords = ['employed', 'working', 'current position', 'job']
        unemployed_keywords = ['unemployed', 'seeking', 'looking for']
        
        is_employed = any(keyword in text.lower() for keyword in employment_keywords)
        is_unemployed = any(keyword in text.lower() for keyword in unemployed_keywords)
        
        if is_employed:
            employment_status = 'employed'
        elif is_unemployed:
            employment_status = 'unemployed'
        else:
            employment_status = 'unknown'
        
        return {
            'raw_text': text,
            'employment_status': employment_status,
            'text_length': len(text),
            'summary': f'Resume processed, status: {employment_status}'
        }
    
    def _extract_assets_liabilities(self, file_path: str) -> Dict[str, Any]:
        """Extract data from assets/liabilities Excel file."""
        try:
            df = pd.read_excel(file_path)
            
            # Assume standard format with 'Asset', 'Liability', 'Amount' columns
            total_assets = 0.0
            total_liabilities = 0.0
            
            # Try to identify asset and liability rows
            if 'Type' in df.columns and 'Amount' in df.columns:
                assets_df = df[df['Type'].str.lower().str.contains('asset', na=False)]
                liabilities_df = df[df['Type'].str.lower().str.contains('liability', na=False)]
                
                total_assets = assets_df['Amount'].sum()
                total_liabilities = liabilities_df['Amount'].sum()
            else:
                # Fallback: assume first column is assets, second is liabilities
                if len(df.columns) >= 2:
                    total_assets = df.iloc[:, 0].sum()
                    total_liabilities = df.iloc[:, 1].sum()
            
            # Calculate ratio
            asset_liability_ratio = total_assets / total_liabilities if total_liabilities > 0 else float('inf')
            net_worth = total_assets - total_liabilities
            
            return {
                'raw_text': df.to_string(),
                'total_assets': float(total_assets),
                'total_liabilities': float(total_liabilities),
                'net_worth': float(net_worth),
                'asset_liability_ratio': float(asset_liability_ratio),
                'summary': f'Assets: AED {total_assets:,.2f}, Liabilities: AED {total_liabilities:,.2f}'
            }
            
        except Exception as e:
            return {
                'raw_text': '',
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
