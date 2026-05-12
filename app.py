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
    .filter-container {
        padding: 20px; border-radius: 10px; background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .disease-header { color: #d9534f; font-weight: bold; border-bottom: 2px solid #d9534f; }
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# 2. CONFIG & LIVE DATA CONNECTORS
# =====================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1903143728"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1122298238"

DISEASES = ["MALARIA", "DENGUE", "CHIKUNGUNYA", "LEPTO", "GASTRO", "HEPATITIS", "H1N1", "TYPHOID"]
YEARS = ["2026", "2025", "2024", "2023"]

# =====================================================
# 3. CORE LOGIC: GRID DATA PARSER
# =====================================================
@st.cache_data(ttl=60)
def fetch_raw_csv(url):
    try:
        return pd.read_csv(url, header=None, dtype=str).fillna("")
    except:
        return pd.DataFrame()

def get_disease_block(df_raw, disease_name, selected_year):
    """
    Finds the specific disease block and matches the correct year columns.
    """
    # 1. Find the row index where disease name is mentioned
    disease_row = None
    for idx, row in df_raw.iterrows():
        if disease_name.upper() in [str(v).strip().upper() for v in row.values]:
            disease_row = idx
            break
    
    if disease_row is None: return pd.DataFrame()

    # 2. Find the 'Ward' header row under that disease
    header_row_idx = None
    for idx in range(disease_row, disease_row + 10): # Look 10 rows down
        if "Ward" in [str(v).strip() for v in df_raw.iloc[idx].values]:
            header_row_idx = idx
            break
            
    if header_row_idx is None: return pd.DataFrame()

    # 3. Process the table
    df_block = df_raw.iloc[header_row_idx:].copy()
    
    # Identify Year Blocks (Since years are side-by-side)
    # 2026: Col A-M, 2025: Col Q-AD, etc. (Mapping manually based on your Sheet structure)
    year_col_ranges = {
        "2026": (0, 14),   # Approx columns based on your screenshot
        "2025": (16, 30),
        "2024": (31, 45),
        "2023": (46, 60)
    }
    
    start_col, end_col = year_col_ranges.get(selected_year, (0, 14))
    
    # Extract only the selected year columns + Ward/HP Name info
    # We keep Ward (Col 1), HP Name (Col 2/3) depending on the sheet
    info_cols = [0, 1, 2] # Ward, HP Name columns
    data_cols = list(range(start_col, end_col))
    
    final_cols = list(dict.fromkeys(info_cols + data_cols)) # Unique combined list
    df_final = df_block.iloc[:, final_cols].copy()
    
    # Set headers
    df_final.columns = df_final.iloc[0].str.strip()
    df_final = df_final[1:].reset_index(drop=True)
    
    # Clean up empty rows/totals
    df_final = df_final[df_final.iloc[:, 0] != ""]
    return df_final

# =====================================================
# 4. AUTHENTICATION
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "ward": "", "role": ""}

if not st.session_state.auth["logged_in"]:
    # Login Logic (simplified for testing)
    st.title("🏥 Mumbai Health Portal")
    u_id = st.text_input("User ID")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        users_df = fetch_raw_csv(USER_URL)
        # Check against User ID sheet (assuming Row 1 is header)
        if not users_df.empty:
            users_df.columns = users_df.iloc[0]
            users_df = users_df[1:]
            match = users_df[(users_df["User ID"] == u_id) & (users_df["Password"] == u_pw)]
            if not match.empty:
                st.session_state.auth = {"logged_in": True, "ward": match.iloc[0]["Ward"], "role": match.iloc[0]["Role"]}
                st.rerun()
            else: st.error("Invalid credentials")

# =====================================================
# 5. DASHBOARD MAIN
# =====================================================
else:
    # Sidebar Filters
    st.sidebar.title(f"👤 Ward: {st.session_state.auth['ward']}")
    sel_disease = st.sidebar.selectbox("Select Disease", DISEASES)
    sel_year = st.sidebar.selectbox("Select Year", YEARS)
    
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False}
        st.rerun()

    st.markdown(f"<h2 class='disease-header'>{sel_disease} Report - {sel_year}</h2>", unsafe_allow_html=True)

    # Fetch Data
    raw_hp_data = fetch_raw_csv(DATA_HP_URL)
    
    if not raw_hp_data.empty:
        # Get processed block
        df_display = get_disease_block(raw_hp_data, sel_disease, sel_year)
        
        if not df_display.empty:
            # Filter by User's Ward
            if st.session_state.auth["role"].lower() != "admin":
                # Ensure we find the Ward column correctly
                ward_col = "Ward" if "Ward" in df_display.columns else df_display.columns[1]
                df_display = df_display[df_display[ward_col] == st.session_state.auth["ward"]]
            
            # HP Selector
            all_hps = ["All Health Posts"] + df_display["HP Name"].unique().tolist()
            sel_hp = st.selectbox("Filter by Health Post", all_hps)
            
            if sel_hp != "All Health Posts":
                df_display = df_display[df_display["HP Name"] == sel_hp]
            
            # Final Output
            st.write(f"### Records for {st.session_state.auth['ward']} Ward")
            st.dataframe(df_display, use_container_width=True)
            
            # Simple Summary Metric
            if "Total" in df_display.columns:
                total_cases = pd.to_numeric(df_display["Total"], errors='coerce').sum()
                st.metric(label=f"Total {sel_disease} Cases", value=int(total_cases))
        else:
            st.warning("No data found for the selected criteria.")
