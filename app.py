import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Disease Surveillance Dashboard", layout="wide")

# Google Sheet Details
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# Specific URLs for each tab using GID
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1496660724"
DATA_BACKEND_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1815143324"

def load_robust_data(url):
    """
    This function reads the CSV and automatically finds the header row 
    to avoid 'KeyError' caused by empty rows/columns in Google Sheets.
    """
    try:
        # Load raw data without headers first
        df_raw = pd.read_csv(url, header=None)
        
        # Find the index of the row that contains 'User ID' or 'Ward'
        header_index = 0
        for i, row in df_raw.iterrows():
            if row.astype(str).str.contains('User ID|Ward|Disease', case=False, na=False).any():
                header_index = i
                break
        
        # Re-load or set the found row as header
        df = df_raw.iloc[header_index:].copy()
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        
        # Remove completely empty columns and rows
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        
        # Clean column names (strip spaces and handle NaN headers)
        df.columns = [str(c).strip() if pd.notna(c) else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.title("🔐 Login - Disease Surveillance Dashboard")
    
    with st.form("login_form"):
        uid = st.text_input("User ID")
        pwd = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")
        
        if login_btn:
            users_df = load_robust_data(USER_DB_URL)
            
            if not users_df.empty:
                # Ensure 'User ID' column exists before filtering
                if 'User ID' in users_df.columns and 'Password' in users_df.columns:
                    # Match credentials
                    match = users_df[(users_df['User ID'] == uid) & (users_df['Password'] == str(pwd))]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = match['Role'].values[0]
                        st.session_state['user_ward'] = match['Ward'].values[0]
                        st.rerun()
                    else:
                        st.error("Invalid User ID or Password")
                else:
                    st.error("Login structure error. Please check 'User ID' sheet headers.")
            else:
                st.error("Could not connect to User Database.")

# --- DASHBOARD SCREEN (After Login) ---
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']
    
    st.sidebar.success(f"Login Successful!")
    st.sidebar.markdown(f"**Role:** {role}")
    st.sidebar.markdown(f"**Assigned Ward:** {ward}")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- ADMIN (MASTER) VIEW ---
    if role == "Admin":
        st.title("🏆 Master Dashboard - All Wards")
        
        # Tab 1: Disease Trends from Backend
        st.subheader("Comparative Analysis (Jan-May)")
        backend_df = load_robust_data(DATA_BACKEND_URL)
        st.dataframe(backend_df, use_container_width=True)
        
        # Tab 2: Full Data with Filtering
        st.subheader("Global Data Filter")
        main_df = load_robust_data(DATA_MAIN_URL)
        if 'Ward' in main_df.columns:
            ward_list = main_df['Ward'].unique().tolist()
            selected_ward = st.selectbox("Select Ward to Inspect", ward_list)
            st.write(main_df[main_df['Ward'] == selected_ward])

    # --- USER (WARD) VIEW ---
    else:
        st.title(f"📍 Surveillance Report - Ward {ward}")
        
        # Load main data and filter
        main_df = load_robust_data(DATA_MAIN_URL)
        if 'Ward' in main_df.columns:
            ward_data = main_df[main_df['Ward'] == ward]
            st.subheader(f"Disease Status in Ward {ward}")
            st.dataframe(ward_data, use_container_width=True)
        
        # Load Health Post Data
        hp_df = load_robust_data(DATA_HP_URL)
        if 'Ward' in hp_df.columns:
            hp_ward_data = hp_df[hp_df['Ward'] == ward]
            st.subheader(f"Health Post Wise Details ({ward})")
            st.dataframe(hp_ward_data, use_container_width=True)
