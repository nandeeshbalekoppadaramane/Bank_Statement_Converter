import pdfplumber
import pandas as pd
import re

def parse_hdfc_statement(pdf_path, output_excel, progress_callback=None):
    """
    Parses an HDFC Bank Statement PDF, saves to Excel, and returns the DataFrame.
    """
    transactions = []
    
    # Expanded column ranges for better coverage
    COL_RANGES = {
        'Date': (0, 100),         # Be greedy with the date column
        'Narration': (65, 320),
        'Withdrawal': (380, 485),
        'Deposit': (485, 565),
        'Balance': (565, 800)
    }
    
    current_tx = None
    
    # Junk patterns to skip in narration
    JUNK_PATTERNS = [
        r'PageNo\.:', r'Statementofaccount', r'Date Narration', r'Closingbalanceincludes',
        r'Contentsofthisstatement', r'Stateaccountbranch', r'HDFCBankGSTIN', r'RegisteredOffice',
        r'GeneratedOn:', r'GeneratedBy:', r'RequestingBranchCode:', r'STATEMENTSUMMARY',
        r'OpeningBalance', r'A/COpenDate', r'JOINTHOLDERS'
    ]
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i + 1, total_pages)
                
                words = page.extract_words()
                if not words:
                    continue
                
                # Group words by line with a small tolerance (2 pixels) for vertical jitter
                lines = {}
                for w in words:
                    found_line = False
                    for existing_y in lines.keys():
                        if abs(w['top'] - existing_y) < 2:
                            lines[existing_y].append(w)
                            found_line = True
                            break
                    if not found_line:
                        lines[w['top']] = [w]
                
                sorted_y = sorted(lines.keys())
                
                for y in sorted_y:
                    line_words = sorted(lines[y], key=lambda x: x['x0'])
                    
                    # Check for a date
                    date_word = next((w for w in line_words if COL_RANGES['Date'][0] <= w['x0'] <= COL_RANGES['Date'][1]), None)
                    
                    is_new_tx = False
                    if date_word and re.search(r'\d{2}/\d{2}/\d{2,4}', date_word['text']):
                        if y > 180: 
                            is_new_tx = True
                    
                    if is_new_tx:
                        if current_tx:
                            transactions.append(current_tx)
                        
                        current_tx = {
                            'Date': re.search(r'\d{2}/\d{2}/\d{2,4}', date_word['text']).group(),
                            'Narration': " ".join([w['text'] for w in line_words if COL_RANGES['Narration'][0] <= w['x0'] <= COL_RANGES['Narration'][1]]),
                            'Withdrawal': "".join([w['text'] for w in line_words if COL_RANGES['Withdrawal'][0] <= w['x0'] <= COL_RANGES['Withdrawal'][1]]),
                            'Deposit': "".join([w['text'] for w in line_words if COL_RANGES['Deposit'][0] <= w['x0'] <= COL_RANGES['Deposit'][1]]),
                            'Balance': "".join([w['text'] for w in line_words if COL_RANGES['Balance'][0] <= w['x0'] <= COL_RANGES['Balance'][1]])
                        }
                        
                    elif current_tx:
                        nar_words = [w['text'] for w in line_words if COL_RANGES['Narration'][0] <= w['x0'] <= COL_RANGES['Narration'][1]]
                        if nar_words:
                            text = " ".join(nar_words)
                            if not any(re.search(p, text, re.IGNORECASE) for p in JUNK_PATTERNS):
                                current_tx['Narration'] += " " + text
                        
                        if not current_tx['Withdrawal']:
                            current_tx['Withdrawal'] = "".join([w['text'] for w in line_words if COL_RANGES['Withdrawal'][0] <= w['x0'] <= COL_RANGES['Withdrawal'][1]])
                        if not current_tx['Deposit']:
                            current_tx['Deposit'] = "".join([w['text'] for w in line_words if COL_RANGES['Deposit'][0] <= w['x0'] <= COL_RANGES['Deposit'][1]])
                        if not current_tx['Balance']:
                            current_tx['Balance'] = "".join([w['text'] for w in line_words if COL_RANGES['Balance'][0] <= w['x0'] <= COL_RANGES['Balance'][1]])

            if current_tx:
                transactions.append(current_tx)
                
    except Exception as e:
        raise Exception(f"Critical error on page {i+1}: {str(e)}")

    if not transactions:
        raise Exception("No transaction data found in the PDF.")
        
    df = pd.DataFrame(transactions)
    df['Narration'] = df['Narration'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df = df[df['Balance'] != ""]
    
    def to_float(val):
        if not val or not isinstance(val, str): return 0.0
        clean_val = val.replace(',', '').replace('(', '').replace(')', '').strip()
        try:
            return float(clean_val)
        except:
            return 0.0
            
    df['Withdrawal Amt'] = df['Withdrawal'].apply(to_float)
    df['Deposit Amt'] = df['Deposit'].apply(to_float)
    df['Closing Balance'] = df['Balance'].apply(to_float)
    
    final_df = df[['Date', 'Narration', 'Withdrawal Amt', 'Deposit Amt', 'Closing Balance']]
    final_df.to_excel(output_excel, index=False)
    
    return final_df


def parse_union_statement(pdf_path, output_excel, progress_callback=None):
    """
    Parses a Union Bank Statement PDF, saves to Excel, and returns the DataFrame.
    """
    all_data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i + 1, total_pages)
                    
                table = page.extract_table()
                if not table:
                    continue

                df = pd.DataFrame(table)

                for index, row in df.iterrows():
                    # Skip header rows
                    if any(val is not None and "Date" in str(val) for val in row):
                        continue
                    if any(val is not None and "Balance" in str(val) for val in row):
                        continue
                    if len(row) < 8:
                        continue

                    date_time = str(row[0]).replace("\n", " ").strip() if row[0] else ""
                    remarks = str(row[1]).replace("\n", " ").strip() if row[1] else ""
                    withdrawals = str(row[5]).replace("\n", "").strip() if row[5] else ""
                    deposits = str(row[6]).replace("\n", "").strip() if row[6] else ""
                    balance = str(row[7]).replace("\n", "").strip() if row[7] else ""

                    if date_time or remarks:
                        all_data.append({
                            "Date & Time": date_time,
                            "Remarks": remarks,
                            "Withdrawals": withdrawals,
                            "Deposits": deposits,
                            "Balance": balance
                        })

        if not all_data:
            raise Exception("No data extracted. Check PDF structure.")

        final_df = pd.DataFrame(all_data)
        final_df = final_df[["Date & Time", "Remarks", "Withdrawals", "Deposits", "Balance"]]
        final_df.to_excel(output_excel, index=False)
        return final_df

    except Exception as e:
        raise e

