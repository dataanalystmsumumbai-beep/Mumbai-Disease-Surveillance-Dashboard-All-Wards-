import streamlit as st
import pandas as pd

# 1. PAGE CONFIG
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# 2. GOOGLE SHEET CONFIG
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

# 3. DATA LOADER (Finds headers dynamically anywhere in the sheet)
@st.cache_data(ttl=60)
def load_and_fix_sheet(url, expected_col):
    try:
        # Load raw CSV without assuming headers
        df_raw = pd.read_csv(url, header=None, dtype=str).fillna("")
        
        # Search every row for the header keyword
        header_row_index = None
        for i, row in df_raw.iterrows():
            if expected_col in row.values:
                header_row_index = i
                break
        
        if header_row_index is not None:
            # Slice from that row and set headers
            df = df_raw.iloc[header_row_index:].copy()
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # Remove empty columns and strip whitespace from data
            df = df.dropna(axis=1, how='all')
            df = df.map(lambda x: str(x).strip() if x else "")
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Sheet Error: {e}")
        return pd.DataFrame()

# 4. SESSION STATE
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}

# 5. LOGIN UI
if not st.session_state.auth["logged_in"]:
    st.title("🔐 Login")
    with st.form("login_box"):
        u_id = st.text_input("User ID")
        u_pw = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            users_df = load_and_fix_sheet(USER_URL, "User ID")
            if not users_df.empty:
                match = users_df[(users_df["User ID"] == u_id) & (users_df["Password"] == u_pw)]
                if not match.empty:
                    st.session_state.auth = {
                        "logged_in": True,
                        "id": match.iloc[0]["User ID"],
                        "ward": match.iloc[0]["Ward"],
                        "role": match.iloc[0]["Role"]
                    }
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

# 6. DASHBOARD UI
else:
    st.sidebar.title(f"User: {st.session_state.auth['id']}")
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}
        st.rerun()

    st.title(f"📊 {st.session_state.auth['ward']} Ward Dashboard")
    data_df = load_and_fix_sheet(DATA_URL, "Ward")
    
    if not data_df.empty:
        if st.session_state.auth["role"].lower() == "admin":
            st.dataframe(data_df, use_container_width=True)
        else:
            filtered = data_df[data_df["Ward"] == st.session_state.auth["ward"]]
            st.dataframe(filtered, use_container_width=True)
