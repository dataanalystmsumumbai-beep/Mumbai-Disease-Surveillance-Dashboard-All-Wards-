import streamlit as st
import pandas as pd

# =====================================================
# 1. PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# =====================================================
# 2. GOOGLE SHEET CONFIG
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

# =====================================================
# 3. SMART DATA LOADER (Skips Titles & Finds Headers)
# =====================================================
@st.cache_data(ttl=60)
def load_and_fix_sheet(url, expected_col):
    try:
        # Load the whole sheet first
        df_raw = pd.read_csv(url, header=None, dtype=str).fillna("")
        
        # Look for the row that actually contains the "expected_col" (e.g., 'User ID' or 'Ward')
        header_row_index = None
        for i, row in df_raw.iterrows():
            if expected_col in row.values:
                header_row_index = i
                break
        
        if header_row_index is not None:
            # Re-read or slice from that row onwards
            df = df_raw.iloc[header_row_index:].copy()
            df.columns = df.iloc[0].str.strip() # Set the found row as header
            df = df[1:].reset_index(drop=True) # Remove the header row from data
            
            # Final cleanup
            df = df.dropna(axis=1, how='all')
            df = df.map(lambda x: str(x).strip() if x else "")
            return df
        else:
            st.error(f"Could not find a row containing '{expected_col}'")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# =====================================================
# 4. SESSION STATE
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}

# =====================================================
# 5. LOGIN PAGE
# =====================================================
if not st.session_state.auth["logged_in"]:
    st.title("🔐 Login")
    
    with st.form("login_box"):
        u_id = st.text_input("User ID")
        u_pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            # We expect the 'User ID' tab to have a column named "User ID"
            users_df = load_and_fix_sheet(USER_URL, "User ID")
            
            if not users_df.empty:
                # Match credentials
                match = users_df[
                    (users_df["User ID"] == u_id) & 
                    (users_df["Password"] == u_pw)
                ]
                
                if not match.empty:
                    st.session_state.auth = {
                        "logged_in": True,
                        "id": match.iloc[0]["User ID"],
                        "ward": match.iloc[0]["Ward"],
                        "role": match.iloc[0]["Role"]
                    }
                    st.rerun()
                else:
                    st.error("❌ Incorrect User ID or Password.")

# =====================================================
# 6. DASHBOARD PAGE
# =====================================================
else:
    st.sidebar.title(f"👤 {st.session_state.auth['id']}")
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}
        st.rerun()

    st.title(f"📊 Dashboard - {st.session_state.auth['ward']} Ward")
    
    # We expect the 'Data' tab to have a column named "Ward"
    data_df = load_and_fix_sheet(DATA_URL, "Ward")
    
    if not data_df.empty:
        if st.session_state.auth["role"].lower() == "admin":
            st.subheader("Full Data Access")
            st.dataframe(data_df, use_container_width=True)
        else:
            st.subheader(f"Data for {st.session_state.auth['ward']}")
            # Filter by Ward
            filtered = data_df[data_df["Ward"] == st.session_state.auth["ward"]]
            st.dataframe(filtered, use_container_width=True)
