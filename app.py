import streamlit as st
import pandas as pd

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Public Health Dashboard",
    layout="wide"
)

# =====================================================
# GOOGLE SHEET CONFIG
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

# =====================================================
# DATA FETCH & CLEANING FUNCTION (FIXED)
# =====================================================
@st.cache_data(ttl=300)
def fetch_and_clean_data(url, target_keyword):
    try:
        # Read the raw CSV
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # Locate the header row based on target_keyword
        start_row, start_col = None, None
        for r_idx, row in df_raw.iterrows():
            for c_idx, value in enumerate(row):
                if str(value).strip().lower() == target_keyword.lower():
                    start_row, start_col = r_idx, c_idx
                    break
            if start_row is not None:
                break
        
        if start_row is not None:
            # Create table starting from found row
            df = df_raw.iloc[start_row:].copy()
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # Remove empty columns (A, B, C etc) and empty rows
            df = df.dropna(axis=1, how='all')
            df = df.dropna(axis=0, how='all')
            
            # --- FIXED: Use map instead of applymap for compatibility ---
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

# =====================================================
# SESSION STATE
# =====================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = ""
    st.session_state.user_ward = ""
    st.session_state.user_id = ""

# =====================================================
# LOGIN PAGE
# =====================================================
if not st.session_state.logged_in:
    st.title("🔐 Public Health Dashboard Login")
    
    with st.form("login_form"):
        user_input = st.text_input("User ID")
        pass_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")

    if login_btn:
        users_df = fetch_and_clean_data(USER_DB_URL, "User ID")

        if not users_df.empty:
            # Credentials matching
            match = users_df[
                (users_df["User ID"] == str(user_input).strip()) &
                (users_df["Password"] == str(pass_input).strip())
            ]

            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]["Role"]
                st.session_state.user_ward = match.iloc[0]["Ward"]
                st.session_state.user_id = match.iloc[0]["User ID"]
                st.rerun()
            else:
                st.error("Invalid Username or Password")
        else:
            st.error("User database not found. Please check Sheet data.")

# =====================================================
# DASHBOARD PAGE
# =====================================================
else:
    # Sidebar
    st.sidebar.title(f"Welcome, {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title(f"📊 Dashboard - {st.session_state.user_ward} Ward")
    
    # Load Main Data
    main_df = fetch_and_clean_data(DATA_MAIN_URL, "Ward")
    
    if not main_df.empty:
        if str(st.session_state.user_role).lower() == "admin":
            st.dataframe(main_df, use_container_width=True)
        else:
            # Filtering by User's Ward
            if "Ward" in main_df.columns:
                filtered_df = main_df[main_df["Ward"] == st.session_state.user_ward]
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.warning("Data loaded but 'Ward' column not detected.")
    else:
        st.info("No data available to display.")
