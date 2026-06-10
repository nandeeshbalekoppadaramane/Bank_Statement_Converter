import streamlit as st
import tempfile
import os
import parsers

# Configure the page
st.set_page_config(
    page_title="Bank Statement Converter",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed", # Collapse sidebar to give more focus
)

# Initialize Session State
if 'step' not in st.session_state:
    st.session_state.step = 'select_bank'
if 'selected_bank' not in st.session_state:
    st.session_state.selected_bank = "Select a Bank..."
if 'df_extracted' not in st.session_state:
    st.session_state.df_extracted = None
if 'excel_data' not in st.session_state:
    st.session_state.excel_data = None

def reset_app():
    st.session_state.step = 'select_bank'
    st.session_state.selected_bank = "Select a Bank..."
    st.session_state.df_extracted = None
    st.session_state.excel_data = None

# Custom CSS for better aesthetics
st.markdown("""
<style>
    /* Header styling */
    h1 {
        color: #1e3d59;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
    }
    
    /* Subheader styling */
    h2, h3 {
        color: #ff6e40;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Creator section styling */
    .creator-card {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-top: 50px;
        border-left: 5px solid #ff6e40;
    }
    
    .creator-name {
        font-size: 1.5em;
        font-weight: bold;
        color: #1e3d59;
        margin-bottom: 5px;
    }
    
    .creator-bio {
        color: #475569;
        font-size: 1em;
        margin-bottom: 10px;
        line-height: 1.5;
    }
    
    .social-links a {
        color: #0077b5; /* LinkedIn Blue */
        text-decoration: none;
        font-weight: bold;
    }
    
    .social-links a:hover {
        text-decoration: underline;
    }
    
    /* Styling the uploader area to be large and prominent */
    .stFileUploader > div > div {
        background-color: #f8fafc;
        border-radius: 15px;
        padding: 50px !important;
        border: 2px dashed #0077b5;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div > div:hover {
        background-color: #e0f2fe;
        border-color: #0284c7;
    }
    
    /* Center text */
    .center-text {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# Main Content
st.title("🏦 Bank Statement Converter")
st.markdown("<p class='center-text'>Easily convert your bank statements into a clean, unified Excel format.</p>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# STEP 1: Select Bank
# ==========================================
if st.session_state.step == 'select_bank':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("1. Select Your Bank")
        
        banks = [
            "Select a Bank...",
            "Canara Bank",
            "HDFC Bank",
            "Union Bank",
            "ICICI Bank (Coming Soon)",
            "State Bank of India (Coming Soon)"
        ]
        
        selected_bank = st.selectbox("Choose the bank whose statement you want to convert:", banks)
        
        if selected_bank not in ["Select a Bank...", "Canara Bank", "HDFC Bank", "Union Bank"]:
            st.warning(f"Support for **{selected_bank}** is coming soon. Please select Canara, HDFC or Union Bank.")
        elif selected_bank != "Select a Bank...":
            st.session_state.selected_bank = selected_bank
            st.success(f"Bank Selected: **{selected_bank}**")
            
            if st.button("Next: Upload Statement ➡️", type="primary", use_container_width=True):
                st.session_state.step = 'upload_file'
                st.rerun()

# ==========================================
# STEP 2 & 3: Upload and Process
# ==========================================
elif st.session_state.step == 'upload_file':
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.button("⬅️ Back to Bank Selection", on_click=reset_app)
        st.subheader(f"2. Upload {st.session_state.selected_bank} Statement")
        
        uploaded_file = st.file_uploader("Drag and drop your PDF statement here", type=['pdf'])
        
        if uploaded_file is not None:
            st.success(f"File **{uploaded_file.name}** ready for processing!")
            
            if st.button("Process & Convert to Excel 🚀", type="primary", use_container_width=True):
                # Progress Area
                st.markdown("### ⚙️ Processing your file...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total):
                    percent = int((current / total) * 100)
                    progress_bar.progress(percent)
                    status_text.text(f"Processing page {current} of {total}...")
                
                try:
                    # Save uploaded file to temp path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                        tmp_pdf.write(uploaded_file.getvalue())
                        temp_pdf_path = tmp_pdf.name
                        
                    # Prepare output excel path
                    temp_excel_path = temp_pdf_path.replace(".pdf", ".xlsx")
                    
                    # Call appropriate parser
                    if st.session_state.selected_bank == "Canara Bank":
                        df_extracted = parsers.parse_canara_statement(temp_pdf_path, temp_excel_path, update_progress)
                    elif st.session_state.selected_bank == "HDFC Bank":
                        df_extracted = parsers.parse_hdfc_statement(temp_pdf_path, temp_excel_path, update_progress)
                    elif st.session_state.selected_bank == "Union Bank":
                        df_extracted = parsers.parse_union_statement(temp_pdf_path, temp_excel_path, update_progress)
                        
                    # Read the generated Excel file to memory
                    with open(temp_excel_path, "rb") as f:
                        excel_data = f.read()
                        
                    # Clean up temp files
                    os.remove(temp_pdf_path)
                    os.remove(temp_excel_path)
                    
                    # Save to session state and move to next step
                    st.session_state.df_extracted = df_extracted
                    st.session_state.excel_data = excel_data
                    st.session_state.step = 'results'
                    st.rerun()
                    
                except Exception as e:
                    status_text.error(f"An error occurred during conversion: {str(e)}")

# ==========================================
# STEP 4: Results (Table only)
# ==========================================
elif st.session_state.step == 'results':
    st.success(f"✅ Extraction Complete! Found {len(st.session_state.df_extracted)} transactions.")
    
    col_dl, col_reset = st.columns([1, 1])
    with col_dl:
        st.download_button(
            label="⬇️ Download Full Excel File",
            data=st.session_state.excel_data,
            file_name=f"{st.session_state.selected_bank}_Converted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
    with col_reset:
        st.button("🔄 Convert Another File", on_click=reset_app, use_container_width=True)
        
    st.subheader("📊 Extracted Transactions")
    st.dataframe(st.session_state.df_extracted, use_container_width=True)

st.markdown("---")

# Creator Section
st.markdown("""
<div class="creator-card">
    <div class="creator-name">👨‍💻 About the Creator: Nandeesh</div>
    <div class="creator-bio">
        Hi! I'm <strong>Nandeesh</strong>, a passionate developer dedicated to building tools that make data processing easier and more efficient. 
        I love exploring technologies and creating intuitive, user-friendly applications that solve real-world problems.
    </div>
    <div class="social-links">
        Let's connect: <a href="YOUR_LINKEDIN_URL_HERE" target="_blank">LinkedIn</a>
    </div>
</div>
""", unsafe_allow_html=True)
