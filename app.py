import streamlit as st
import pandas as pd

# =====================================================
# 1. PAGE SETUP & STYLING
# =====================================================
st.set_page_config(page_title="Mumbai Health Dashboard", layout="centered")

# Custom CSS for Attractive UI
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .login-card {
        padding: 30px;
        border-radius: 15px;
        background-color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# 2. CONFIG & DATA LOADER
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

@st.cache_data(ttl=60)
def fetch_smart_data(url, key_column):
    try:
        # Load raw data
        df_raw = pd.read_csv(url, header=None, dtype=str).fillna("")
        
        # Find exactly where the table starts
        start_row = None
        for i, row in df_raw.iterrows():
            if key_column in [str(val).strip() for val in row.values]:
                start_row = i
                break
        
        if start_row is not None:
            df = df_raw.iloc[start_row:].copy()
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            # Cleanup
            df = df.dropna(axis=1, how='all')
            df = df.map(lambda x: str(x).strip() if x else "")
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# =====================================================
# 3. AUTHENTICATION LOGIC
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}

# =====================================================
# 4. ATTRACTIVE LOGIN PAGE
# =====================================================
if not st.session_state.auth["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://img.icons8.com/fluency/96/hospital.png", width=80)
        st.title("Mumbai Health Portal")
        st.subheader("Login to Access Dashboard")
        
        u_id = st.text_input("User ID", placeholder="Enter your ID")
        u_pw = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Sign In"):
            with st.spinner("Verifying..."):
                users_df = fetch_smart_data(USER_URL, "User ID")
                
                if not users_df.empty and "User ID" in users_df.columns:
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
                        st.error("Invalid credentials. Please check again.")
                else:
                    st.error("Connection failed or Data not found in Sheet.")
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 5. DASHBOARD PAGE
# =====================================================
else:
    st.sidebar.title(f"👤 {st.session_state.auth['id']}")
    st.sidebar.info(f"Role: {st.session_state.auth['role']}\n\nWard: {st.session_state.auth['ward']}")
    
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}
        st.rerun()

    st.title(f"📊 {st.session_state.auth['ward']} Ward Report")
    st.markdown("---")
    
    data_df = fetch_smart_data(DATA_URL, "Ward")
    
    if not data_df.empty:
        if st.session_state.auth["role"].lower() == "admin":
            st.write("### Master Data View")
            st.dataframe(data_df, use_container_width=True)
        else:
            filtered = data_df[data_df["Ward"] == st.session_state.auth["ward"]]
            if not filtered.empty:
                st.write(f"### Results for {st.session_state.auth['ward']} Ward")
                st.dataframe(filtered, use_container_width=True)
            else:
                st.warning("No records found for your ward.")
    else:
        st.error("Dashboard data could not be loaded.")
