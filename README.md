# Bank Statement Converter

A modular and extensible tool to convert PDF bank statements into clean, unified Excel formats. This project supports multiple bank formats and provides both a user-friendly Web UI and a powerful Command Line Interface (CLI).

> [!NOTE]
> This project is a forked and significantly improved version of the original [Bank_Statement_Converter](https://github.com/nandeeshbalekoppadaramane/Bank_Statement_Converter) developed by **Nandeesh**. This version introduces a **modular rewrite** for better extensibility and full **CLI support** for automated workflows.

## Features

-   **Multi-Bank Support**: Easily add and manage parsers for different banks.
-   **Web Interface**: Built with Streamlit for a seamless, interactive experience.
-   **CLI Functionality**: Process statements in batches or automate workflows via the terminal.
-   **Modular Architecture**: Clean separation between parsing logic, core engine, and UI components.
-   **Dynamic Versioning**: Support for multiple versions of the same bank's statement format.

## Project Structure

```text
.
├── app.py                  # Streamlit Web Application
├── cli/
│   └── bank_parser.py      # Command Line Interface tool
├── parsers/                # Bank-specific parsing logic files
│   ├── hdfc-v0.0.0.py
│   ├── canara-v0.0.0.py
│   └── ...
├── src/
│   └── base_parse.py       # Core engine for dynamic parser loading
├── web/
│   ├── components.py       # UI components (Header, Footer)
│   └── styles.py           # Custom CSS styling
└── requirements.txt        # Project dependencies
```

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd project-bank_stmnt_parser
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Web Application

Launch the interactive web UI:
```bash
streamlit run app.py
```

### Command Line Interface (CLI)

Parse a statement directly from the terminal:
```bash
python cli/bank_parser.py --bank-name <bank-name> --pdf-file <path-to-pdf> --save-loc <output-path-xlsx>
```

**Options:**
-   `--bank-name`: Name of the bank (e.g., `hdfc`, `union`, `canara`).
-   `--pdf-file`: Path to the input PDF file.
-   `--save-loc`: Path where the output Excel file will be saved.
-   `--version`: (Optional) Specific parser version (e.g., `0.1`). Defaults to the latest version found in `parsers/`.

## How to Contribute

### Adding a New Bank Parser

1.  Create a new file in the `parsers/` directory.
2.  Name it `<bankname>-v<version>.py` (e.g., `icici-v0.0.py`).
3.  Implement a `parse(pdf_path, output_excel, progress_callback=None)` function that returns a Pandas DataFrame with columns ['Date', 'Description', 'Withdrawal', 'Deposit', 'Closing Balance'].
4.  The new bank will automatically appear in the Web UI and be available via the CLI.

### Any other features

Project is open and anyone willing to contribute can raise a pull request with their contributions.