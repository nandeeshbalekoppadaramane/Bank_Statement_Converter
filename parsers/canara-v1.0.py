import pdfplumber
import pandas as pd

def _clean_amt(val):
    """
    Cleans and converts a value to a float for Excel formatting.
    """
    if not val: 
        return 0.0
    v = str(val).replace(',', '').replace('Cr', '').replace('Dr', '').strip()
    try: 
        return float(v)
    except (ValueError, TypeError): 
        return val

def parse(pdf_path, output_excel, progress_callback=None):
    """
    Parses a Canara Bank Statement PDF, saves to Excel, and returns the DataFrame.
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
                    first_col = str(row[0]).upper() if row[0] else ""
                    if "DATE" in first_col or "TRANS" in first_col:
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
                            "Withdrawals": withdrawals,
                            "Deposits": deposits,
                            "Balance": balance
                        })

        if not all_data:
            raise Exception("No data extracted. Check PDF structure.")

        final_df = pd.DataFrame(all_data)
        
        # Apply amount cleaning
        final_df['Withdrawals'] = final_df['Withdrawals'].apply(_clean_amt)
        final_df['Deposits'] = final_df['Deposits'].apply(_clean_amt)
        final_df['Balance'] = final_df['Balance'].apply(_clean_amt)

        final_df = final_df[["Trans Date", "Description", "Withdrawals", "Deposits", "Balance"]]
        final_df.columns = ['Date', 'Description', 'Withdrawal', 'Deposit', 'Closing Balance']
        final_df.to_excel(output_excel, index=False)
        return final_df

    except Exception as e:
        raise Exception(f"Critical error during parsing: {str(e)}")
