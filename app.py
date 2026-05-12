import streamlit as st
import pandas as pd

# =====================================================
# 1. PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Mumbai Disease Surveillance", layout="wide")

# =====================================================
# 2. GOOGLE SHEET CONFIG (Direct Link to your tabs)
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# GID for 'User ID' tab is 79694728
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
# GID for 'Data' tab is 1152016550
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

# =====================================================
# 3. ROBUST DATA LOADER
# =====================================================
@st.cache_data(ttl=60)
def load_sheet_data(url):
    try:
        # Read the CSV and force all columns to be strings to avoid ID issues
        df = pd.read_csv(url, dtype=str).fillna("")
        # Clean up column names (remove any hidden spaces)
        df.columns = [str(col).strip() for col in df.columns]
        # Clean up data cells (remove any hidden spaces)
        df = df.map(lambda x: str(x).strip() if x else "")
        return df
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return pd.DataFrame()

# =====================================================
# 4. LOGIN SYSTEM
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}

if not st.session_state.auth["logged_in"]:
    st.title("🔐 Mumbai Health Login")
    
    with st.form("login_box"):
        u_id = st.text_input("User ID")
        u_pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            users_df = load_sheet_data(USER_URL)
            
            if not users_df.empty:
                # Check if columns exist
                if "User ID" in users_df.columns and "Password" in users_df.columns:
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
                        st.success("✅ Logged in!")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect User ID or Password.")
                else:
                    st.error(f"❌ Header mismatch. Found: {list(users_df.columns)}")
            else:
                st.error("❌ Could not connect to Google Sheets.")

# =====================================================
# 5. DASHBOARD
# =====================================================
else:
    # Sidebar
    st.sidebar.title(f"👤 {st.session_state.auth['id']}")
    st.sidebar.write(f"**Role:** {st.session_state.auth['role']}")
    st.sidebar.write(f"**Ward:** {st.session_state.auth['ward']}")
    
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}
        st.rerun()

    st.title(f"📊 Dashboard - {st.session_state.auth['ward']} View")
    
    # Load Main Health Data
    data_df = load_sheet_data(DATA_URL)
    
    if not data_df.empty:
        if st.session_state.auth["role"].lower() == "admin":
            st.subheader("Admin: Full Data Access")
            st.dataframe(data_df, use_container_width=True)
        else:
            st.subheader(f"Data for Ward {st.session_state.auth['ward']}")
            if "Ward" in data_df.columns:
                # Filter specifically for the user's ward
                filtered = data_df[data_df["Ward"] == st.session_state.auth["ward"]]
                if not filtered.empty:
                    st.dataframe(filtered, use_container_width=True)
                else:
                    st.info("No records found for your ward.")
            else:
                st.warning("Column 'Ward' not found in Data sheet.")
