import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV export URLs for specific tabs
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1496660724"
DATA_BACKEND_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1815143324"

@st.cache_data(ttl=600)  # Refresh data every 10 minutes
def load_sheet_data(url, skip_rows=0):
    try:
        df = pd.read_csv(url, skiprows=skip_rows)
        # Clean column names (remove leading/trailing spaces)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Failed to load data from sheet: {e}")
        return pd.DataFrame()

# Session State for tracking login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None
    st.session_state['user_id'] = None

# Login UI
if not st.session_state['logged_in']:
    st.title("🔐 Surveillance System Login")
    
    with st.form("login_form"):
        username_input = st.text_input("User ID")
        password_input = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            # Load User Database (skipping empty rows if any)
            users_df = load_sheet_data(USER_DB_URL, skip_rows=1)
            
            # Validate credentials
            if not users_df.empty:
                # Find matching user
                match = users_df[(users_df['User ID'] == username_input) & (users_df['Password'] == str(password_input))]
                
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = match['Role'].values[0]
                    st.session_state['user_ward'] = match['Ward'].values[0]
                    st.session_state['user_id'] = username_input
                    st.rerun()
                else:
                    st.error("❌ Invalid User ID or Password")
            else:
                st.error("Error connecting to User Database.")

# Dashboard UI (After Successful Login)
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']
    
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    st.sidebar.info(f"User: {st.session_state['user_id']}\n\nRole: {role}\n\nWard: {ward}")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- ADMIN / MASTER DASHBOARD ---
    if role == "Admin":
        st.title("🏆 Master Dashboard - All Wards")
        
        # Load backend comparison data
        backend_df = load_sheet_data(DATA_BACKEND_URL)
        if not backend_df.empty:
            st.subheader("Disease Trends & Comparisons")
            st.dataframe(backend_df)
        
        # Load main data for ward-wise filtering
        main_df = load_sheet_data(DATA_MAIN_URL, skip_rows=2)
        if not main_df.empty:
            st.subheader("Full Data View")
            selected_ward = st.selectbox("Filter by Ward", main_df['Ward'].unique())
            filtered_data = main_df[main_df['Ward'] == selected_ward]
            st.dataframe(filtered_data)

    # --- USER / WARD DASHBOARD ---
    else:
        st.title(f"📍 Ward Report: {ward}")
        
        # Load main data and filter for current user's ward
        main_df = load_sheet_data(DATA_MAIN_URL, skip_rows=2)
        if not main_df.empty:
            st.subheader(f"Disease Statistics for Ward {ward}")
            ward_specific_data = main_df[main_df['Ward'] == ward]
            st.dataframe(ward_specific_data)
        
        # Load Health Post level data
        hp_df = load_sheet_data(DATA_HP_URL, skip_rows=4)
        if not hp_df.empty:
            st.subheader(f"Health Post Wise Breakdown - {ward}")
            hp_filtered = hp_df[hp_df['Ward'] == ward]
            st.dataframe(hp_filtered)
