import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Mumbai Disease Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV Links
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1496660724"
DATA_BACKEND_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1815143324"

def load_and_fix_data(url):
    """
    Finds the correct starting point of the data by searching for keywords
    and handles leading empty columns/rows.
    """
    try:
        # Load everything as strings to prevent errors
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # 1. Find the exact row and starting column for headers
        header_row = None
        for i, row in df_raw.iterrows():
            row_values = [str(val).strip().lower() for val in row if pd.notna(val)]
            if any(key in row_values for key in ['user id', 'ward', 'hp name', 'disease']):
                header_row = i
                break
        
        if header_row is not None:
            # Set the found row as header
            df = df_raw.iloc[header_row:].copy()
            df.columns = df.iloc[0].str.strip() # Set first row as column names
            df = df[1:].reset_index(drop=True)  # Remove the header row from data
            
            # 2. Remove columns that are completely NaN or have no name
            df = df.loc[:, df.columns.notna()]
            df = df.loc[:, df.columns != 'nan']
            
            # 3. Final cleaning: Drop completely empty rows
            df = df.dropna(how='all').reset_index(drop=True)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching sheet: {e}")
        return pd.DataFrame()

# Initialize Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    st.title("🔐 Mumbai Disease Surveillance Login")
    
    with st.form("login_box"):
        u_id = st.text_input("User ID")
        u_pw = st.text_input("Password", type="password")
        btn = st.form_submit_button("Login")

        if btn:
            users_df = load_and_fix_data(USER_DB_URL)
            
            if not users_df.empty:
                # Fuzzy matching for 'User ID' column (ignores extra spaces)
                id_col = next((c for c in users_df.columns if 'user id' in c.lower()), None)
                pw_col = next((c for c in users_df.columns if 'password' in c.lower()), None)

                if id_col and pw_col:
                    match = users_df[(users_df[id_col] == u_id) & (users_df[pw_col] == str(u_pw))]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        # Get Role and Ward safely
                        st.session_state['user_role'] = match.iloc[0].get('Role', 'User')
                        st.session_state['user_ward'] = match.iloc[0].get('Ward', 'All')
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                else:
                    st.warning(f"Detected columns: {list(users_df.columns)}")
                    st.error("Sheet structure error: 'User ID' or 'Password' columns not found.")
            else:
                st.error("Could not load User Database. Check Sheet permissions.")

# --- DASHBOARD PAGE ---
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']

    st.sidebar.success(f"Login: {role}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📍 Ward Report: {ward}")

    # Load Main Data
    main_df = load_and_fix_data(DATA_MAIN_URL)
    if not main_df.empty:
        # Filter logic
        ward_col = next((c for c in main_df.columns if 'ward' in c.lower()), None)
        if ward_col:
            if role != "Admin":
                display_df = main_df[main_df[ward_col] == ward]
            else:
                display_df = main_df
            st.dataframe(display_df, use_container_width=True)
