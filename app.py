import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV Export Links (Ensure GIDs match your sheet tabs)
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1496660724"
DATA_BACKEND_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1815143324"

def load_sheet_data(url):
    """
    Downloads the Google Sheet as CSV and automatically finds the 
    row containing headers like 'User ID' or 'Ward'.
    """
    try:
        # Load raw data with no headers to find the actual header row
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # Search for a row that contains our key columns
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.lower()
            if any(key in row_str.values for key in ['user id', 'ward', 'hp name', 'disease']):
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            # Set the found row as header and clean the dataframe
            df = df_raw.iloc[header_row_idx:].copy()
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # Remove entirely empty rows and columns (common in Google Sheets)
            df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# Initialize Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    st.title("🔐 Mumbai Disease Surveillance Login")
    
    with st.form("login_form"):
        input_user = st.text_input("User ID")
        input_pass = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")

        if login_btn:
            users_df = load_sheet_data(USER_DB_URL)
            
            if not users_df.empty:
                # Basic column name check
                if 'User ID' in users_df.columns and 'Password' in users_df.columns:
                    # Match credentials
                    match = users_df[(users_df['User ID'] == input_user) & (users_df['Password'] == str(input_pass))]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = match['Role'].values[0]
                        st.session_state['user_ward'] = match['Ward'].values[0]
                        st.rerun()
                    else:
                        st.error("Invalid User ID or Password")
                else:
                    st.warning(f"Columns detected: {list(users_df.columns)}")
                    st.error("Header Error: 'User ID' column not detected in the sheet.")
            else:
                st.error("Access Error: Could not fetch data. Check Google Sheet 'Share' settings.")

# --- DASHBOARD PAGE ---
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']

    st.sidebar.title("App Navigation")
    st.sidebar.success(f"Logged in as: {role}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # ADMIN VIEW
    if role == "Admin":
        st.title("🏆 Master Dashboard (All Wards)")
        
        st.subheader("Disease Comparison")
        backend_df = load_sheet_data(DATA_BACKEND_URL)
        st.dataframe(backend_df, use_container_width=True)

        st.subheader("Global Ward Statistics")
        main_df = load_sheet_data(DATA_MAIN_URL)
        if not main_df.empty and 'Ward' in main_df.columns:
            selected_ward = st.selectbox("Select Ward", main_df['Ward'].unique())
            st.dataframe(main_df[main_df['Ward'] == selected_ward], use_container_width=True)

    # USER VIEW
    else:
        st.title(f"📍 Ward Report: {ward}")
        
        main_df = load_sheet_data(DATA_MAIN_URL)
        if not main_df.empty and 'Ward' in main_df.columns:
            st.subheader(f"Data for Ward {ward}")
            st.dataframe(main_df[main_df['Ward'] == ward], use_container_width=True)

        st.subheader("Health Post Details")
        hp_df = load_sheet_data(DATA_HP_URL)
        if not hp_df.empty and 'Ward' in hp_df.columns:
            st.dataframe(hp_df[hp_df['Ward'] == ward], use_container_width=True)
