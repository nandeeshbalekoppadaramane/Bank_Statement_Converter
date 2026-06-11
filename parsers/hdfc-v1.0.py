import pdfplumber
import pandas as pd
import re

# Constants
COL_RANGES = {
    'Date': (0, 100),         # Be greedy with the date column
    'Narration': (65, 320),
    'Withdrawal': (380, 485),
    'Deposit': (485, 565),
    'Balance': (565, 800)
}

# Junk patterns to skip in narration
JUNK_PATTERNS = [
    r'PageNo\.:', r'Statementofaccount', r'Date Narration', r'Closingbalanceincludes',
    r'Contentsofthisstatement', r'Stateaccountbranch', r'HDFCBankGSTIN', r'RegisteredOffice',
    r'GeneratedOn:', r'GeneratedBy:', r'RequestingBranchCode:', r'STATEMENTSUMMARY',
    r'OpeningBalance', r'A/COpenDate', r'JOINTHOLDERS'
]

def _to_float(val):
    """
    Cleans and converts a string value to a float.
    """
    if not val or not isinstance(val, str): 
        return 0.0
    clean_val = val.replace(',', '').replace('(', '').replace(')', '').strip()
    try:
        return float(clean_val)
    except (ValueError, TypeError):
        return 0.0

def _group_words_to_lines(words, tolerance=2):
    """
    Groups pdfplumber word objects into lines based on their vertical position.
    """
    lines = {}
    for w in words:
        found_line = False
        for existing_y in lines.keys():
            if abs(w['top'] - existing_y) < tolerance:
                lines[existing_y].append(w)
                found_line = True
                break
        if not found_line:
            lines[w['top']] = [w]
    
    sorted_y = sorted(lines.keys())
    return [sorted(lines[y], key=lambda x: x['x0']) for y in sorted_y]

def _extract_line_text(line_words, col_key):
    """
    Extracts and joins text from words within a specific column range.
    """
    range_min, range_max = COL_RANGES[col_key]
    words = [w['text'] for w in line_words if range_min <= w['x0'] <= range_max]
    return " ".join(words) if col_key == 'Narration' else "".join(words)

def _is_date_line(line_words):
    """
    Checks if a line starts with a date pattern in the Date column range.
    """
    date_word = next((w for w in line_words if COL_RANGES['Date'][0] <= w['x0'] <= COL_RANGES['Date'][1]), None)
    if date_word and re.search(r'\d{2}/\d{2}/\d{2,4}', date_word['text']):
        # Using a simple heuristic for vertical position if needed, 
        # but here we just return the match object or True
        return date_word
    return None

def parse(pdf_path, output_excel, progress_callback=None):
    """
    Parses an HDFC Bank Statement PDF, saves to Excel, and returns the DataFrame.
    """
    transactions = []
    current_tx = None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i + 1, total_pages)
                
                words = page.extract_words()
                if not words:
                    continue
                
                lines = _group_words_to_lines(words)
                
                for line_words in lines:
                    y_pos = line_words[0]['top']
                    date_word = _is_date_line(line_words)
                    
                    is_new_tx = False
                    if date_word and y_pos > 180: # Heuristic to skip header area
                        is_new_tx = True
                    
                    if is_new_tx:
                        if current_tx:
                            transactions.append(current_tx)
                        
                        current_tx = {
                            'Date': re.search(r'\d{2}/\d{2}/\d{2,4}', date_word['text']).group(), 
                            'Narration': _extract_line_text(line_words, 'Narration'),
                            'Withdrawal': _extract_line_text(line_words, 'Withdrawal'),
                            'Deposit': _extract_line_text(line_words, 'Deposit'),
                            'Balance': _extract_line_text(line_words, 'Balance')
                        }
                        
                    elif current_tx:
                        narration_text = _extract_line_text(line_words, 'Narration')
                        if narration_text:
                            if not any(re.search(p, narration_text, re.IGNORECASE) for p in JUNK_PATTERNS):
                                current_tx['Narration'] += " " + narration_text
                        
                        if not current_tx['Withdrawal']:
                            current_tx['Withdrawal'] = _extract_line_text(line_words, 'Withdrawal')
                        if not current_tx['Deposit']:
                            current_tx['Deposit'] = _extract_line_text(line_words, 'Deposit')
                        if not current_tx['Balance']:
                            current_tx['Balance'] = _extract_line_text(line_words, 'Balance')

            if current_tx:
                transactions.append(current_tx)
                
    except Exception as e:
        raise Exception(f"Critical error during parsing: {str(e)}")

    if not transactions:
        raise Exception("No transaction data found in the PDF.")
        
    df = pd.DataFrame(transactions)
    df['Narration'] = df['Narration'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df = df[df['Balance'] != ""]
    
    df['Withdrawal'] = df['Withdrawal'].apply(_to_float)
    df['Deposit'] = df['Deposit'].apply(_to_float)
    df['Closing Balance'] = df['Balance'].apply(_to_float)
    
    final_df = df[['Date', 'Narration', 'Withdrawal', 'Deposit', 'Closing Balance']]
    final_df.columns = ['Date', 'Description', 'Withdrawal', 'Deposit', 'Closing Balance']
    final_df.to_excel(output_excel, index=False)
    
    return final_df
