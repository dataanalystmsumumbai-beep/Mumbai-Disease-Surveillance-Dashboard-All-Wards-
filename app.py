import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Disease Surveillance Dashboard", layout="wide")

# Google Sheet Details
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

def load_dynamic_sheet(url, keyword):
    """
    Ha function sheet madhye 'User ID' kiva 'Ward' kuthe aahe te shodhto 
    ani tyachya bajucha purna data table load karto.
    """
    try:
        # Purna sheet string mhanun read kara
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # 1. Header row shodha (jithe 'User ID' kiva 'Ward' lihila aahe)
        header_row_idx = None
        for i, row in df_raw.iterrows():
            if row.astype(str).str.contains(keyword, case=False, na=False).any():
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            # 2. Table slice kara
            df = df_raw.iloc[header_row_idx:].copy()
            
            # 3. Headers set kara ani rikame columns (A, B, C) kadhun taka
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # 4. Fakt te columns ghya jyana nav aahe (Unnamed kadhun taka)
            df = df.loc[:, df.columns.notna()]
            df = df.loc[:, ~df.columns.str.contains('^Unnamed|^nan', case=False)]
            
            # 5. Row cleanup
            df = df.dropna(how='all')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.title("🔐 Mumbai Health Login")
    
    with st.form("login"):
        u_id = st.text_input("User ID")
        u_pw = st.text_input("Password", type="password")
        btn = st.form_submit_button("Sign In")
        
        if btn:
            users_df = load_dynamic_sheet(USER_DB_URL, "User ID")
            
            if not users_df.empty:
                # Column check
                if 'User ID' in users_df.columns and 'Password' in users_df.columns:
                    match = users_df[(users_df['User ID'] == u_id) & (users_df['Password'] == str(u_pw))]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = match.iloc[0]['Role']
                        st.session_state['user_ward'] = match.iloc[0]['Ward']
                        st.rerun()
                    else:
                        st.error("Ghalat User ID kiva Password!")
                else:
                    st.warning(f"Columns found: {list(users_df.columns)}")
                    st.error("Sheet madhye 'User ID' navacha column sapadla nahi.")
            else:
                st.error("Database load hou shakla nahi. Sheet sharing check kar.")

# --- DASHBOARD SCREEN ---
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']
    
    st.sidebar.success(f"Login Success: {role}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📊 Dashboard - {ward} Ward")
    
    # Dashboard cha data load kara
    main_df = load_dynamic_sheet(DATA_MAIN_URL, "Ward")
    
    if not main_df.empty:
        # Admin sathi sagle wards, User sathi fakt tyancha ward
        if role != "Admin":
            display_df = main_df[main_df['Ward'] == ward]
        else:
            display_df = main_df
            
        st.subheader(f"Disease Data for {ward}")
        st.dataframe(display_df, use_container_width=True)
