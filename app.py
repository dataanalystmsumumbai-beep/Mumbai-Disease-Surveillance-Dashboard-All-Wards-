import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Mumbai Disease Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV Links with GIDs
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1496660724"
DATA_BACKEND_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1815143324"

def load_google_sheet(url, key_column):
    """
    Cleans Google Sheet data by skipping empty leading rows and columns.
    Searches for the row containing 'key_column' and sets it as header.
    """
    try:
        # Load raw data without headers to find the actual table
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # 1. Find the row index where our 'key_column' exists
        header_row_idx = None
        for i, row in df_raw.iterrows():
            if row.astype(str).str.contains(key_column, case=False, na=False).any():
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            # 2. Slice dataframe from that row
            df = df_raw.iloc[header_row_idx:].copy()
            
            # 3. Set the first row of this slice as column names
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # 4. Remove empty columns (caused by empty A, B, C columns in sheet)
            df = df.loc[:, df.columns.notna()]
            df = df.loc[:, ~df.columns.str.contains('^Unnamed|^nan', case=False)]
            
            # 5. Final cleanup: drop empty rows
            df = df.dropna(how='all')
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Sheet Loading Error: {e}")
        return pd.DataFrame()

# Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔐 Surveillance System Login")
    
    with st.form("login_box"):
        u_id = st.text_input("User ID")
        u_pw = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")
        
        if login_btn:
            # Look for 'User ID' keyword to find header row
            users_df = load_google_sheet(USER_DB_URL, "User ID")
            
            if not users_df.empty:
                # Basic credential check
                if 'User ID' in users_df.columns and 'Password' in users_df.columns:
                    match = users_df[(users_df['User ID'] == u_id) & (users_df['Password'] == str(u_pw))]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = match.iloc[0]['Role']
                        st.session_state['user_ward'] = match.iloc[0]['Ward']
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                else:
                    st.error(f"Structure Error: Found columns {list(users_df.columns)}")
            else:
                st.error("Could not fetch User Database. Check Sheet Sharing.")

# --- DASHBOARD ---
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']
    
    st.sidebar.success(f"Login: {st.session_state['user_role']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # ADMIN
    if role == "Admin":
        st.title("🏆 Master Dashboard")
        main_df = load_google_sheet(DATA_MAIN_URL, "Ward")
        st.dataframe(main_df, use_container_width=True)
        
    # USER
    else:
        st.title(f"📍 Ward Status: {ward}")
        main_df = load_google_sheet(DATA_MAIN_URL, "Ward")
        if not main_df.empty and 'Ward' in main_df.columns:
            st.dataframe(main_df[main_df['Ward'] == ward], use_container_width=True)
