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

# USER DATABASE SHEET
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"

# MAIN DATA SHEET
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

# =====================================================
# DATA FETCH & CLEANING FUNCTION
# =====================================================
@st.cache_data(ttl=300)
def fetch_and_clean_data(url, target_keyword):
    """
    Finds the table by searching for a keyword (like 'User ID' or 'Ward') 
    anywhere in the sheet and ignores empty rows/columns.
    """
    try:
        # Load raw data without headers to see everything
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # 1. Search for the cell containing the target_keyword
        start_row, start_col = None, None
        for r_idx, row in df_raw.iterrows():
            for c_idx, value in enumerate(row):
                if str(value).strip().lower() == target_keyword.lower():
                    start_row, start_col = r_idx, c_idx
                    break
            if start_row is not None:
                break
        
        if start_row is not None:
            # 2. Slice the dataframe starting from the detected table header
            df = df_raw.iloc[start_row:].copy()
            
            # 3. Set the first row of the slice as columns
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # 4. Remove any leading empty columns (like A, B, C)
            df = df.dropna(axis=1, how='all')
            
            # 5. Remove completely empty rows
            df = df.dropna(axis=0, how='all')
            
            # 6. Clean string values (strip spaces)
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Data Fetch Error: {e}")
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
    st.markdown("---")

    with st.form("login_form"):
        user_input = st.text_input("User ID")
        pass_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")

    if login_btn:
        with st.spinner("Authenticating..."):
            users_df = fetch_and_clean_data(USER_DB_URL, "User ID")

        if users_df.empty:
            st.error("❌ Could not load User Database. Please check Sheet permissions.")
        else:
            # Check if required columns exist after cleaning
            if "User ID" in users_df.columns and "Password" in users_df.columns:
                # Match credentials
                match = users_df[
                    (users_df["User ID"] == str(user_input).strip()) &
                    (users_df["Password"] == str(pass_input).strip())
                ]

                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = match.iloc[0]["Role"]
                    st.session_state.user_ward = match.iloc[0]["Ward"]
                    st.session_state.user_id = match.iloc[0]["User ID"]
                    st.success("✅ Login Successful")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")
            else:
                st.error(f"❌ Column Error. Found: {list(users_df.columns)}")

# =====================================================
# DASHBOARD PAGE
# =====================================================
else:
    role = st.session_state.user_role
    ward = st.session_state.user_ward
    user_id = st.session_state.user_id

    # SIDEBAR
    st.sidebar.title("👤 User Details")
    st.sidebar.write(f"**User:** {user_id}")
    st.sidebar.write(f"**Role:** {role}")
    st.sidebar.write(f"**Ward:** {ward}")
    st.sidebar.markdown("---")

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # MAIN CONTENT
    st.title("📊 Public Health Dashboard")
    
    with st.spinner("Loading Data..."):
        # Search for table starting with 'Ward'
        main_df = fetch_and_clean_data(DATA_MAIN_URL, "Ward")

    if main_df.empty:
        st.error("❌ Could not load Dashboard Data")
    else:
        st.markdown("---")
        
        if str(role).lower() == "admin":
            st.subheader("🛡️ Admin Access - Full Data")
            st.dataframe(main_df, use_container_width=True)
        else:
            st.subheader(f"🏥 Ward {ward} Data")
            if "Ward" in main_df.columns:
                filtered_df = main_df[main_df["Ward"] == str(ward).strip()]
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.warning("Filter column 'Ward' not found in data.")
                st.dataframe(main_df, use_container_width=True)
