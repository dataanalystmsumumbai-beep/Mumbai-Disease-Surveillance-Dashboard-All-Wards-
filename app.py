import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV URLs
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

def fetch_and_clean_data(url, target_keyword):
    """
    Finds the table by searching for a keyword (like 'User ID') 
    anywhere in the sheet and ignores empty rows/columns.
    """
    try:
        # Load raw data without headers
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # Search for the cell containing the target_keyword
        start_row, start_col = None, None
        for r_idx, row in df_raw.iterrows():
            for c_idx, value in enumerate(row):
                if str(value).strip().lower() == target_keyword.lower():
                    start_row, start_col = r_idx, c_idx
                    break
            if start_row is not None:
                break
        
        if start_row is not None:
            # Slice the dataframe starting from the detected table header
            df = df_raw.iloc[start_row:].copy()
            # Set the first row of the slice as columns
            df.columns = df.iloc[0].str.strip()
            # Remove the header row from data and reset index
            df = df[1:].reset_index(drop=True)
            
            # Remove any leading empty columns (like A, B, C)
            df = df.dropna(axis=1, how='all')
            # Remove completely empty rows
            df = df.dropna(axis=0, how='all')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

# Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN PAGE ---
if not st.session_state['logged_in']:
    st.title("🔐 Login")
    
    with st.form("login_form"):
        user_input = st.text_input("User ID")
        pass_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")
        
        if login_btn:
            # We search for the table starting with 'User ID'
            users_df = fetch_and_clean_data(USER_DB_URL, "User ID")
            
            if not users_df.empty:
                # Security: Check credentials
                if 'User ID' in users_df.columns and 'Password' in users_df.columns:
                    match = users_df[(users_df['User ID'] == user_input) & 
                                     (users_df['Password'] == str(pass_input))]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = match.iloc[0]['Role']
                        st.session_state['user_ward'] = match.iloc[0]['Ward']
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")
                else:
                    st.error("Sheet Error: 'User ID' or 'Password' columns not found.")
            else:
                st.error("Could not load Database. Check Sheet sharing permissions.")

# --- DASHBOARD PAGE ---
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']
    
    st.sidebar.success(f"Welcome: {role}")
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📊 Dashboard - Ward {ward}")
    
    # Load Main Data by searching for 'Ward' column
    main_df = fetch_and_clean_data(DATA_MAIN_URL, "Ward")
    
    if not main_df.empty:
        if role == "Admin":
            st.write("Full Ward Data (Admin Access)")
            st.dataframe(main_df, use_container_width=True)
        else:
            # Filter data for specific ward
            filtered_df = main_df[main_df['Ward'] == ward]
            st.write(f"Data for Ward {ward}")
            st.dataframe(filtered_df, use_container_width=True)
