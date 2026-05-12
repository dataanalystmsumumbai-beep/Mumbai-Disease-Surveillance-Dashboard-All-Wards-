import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
# 1. PAGE SETUP & STYLING
# =====================================================
st.set_page_config(page_title="Mumbai Health Dashboard", layout="wide")

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
    .disease-header { color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# 2. CONFIG & DATA LOADER
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1903143728"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1122298238"

# List of diseases as per your Excel sheet
DISEASE_LIST = ["MALARIA", "DENGUE", "CHIKUNGUNYA", "LEPTO", "GASTRO", "HEPATITIS", "H1N1", "Typhoid"]

@st.cache_data(ttl=60)
def fetch_user_data(url):
    try:
        df = pd.read_csv(url, dtype=str).fillna("")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def fetch_and_parse_disease_data(url):
    """
    Custom Parser with Year mapping to read horizontal years perfectly.
    """
    try:
        df_raw = pd.read_csv(url, header=None, dtype=str).fillna("")
        
        disease_dataframes = {}
        current_disease = None
        start_idx = None

        # Find where each disease block starts
        for i, row in df_raw.iterrows():
            row_values = [str(val).strip().upper() for val in row.values]
            for disease in DISEASE_LIST:
                if disease.upper() in row_values:
                    if current_disease:
                        disease_dataframes[current_disease] = {"start": start_idx, "end": i-1}
                    current_disease = disease
                    start_idx = i
                    break
                    
        if current_disease:
            disease_dataframes[current_disease] = {"start": start_idx, "end": len(df_raw)}

        # Extract and format data for each disease
        parsed_data = {}
        for disease, indices in disease_dataframes.items():
            df_slice = df_raw.iloc[indices["start"]:indices["end"]].copy()
            
            header_idx = None
            for j, row in df_slice.iterrows():
                if "Ward" in [str(val).strip() for val in row.values]:
                    header_idx = j
                    break
            
            if header_idx is not None:
                df_clean = df_raw.iloc[header_idx:].copy()
                
                # --- SMART YEAR MAPPING LOGIC ---
                columns = df_raw.iloc[header_idx].astype(str).str.strip().tolist()
                year_map = {0: "2026", 1: "2025", 2: "2024", 3: "2023", 4: "2022"}
                unique_cols = []
                seen = {}
                
                for c in columns:
                    if not c:
                        unique_cols.append("")
                        continue
                    
                    count = seen.get(c, 0)
                    seen[c] = count + 1
                    
                    # Keep core columns names simple for the first occurrence so we can filter easily
                    if c.lower() in ["ward", "sr no.", "hp name"]:
                        if count == 0:
                            unique_cols.append(c) 
                        else:
                            unique_cols.append(f"{c} {year_map.get(count, '')}".strip())
                    else:
                        # Append the year to months and totals (e.g., Jan 2026, Total 2025)
                        unique_cols.append(f"{c} {year_map.get(count, '')}".strip())
                
                df_clean.columns = unique_cols
                df_clean = df_clean[1:].reset_index(drop=True)
                
                # Stop reading at the "Total" row using the first 3 columns
                mask = df_clean.iloc[:, 0:3].apply(lambda x: x.astype(str).str.contains("Total", case=False, na=False)).any(axis=1)
                total_idx = df_clean[mask].index.min()
                if pd.notna(total_idx):
                    df_clean = df_clean.iloc[:total_idx+1]
                
                # Remove empty columns that separated the years
                df_clean = df_clean.loc[:, df_clean.columns != ""]
                df_clean = df_clean.loc[:, df_clean.columns.notna()]
                
                parsed_data[disease] = df_clean
                
        return parsed_data

    except Exception as e:
        st.error(f"Data Fetching Error: {e}")
        return {}

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
                st.cache_data.clear() 
                users_df = fetch_user_data(USER_URL)
                
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
# 5. DASHBOARD PAGE (WITH CUSTOM DISEASE TABS)
# =====================================================
else:
    st.sidebar.title(f"👤 Welcome, {st.session_state.auth['id']}")
    st.sidebar.info(f"**Role:** {st.session_state.auth['role']}\n\n**Ward:** {st.session_state.auth['ward']}")
    
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}
        st.rerun()

    st.title(f"📊 {st.session_state.auth['ward']} Ward Dashboard")
    st.markdown("---")
    
    with st.spinner("Analyzing Complex Grid Data..."):
        parsed_diseases = fetch_and_parse_disease_data(DATA_URL)
    
    if parsed_diseases:
        disease_names = list(parsed_diseases.keys())
        tabs = st.tabs(disease_names)
        
        for i, disease in enumerate(disease_names):
            with tabs[i]:
                st.markdown(f"<h3 class='disease-header'>{disease} Report</h3>", unsafe_allow_html=True)
                
                df_disease = parsed_diseases[disease]
                
                # Filter by Ward if user is not Admin
                if st.session_state.auth["role"].lower() != "admin":
                    if "Ward" in df_disease.columns:
                        # Display user's ward along with the Total row
                        df_disease = df_disease[(df_disease["Ward"] == st.session_state.auth["ward"]) | (df_disease["Ward"].str.contains("Total", case=False, na=False))]
                
                st.dataframe(df_disease, use_container_width=True)
                
    else:
        st.error("Could not parse the disease data from the Google Sheet. Please check the format.")
