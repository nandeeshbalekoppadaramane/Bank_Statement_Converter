import streamlit as st
import tempfile
import os
from src import base_parse
from web import css_config, html_config, md_config, general_config

# Configure the page
st.set_page_config(
    page_title=general_config.PAGE_TITLE,
    page_icon=general_config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed", # Collapse sidebar to give more focus
)

# Initialize Session State
if 'step' not in st.session_state:
    st.session_state.step = 'select_bank'
if 'selected_bank' not in st.session_state:
    st.session_state.selected_bank = general_config.SELECT_BANK_DEFAULT
if 'df_extracted' not in st.session_state:
    st.session_state.df_extracted = None
if 'excel_data' not in st.session_state:
    st.session_state.excel_data = None

def reset_app():
    st.session_state.step = 'select_bank'
    st.session_state.selected_bank = general_config.SELECT_BANK_DEFAULT
    st.session_state.df_extracted = None
    st.session_state.excel_data = None

# Apply Custom CSS
st.markdown(css_config.CUSTOM_CSS, unsafe_allow_html=True)

# Header Section
st.markdown(md_config.MAIN_TITLE_MD)
st.markdown(html_config.HEADER_DESC_HTML, unsafe_allow_html=True)
st.markdown(md_config.DIVIDER_MD)

# ==========================================
# STEP 1: Select Bank
# ==========================================
if st.session_state.step == 'select_bank':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(general_config.SUBHEADER_SELECT_BANK)
        
        available_parsers = base_parse.get_available_parsers()
        supported_banks = [b.title() + " Bank" for b in available_parsers.keys()]
        
        banks = [
            general_config.SELECT_BANK_DEFAULT,
        ] + supported_banks + general_config.SUPPORT_COMING_SOON
        
        selected_bank = st.selectbox(general_config.SELECTBOX_LABEL, banks)
        
        if selected_bank != general_config.SELECT_BANK_DEFAULT and "(Coming Soon)" in selected_bank:
            st.warning(general_config.MSG_COMING_SOON.format(bank=selected_bank))
        elif selected_bank != general_config.SELECT_BANK_DEFAULT:
            st.session_state.selected_bank = selected_bank
            st.success(general_config.MSG_BANK_SELECTED.format(bank=selected_bank))
            
            if st.button(general_config.BTN_NEXT, type="primary", use_container_width=True):
                st.session_state.step = 'upload_file'
                st.rerun()

# ==========================================
# STEP 2 & 3: Upload and Process
# ==========================================
elif st.session_state.step == 'upload_file':
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.button(general_config.BTN_BACK, on_click=reset_app)
        st.subheader(general_config.SUBHEADER_UPLOAD_FILE.format(bank=st.session_state.selected_bank))
        
        uploaded_file = st.file_uploader(general_config.FILE_UPLOADER_LABEL, type=['pdf'])
        
        if uploaded_file is not None:
            st.success(general_config.MSG_FILE_READY.format(filename=uploaded_file.name))
            
            if st.button(general_config.BTN_PROCESS, type="primary", use_container_width=True):
                # Progress Area
                st.markdown(md_config.PROCESSING_MD)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total):
                    percent = int((current / total) * 100)
                    progress_bar.progress(percent)
                    status_text.text(general_config.MSG_PROCESSING_PAGE.format(current=current, total=total))
                
                try:
                    # Save uploaded file to temp path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                        tmp_pdf.write(uploaded_file.getvalue())
                        temp_pdf_path = tmp_pdf.name
                        
                    # Prepare output excel path
                    temp_excel_path = temp_pdf_path.replace(".pdf", ".xlsx")
                    
                    # Call appropriate parser
                    bank_key = st.session_state.selected_bank.split(" ")[0].lower()
                    df_extracted = base_parse.parse_statement(bank_key, temp_pdf_path, temp_excel_path, update_progress)
                        
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
                    status_text.error(general_config.MSG_ERROR.format(error=str(e)))

# ==========================================
# STEP 4: Results (Table only)
# ==========================================
elif st.session_state.step == 'results':
    st.success(general_config.MSG_EXTRACTION_COMPLETE.format(count=len(st.session_state.df_extracted)))
    
    col_dl, col_reset = st.columns([1, 1])
    with col_dl:
        st.download_button(
            label=general_config.BTN_DOWNLOAD,
            data=st.session_state.excel_data,
            file_name=f"{st.session_state.selected_bank}_Converted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
    with col_reset:
        st.button(general_config.BTN_RESET, on_click=reset_app, use_container_width=True)
        
    st.subheader(general_config.SUBHEADER_RESULTS)
    st.dataframe(st.session_state.df_extracted, use_container_width=True)

# Footer Section
st.markdown(md_config.DIVIDER_MD)
st.markdown(html_config.FOOTER_HTML, unsafe_allow_html=True)
