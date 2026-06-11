import argparse
import sys
import os

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import base_parse

def main():
    parser = argparse.ArgumentParser(description="Bank Statement Parser CLI")
    
    parser.add_argument("--bank-name", required=True, help="Name of the bank (e.g., hdfc, union, canara)")
    parser.add_argument("--version", help="Version of the parser to use (e.g., 0.0.0). Defaults to latest.")
    parser.add_argument("--pdf-file", required=True, help="Path to the PDF statement file")
    parser.add_argument("--save-loc", required=True, help="Path where the converted Excel file will be saved")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file not found at {args.pdf_file}")
        sys.exit(1)
        
    # Ensure the directory for save-loc exists
    save_dir = os.path.dirname(os.path.abspath(args.save_loc))
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"🚀 Processing {args.bank_name} statement: {args.pdf_file}")
    
    try:
        def cli_progress(current, total):
            sys.stdout.write(f"\rProcessing page {current} of {total}...")
            sys.stdout.flush()
            if current == total:
                sys.stdout.write("\n")

        df = base_parse.parse_statement(
            bank_name=args.bank_name,
            pdf_path=args.pdf_file,
            output_excel=args.save_loc,
            progress_callback=cli_progress,
            version=args.version
        )
        
        print(f"✅ Success! Extracted {len(df)} transactions.")
        print(f"📁 Saved to: {args.save_loc}")
        
    except Exception as e:
        print(f"\n❌ Error during parsing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
