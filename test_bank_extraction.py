"""
Test script to extract bank statement data from PDF.
This helps debug and refine the extraction logic before integrating into data_extraction.py
"""

import pdfplumber
import re
from pathlib import Path
from typing import Dict, Any, List


def extract_bank_statement_debug(file_path: str) -> Dict[str, Any]:
    """
    Extract and analyze bank statement PDF with detailed debugging.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print(f"{'='*60}\n")
    
    # Extract raw text
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}\n")
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                text += page_text + "\n"
                print(f"--- Page {page_num + 1} ---")
                print(page_text[:500])  # Print first 500 chars
                print()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return {}
    
    print(f"\n{'='*60}")
    print("FULL TEXT:")
    print(f"{'='*60}\n")
    print(text)
    
    # Initialize tracking
    salary_deposits = []
    freelance_income = []
    all_transactions = []
    
    print(f"\n{'='*60}")
    print("TRANSACTION EXTRACTION:")
    print(f"{'='*60}\n")
    
    # Split text into lines for better pattern matching
    lines = text.split('\n')
    
    # Multiple patterns to try for transaction matching
    patterns = [
        # Pattern 1: Date Description +/-Amount Balance
        r'(\d{2}-\w+-\d{4})\s+(.+?)\s+([+-][\d,]+\.?\d*)\s+([\d,]+\.?\d*)',
        # Pattern 2: Date Description +/-Amount  
        r'(\d{2}-\w+-\d{4})\s+(.+?)\s+([+-][\d,]+\.?\d*)',
        # Pattern 3: Simple amount with AED
        r'AED\s+([+-]?[\d,]+\.?\d*)',
    ]
    
    for line_num, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            continue
        
        # Try each pattern
        matched = False
        for pattern_num, pattern in enumerate(patterns):
            matches = re.findall(pattern, line)
            if matches:
                print(f"Line {line_num}: {line[:80]}")
                print(f"  ✓ Pattern {pattern_num + 1} matched: {matches}")
                
                # Process matches
                for match in matches:
                    if pattern_num == 0:  # Date Description +/-Amount Balance
                        date, description, amount, balance = match
                        amount_val = float(amount.replace('+', '').replace(',', ''))
                        
                        transaction = {
                            'date': date,
                            'description': description.strip(),
                            'amount': amount_val,
                            'balance': float(balance.replace(',', ''))
                        }
                        all_transactions.append(transaction)
                        
                        # Categorize income
                        desc_lower = description.lower()
                        if any(kw in desc_lower for kw in ['salary', 'salary deposit', 'payroll', 'monthly salary']):
                            salary_deposits.append(amount_val)
                            print(f"    → SALARY: AED {amount_val:,.2f}")
                        elif any(kw in desc_lower for kw in ['freelance', 'freelance income', 'contract', 'freelance payment']):
                            freelance_income.append(amount_val)
                            print(f"    → FREELANCE: AED {amount_val:,.2f}")
                        
                        matched = True
                    elif pattern_num == 1:  # Date Description +/-Amount
                        date, description, amount = match
                        amount_val = float(amount.replace('+', '').replace(',', ''))
                        
                        transaction = {
                            'date': date,
                            'description': description.strip(),
                            'amount': amount_val
                        }
                        all_transactions.append(transaction)
                        
                        desc_lower = description.lower()
                        if any(kw in desc_lower for kw in ['salary', 'salary deposit', 'payroll', 'monthly salary']):
                            salary_deposits.append(amount_val)
                            print(f"    → SALARY: AED {amount_val:,.2f}")
                        elif any(kw in desc_lower for kw in ['freelance', 'freelance income', 'contract', 'freelance payment']):
                            freelance_income.append(amount_val)
                            print(f"    → FREELANCE: AED {amount_val:,.2f}")
                        
                        matched = True
            
            if matched:
                break
    
    # Calculate totals
    total_salary = sum(salary_deposits) if salary_deposits else 0.0
    total_freelance = sum(freelance_income) if freelance_income else 0.0
    total_income = total_salary + total_freelance
    
    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY:")
    print(f"{'='*60}")
    print(f"Total Salary Deposits: AED {total_salary:,.2f} ({len(salary_deposits)} entries)")
    print(f"Total Freelance Income: AED {total_freelance:,.2f} ({len(freelance_income)} entries)")
    print(f"Total Monthly Income: AED {total_income:,.2f}")
    print(f"Total Transactions Found: {len(all_transactions)}")
    print(f"\nTransactions:")
    for i, txn in enumerate(all_transactions[:15], 1):
        print(f"  {i}. {txn}")
    
    result = {
        'raw_text': text,
        'monthly_income': float(total_income),
        'salary_deposits': float(total_salary),
        'salary_deposit_count': len(salary_deposits),
        'freelance_income': float(total_freelance),
        'freelance_income_count': len(freelance_income),
        'total_transactions': len(all_transactions),
        'transactions': all_transactions[:15],
        'summary': f'Salary: AED {total_salary:,.2f} ({len(salary_deposits)} deposits), '
                  f'Freelance: AED {total_freelance:,.2f} ({len(freelance_income)} income), '
                  f'Total Monthly Income: AED {total_income:,.2f}'
    }
    
    return result


if __name__ == "__main__":
    # Test file path
    test_file = r"c:\Users\Sarthak\OneDrive\Desktop\Resume, Work and Policies\DGE Assignment\social-support-ai\data\synthetic\Fatima_Hassan_Al-Ketbi\bank_statement.pdf"
    
    # Check if file exists
    if not Path(test_file).exists():
        print(f"❌ File not found: {test_file}")
    else:
        print(f"✓ File found: {test_file}")
        result = extract_bank_statement_debug(test_file)
        
        print(f"\n{'='*60}")
        print("FINAL RESULT (as dictionary):")
        print(f"{'='*60}")
        for key, value in result.items():
            if key != 'raw_text':  # Skip raw text for readability
                print(f"{key}: {value}")
