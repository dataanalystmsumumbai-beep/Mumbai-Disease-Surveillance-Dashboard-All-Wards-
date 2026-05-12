import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# 1. YOUR GOOGLE SHEET ID
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# 2. TAB GIDs (Make sure these match your sheet)
# Click on each tab in Google Sheets and check the 'gid' in the URL
USER_GID = "79694728"
DATA_GID = "1152016550"

# Constructing URLs
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={USER_GID}"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={DATA_GID}"

def load_data_robust(url):
    try:
        # We read everything as strings to avoid format errors
        df = pd.read_csv(url, header=None, dtype=str)
        
        # Find row containing headers
        header_row_idx = None
        for i, row in df.iterrows():
            if row.astype(str).str.contains('User ID|Ward|Password', case=False).any():
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            new_header = df.iloc[header_row_idx].str.strip()
            df = df.iloc[header_row_idx+1:].copy()
            df.columns = new_header
            # Drop empty columns and rows
            df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
            # Reset index
            df = df.reset_index(drop=True)
            return df
        else:
            st.error("Header not found in the sheet.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Access Error: {e}")
        st.info("Check: Is the sheet shared as 'Anyone with the link can view'?")
        return pd.DataFrame()

# Initialize Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.title("🔐 Mumbai Disease Surveillance Login")
    
    with st.form("login_box"):
        uid = st.text_input("User ID")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            users_df = load_robust_data(USER_URL)
            
            if not users_df.empty:
                # Clean column names for matching
                users_df.columns = [str(c).strip() for c in users_df.columns]
                
                # Check for correct column names
                target_id_col = 'User ID'
                target_pw_col = 'Password'
                
                if target_id_col in users_df.columns and target_pw_col in users_df.columns:
                    # Validate
                    match = users_df[(users_df[target_id_col] == uid) & (users_df[target_pw_col] == str(pwd))]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = match['Role'].values[0] if 'Role' in match.columns else "User"
                        st.session_state['user_ward'] = match['Ward'].values[0] if 'Ward' in match.columns else "All"
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                else:
                    st.warning(f"Columns found: {list(users_df.columns)}")
                    st.error("Sheet structure mismatch. 'User ID' or 'Password' not found.")
            else:
                st.error("Could not load User Database. Check permissions.")

# --- DASHBOARD SCREEN ---
else:
    st.sidebar.success(f"Welcome {st.session_state['user_role']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.title(f"Dashboard - {st.session_state['user_ward']}")
    # Add your data display logic here...
