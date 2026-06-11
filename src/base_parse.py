from importlib.machinery import ModuleSpec
import os
import importlib.util
import glob

PARSERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parsers')

def get_available_parsers():
    """
    Returns a dictionary of available parsers: {bank_name: [versions]}
    """
    parser_files = glob.glob(os.path.join(PARSERS_DIR, "*-v*.py"))
    parsers = {}
    for f in parser_files:
        filename = os.path.basename(f)
        name_part, version_part = filename.replace(".py", "").split("-v")
        if name_part not in parsers:
            parsers[name_part] = []
        parsers[name_part].append(version_part)
    
    # Sort versions for each bank
    for name in parsers:
        parsers[name].sort(reverse=True)
        
    return parsers

def parse_statement(bank_name, pdf_path, output_excel, progress_callback=None, version=None):
    """
    Unifies all bank statement logic.
    bank_name: name of the bank (one word)
    """
    parsers = get_available_parsers()
    bank_name_clean = bank_name.lower().strip()
    
    if bank_name_clean not in parsers:
        raise ValueError(f"No parser found for bank: {bank_name}")
    
    if version is None:
        version = parsers[bank_name_clean][0] # Latest
        
    parser_file = os.path.join(PARSERS_DIR, f"{bank_name_clean}-v{version}.py")
    
    if not os.path.exists(parser_file):
        raise ValueError(f"Parser file not found: {parser_file}")
    
    # Dynamic import
    spec = importlib.util.spec_from_file_location(f"parser_{bank_name_clean}", parser_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    if hasattr(module, 'parse'):
        return module.parse(pdf_path, output_excel, progress_callback)
    else:
        raise AttributeError(f"Parser {parser_file} does not have a 'parse' function.")