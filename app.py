import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# Google Sheet Details
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV export links for different tabs (GIDs from your link)
# User ID tab (gid=79694728)
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
# Data tab (gid logic - normally gid=0 for first tab, adjust if needed)
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"
# HP Data tab
HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1496660724"

@st.cache_data(ttl=600) # 10 मिनिटांनी डेटा ऑटो-रिफ्रेश होईल
def load_data(url, skip_rows=0):
    return pd.read_csv(url, skiprows=skip_rows)

try:
    # Loading Sheets
    user_db = load_data(USER_URL, skip_rows=1) # User ID sheet usually has 1 empty row
    
    # Session State for Login
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.session_state['user_ward'] = None

    if not st.session_state['logged_in']:
        st.title("🔐 Login - Epidemiology Dashboard")
        username = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # Credential check
            user_info = user_db[(user_db['User ID'] == username) & (user_db['Password'] == str(password))]
            if not user_info.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = user_info['Role'].values[0]
                st.session_state['user_ward'] = user_info['Ward'].values[0]
                st.rerun()
            else:
                st.error("Invalid Username or Password")

    else:
        role = st.session_state['user_role']
        ward = st.session_state['user_ward']
        
        st.sidebar.write(f"Logged in as: **{username}**")
        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

        # Loading Main Data based on Role
        if role == "Admin":
            st.title("🏆 Master Dashboard (All Wards)")
            all_data = load_data(DATA_URL, skip_rows=2)
            st.dataframe(all_data)
        else:
            st.title(f"📍 Ward Dashboard: {ward}")
            all_data = load_data(DATA_URL, skip_rows=2)
            # Filter only for this ward
            ward_data = all_data[all_data['Ward'] == ward]
            st.dataframe(ward_data)

except Exception as e:
    st.error(f"Error connecting to Google Sheet: {e}")
