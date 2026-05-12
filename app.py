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
    .disease-header { color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 5px; margin-top: 20px; }
    .summary-header { color: #28a745; border-bottom: 2px solid #28a745; padding-bottom: 5px; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# 2. CONFIG & DATA LOADER
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1903143728"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1122298238"

DISEASE_LIST = ["MALARIA", "DENGUE", "CHIKUNGUNYA", "LEPTO", "GASTRO", "HEPATITIS", "H1N1", "Typhoid"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

@st.cache_data(ttl=60)
def fetch_user_data(url):
    try:
        df = pd.read_csv(url, dtype=str).fillna("")
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def fetch_and_parse_disease_data(url):
    try:
        df_raw = pd.read_csv(url, header=None, dtype=str).fillna("")
        disease_dataframes = {}
        current_disease = None
        start_idx = None

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

        parsed_data = {}
        for disease, indices in disease_dataframes.items():
            df_slice = df_raw.iloc[indices["start"]:indices["end"]].copy()
            header_idx = None
            for j, row in df_slice.iterrows():
                row_vals = [str(val).strip() for val in row.values]
                if "Ward" in row_vals or "HP Name" in row_vals:
                    header_idx = j
                    break
            
            if header_idx is not None:
                df_clean = df_raw.iloc[header_idx:].copy()
                columns = df_raw.iloc[header_idx].astype(str).str.strip().tolist()
                year_map = {0: "2026", 1: "2023", 2: "2024", 3: "2025", 4: "2022"} 
                
                unique_cols = []
                seen = {}
                for c in columns:
                    if not c:
                        unique_cols.append("")
                        continue
                    count = seen.get(c, 0)
                    seen[c] = count + 1
                    if c.lower() in ["ward", "sr no.", "hp name"]:
                        unique_cols.append(c if count == 0 else f"{c}_{count}")
                    else:
                        unique_cols.append(f"{c} {year_map.get(count, '')}".strip())
                
                df_clean.columns = unique_cols
                df_clean = df_clean[1:].reset_index(drop=True)
                mask = df_clean.iloc[:, 0:4].apply(lambda x: x.astype(str).str.contains("Grand Total", case=False, na=False)).any(axis=1)
                total_idx = df_clean[mask].index.min()
                if pd.notna(total_idx):
                    df_clean = df_clean.iloc[:total_idx+1]
                
                df_clean = df_clean.loc[:, df_clean.columns != ""]
                parsed_data[disease] = df_clean
        return parsed_data
    except:
        return {}

# =====================================================
# 3. AUTHENTICATION
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}

if not st.session_state.auth["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://img.icons8.com/fluency/96/hospital.png", width=80)
        st.title("Mumbai Health Portal")
        u_id = st.text_input("User ID")
        u_pw = st.text_input("Password", type="password")
        if st.button("Sign In"):
            st.cache_data.clear()
            users_df = fetch_user_data(USER_URL)
            if not users_df.empty:
                match = users_df[(users_df["User ID"] == u_id) & (users_df["Password"] == u_pw)]
                if not match.empty:
                    st.session_state.auth = {"logged_in": True, "id": match.iloc[0]["User ID"], "ward": match.iloc[0]["Ward"], "role": match.iloc[0]["Role"]}
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 4. DASHBOARD
# =====================================================
else:
    st.sidebar.title(f"👤 {st.session_state.auth['id']}")
    st.sidebar.info(f"Ward: {st.session_state.auth['ward']}")
    
    # Global Month Filter
    selected_month = st.sidebar.selectbox("Select Month for Summary", MONTHS)
    
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False, "id": "", "ward": "", "role": ""}
        st.rerun()

    st.title(f"📊 {st.session_state.auth['ward']} Dashboard")
    
    with st.spinner("Fetching data..."):
        parsed_ward = fetch_and_parse_disease_data(DATA_URL)
        parsed_hp = fetch_and_parse_disease_data(DATA_HP_URL)
    
    if parsed_ward:
        tabs = st.tabs(list(parsed_ward.keys()))
        for i, disease in enumerate(parsed_ward.keys()):
            with tabs[i]:
                # Section 1: Ward Level Table
                st.markdown(f"<h3 class='disease-header'>{disease} - Ward Wise Report</h3>", unsafe_allow_html=True)
                df_w = parsed_ward[disease]
                if st.session_state.auth["role"].lower() != "admin":
                    df_w = df_w[(df_w["Ward"] == st.session_state.auth["ward"]) | (df_w["Ward"].str.contains("Total", case=False, na=False))]
                st.dataframe(df_w, use_container_width=True)

                # Section 2: Health Post Level Dynamic Summary
                st.markdown(f"<h3 class='summary-header'>{disease} - Health Post Summary ({selected_month})</h3>", unsafe_allow_html=True)
                if disease in parsed_hp:
                    df_h = parsed_hp[disease]
                    # Filter by Ward
                    if st.session_state.auth["role"].lower() != "admin":
                        df_h = df_h[df_h["Ward"] == st.session_state.auth["ward"]]
                    
                    if not df_h.empty:
                        # Identify columns for the selected month across years
                        # Mapping: We need columns like "Jan 2023", "Jan 2024", etc.
                        cols_to_show = ["HP Name"]
                        target_years = ["2023", "2024", "2025", "2026"]
                        for yr in target_years:
                            col_name = f"{selected_month} {yr}"
                            if col_name in df_h.columns:
                                cols_to_show.append(col_name)
                        
                        summary_df = df_h[cols_to_show].reset_index(drop=True)
                        st.dataframe(summary_df, use_container_width=True)
                    else:
                        st.warning(f"No Health Post data found for {st.session_state.auth['ward']}.")
                else:
                    st.info(f"Detailed HP data for {disease} is not available.")