def parse_canara_statement(pdf_path, output_excel, progress_callback=None):
    """
    Parses a Canara Bank Statement PDF, saves to Excel, and returns the DataFrame.
    Returns: Trans Date, Description, Withdraws, Deposit, Balance
    """
    all_data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i + 1, total_pages)
                    
                table = page.extract_table()
                if not table:
                    continue

                df = pd.DataFrame(table)

                for index, row in df.iterrows():
                    if len(row) < 8:
                        continue
                        
                    # Skip header rows
                    if row[0] and "DATE" in str(row[0]).upper():
                        continue
                    if row[0] and "TRANS" in str(row[0]).upper():
                        continue

                    trans_date = str(row[0]).replace("\n", " ").strip() if row[0] else ""
                    description = str(row[4]).replace("\n", " ").strip() if row[4] else ""
                    withdrawals = str(row[5]).replace("\n", "").strip() if row[5] else ""
                    deposits = str(row[6]).replace("\n", "").strip() if row[6] else ""
                    balance = str(row[7]).replace("\n", "").strip() if row[7] else ""

                    if trans_date or description:
                        all_data.append({
                            "Trans Date": trans_date,
                            "Description": description,
                            "Withdraws": withdrawals,
                            "Deposit": deposits,
                            "Balance": balance
                        })

        if not all_data:
            raise Exception("No data extracted. Check PDF structure.")

        final_df = pd.DataFrame(all_data)
        final_df = final_df[["Trans Date", "Description", "Withdraws", "Deposit", "Balance"]]
        
        # Clean amounts for better excel formatting
        def clean_amt(val):
            if not val: return 0.0
            v = str(val).replace(',', '').replace('Cr', '').replace('Dr', '').strip()
            try: return float(v)
            except: return val
            
        final_df['Withdraws'] = final_df['Withdraws'].apply(clean_amt)
        final_df['Deposit'] = final_df['Deposit'].apply(clean_amt)
        final_df['Balance'] = final_df['Balance'].apply(clean_amt)

        final_df.to_excel(output_excel, index=False)
        return final_df

    except Exception as e:
        raise e
