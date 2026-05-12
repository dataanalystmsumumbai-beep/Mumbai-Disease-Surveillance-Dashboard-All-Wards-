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
# GOOGLE SHEET CONFIG (Using your provided ID)
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV URLs with specific GIDs
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

# =====================================================
# DATA FETCH & CLEANING FUNCTION
# =====================================================
@st.cache_data(ttl=300)
def fetch_and_clean_data(url, target_keyword):
    """
    Finds the table by searching for a keyword anywhere 
    in the sheet and ignores empty rows/columns.
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
            # Slice dataframe from the detected header
            df = df_raw.iloc[start_row:].copy()
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # Basic cleanup
            df = df.dropna(axis=1, how='all') # Remove empty columns
            df = df.dropna(axis=0, how='all') # Remove empty rows
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            
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
    st.markdown("---")

    with st.form("login_form"):
        user_input = st.text_input("User ID")
        pass_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")

    if login_btn:
        with st.spinner("Checking Credentials..."):
            users_df = fetch_and_clean_data(USER_DB_URL, "User ID")

        if not users_df.empty and "User ID" in users_df.columns:
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
            st.error("❌ Could not load User Database. Check Sheet permissions.")

# =====================================================
# DASHBOARD PAGE
# =====================================================
else:
    role = st.session_state.user_role
    ward = st.session_state.user_ward

    # SIDEBAR
    st.sidebar.title("👤 Account")
    st.sidebar.write(f"**ID:** {st.session_state.user_id}")
    st.sidebar.write(f"**Role:** {role}")
    st.sidebar.write(f"**Ward:** {ward}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # MAIN CONTENT
    st.title(f"📊 Dashboard - {ward} Ward")
    
    with st.spinner("Loading Ward Data..."):
        main_df = fetch_and_clean_data(DATA_MAIN_URL, "Ward")

    if not main_df.empty:
        if role.lower() == "admin":
            st.subheader("🛡️ Admin View: All Data")
            st.dataframe(main_df, use_container_width=True)
        else:
            st.subheader(f"🏥 Health Records for Ward {ward}")
            # Filtering based on Ward
            if "Ward" in main_df.columns:
                filtered_df = main_df[main_df["Ward"] == ward]
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.warning("Ward column not found in data.")
    else:
        st.error("❌ No data available in the sheet.")
