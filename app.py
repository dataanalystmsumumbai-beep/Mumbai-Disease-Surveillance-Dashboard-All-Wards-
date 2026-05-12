import streamlit as st
import pandas as pd

# =====================================================
# 1. PAGE SETUP & STYLING
# =====================================================
st.set_page_config(page_title="Mumbai Health Dashboard", layout="wide") # Changed to 'wide' for better dashboard view

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%; border-radius: 5px; height: 3em;
        background-color: #007bff; color: white; font-weight: bold;
    }
    .login-card {
        padding: 30px; border-radius: 15px; background-color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# 2. CONFIG & DATA LOADER
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

# TODO: Replace 'YOUR_HP_GID_HERE' with the actual gid of the 'data_hp' tab
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=YOUR_HP_GID_HERE"

@st.cache_data(ttl=60)
def fetch_smart_data(url, key_column):
    try:
        df_raw = pd.read_csv(url, header=None, dtype=str).fillna("")
        start_row = None
        for i, row in df_raw.iterrows():
            if key_column in [str(val).strip() for val in row.values]:
                start_row = i
                break
        if start_row is not None:
            df = df_raw.iloc[start_row:].copy()
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
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
# 4. LOGIN PAGE
# =====================================================
if not st.session_state.auth["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://img.icons8.com/fluency/96/hospital.png", width=80)
        st.title("Mumbai Health Portal")
        st.markdown("<p style='color:gray;'>Secure Access for Epidemiology Sector</p>", unsafe_allow_html=True)
        
        u_id = st.text_input("User ID", placeholder="Enter your ID")
        u_pw = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Sign In"):
            with st.spinner("Authenticating..."):
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
                        st.error("Invalid credentials. Please try again.")
                else:
                    st.error("Unable to connect to the User Database.")
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 5. DASHBOARD PAGE (WITH MULTI-TABS)
# =====================================================
else:
    # Sidebar
    st.sidebar.title(f"👤 Welcome, {st.session_state.auth['id']}")
    st.sidebar.info(f"**Role:** {st.session_state.auth['role']}\n\n**Ward:** {st.session_state.auth['ward']}")
    
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}
        st.rerun()

    # Main Dashboard Header
    st.title(f"📊 {st.session_state.auth['ward']} Ward Dashboard")
    st.markdown("---")
    
    with st.spinner("Fetching live data..."):
        data_df = fetch_smart_data(DATA_URL, "Ward")
    
    if not data_df.empty:
        # Filter data based on Role
        if st.session_state.auth["role"].lower() != "admin":
            data_df = data_df[data_df["Ward"] == st.session_state.auth["ward"]]

        if not data_df.empty:
            # Assuming there is a column named 'Disease' or 'Disease Name'
            # Let's check common names or default to the first available column if missing
            disease_col = "Disease" if "Disease" in data_df.columns else "Disease Name"
            
            if disease_col in data_df.columns:
                # Get unique diseases for dynamic tabs
                unique_diseases = data_df[disease_col].unique().tolist()
                
                # Create tabs dynamically
                tabs = st.tabs(unique_diseases)
                
                # Loop through tabs and display specific data
                for i, disease in enumerate(unique_diseases):
                    with tabs[i]:
                        st.subheader(f"{disease} Data Overview")
                        disease_data = data_df[data_df[disease_col] == disease]
                        
                        # Display Dataframe for now
                        st.dataframe(disease_data, use_container_width=True)
                        
                        # Placeholders for future steps
                        st.info("Graphs and Healthpost level data for this disease will be added here in the next step.")
            else:
                st.warning(f"Could not find a column named '{disease_col}' for creating tabs.")
                st.dataframe(data_df, use_container_width=True)
        else:
            st.warning("No records found for your ward.")
    else:
        st.error("Dashboard data could not be loaded. Please check the Google Sheet link.")
