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
# 3. DATA PARSER LOGIC (Complex Grid Format)
# =====================================================
@st.cache_data(ttl=60)
def fetch_raw_csv(url):
    try:
        return pd.read_csv(url, header=None, dtype=str).fillna("")
    except:
        return pd.DataFrame()

def get_disease_block(df_raw, disease_name, selected_year):
    """
    Finds the specific disease block and ensures unique column names.
    """
    disease_row = None
    for idx, row in df_raw.iterrows():
        if disease_name.upper() in [str(v).strip().upper() for v in row.values]:
            disease_row = idx
            break
    
    if disease_row is None: return pd.DataFrame()

    header_row_idx = None
    for idx in range(disease_row, disease_row + 10): 
        if "Ward" in [str(v).strip() for v in df_raw.iloc[idx].values]:
            header_row_idx = idx
            break
            
    if header_row_idx is None: return pd.DataFrame()

    df_block = df_raw.iloc[header_row_idx:].copy()
    
    # Mapping horizontal years
    year_col_ranges = {
        "2026": (0, 14),   
        "2025": (16, 30),
        "2024": (31, 45),
        "2023": (46, 60)
    }
    
    start_col, end_col = year_col_ranges.get(selected_year, (0, 14))
    info_cols = [0, 1, 2] 
    data_cols = list(range(start_col, end_col))
    final_cols = list(dict.fromkeys(info_cols + data_cols)) 
    
    df_final = df_block.iloc[:, final_cols].copy()
    
    # --- UNIQUE COLUMN NAMES FIX ---
    cols = df_final.iloc[0].str.strip().tolist()
    new_cols = []
    col_counts = {}
    for item in cols:
        if not item: item = "Unnamed"
        if item in col_counts:
            col_counts[item] += 1
            new_cols.append(f"{item}.{col_counts[item]}")
        else:
            col_counts[item] = 0
            new_cols.append(item)
    
    df_final.columns = new_cols
    
    df_final = df_final[1:].reset_index(drop=True)
    df_final = df_final[df_final.iloc[:, 0] != ""]
    
    # Total row filter
    mask = df_final.iloc[:, 0:3].apply(lambda x: x.astype(str).str.contains("Total", case=False, na=False)).any(axis=1)
    total_idx = df_final[mask].index.min()
    if pd.notna(total_idx):
        df_final = df_final.iloc[:total_idx+1]

    return df_final

# =====================================================
# 4. AUTHENTICATION (Login Logic)
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "ward": "", "role": ""}

if not st.session_state.auth["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://img.icons8.com/fluency/96/hospital.png", width=80)
        st.title("Mumbai Health Portal")
        u_id = st.text_input("User ID", placeholder="ID Enter करा")
        u_pw = st.text_input("Password", type="password", placeholder="Password Enter करा")
        if st.button("Sign In"):
            users_df = fetch_raw_csv(USER_URL)
            if not users_df.empty:
                users_df.columns = users_df.iloc[0].str.strip()
                users_df = users_df[1:]
                match = users_df[(users_df["User ID"] == u_id) & (users_df["Password"] == u_pw)]
                if not match.empty:
                    st.session_state.auth = {"logged_in": True, "ward": match.iloc[0]["Ward"], "role": match.iloc[0]["Role"]}
                    st.rerun()
                else: st.error("Invalid credentials")
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 5. DASHBOARD MAIN (Output Area)
# =====================================================
else:
    st.sidebar.title(f"👤 {st.session_state.auth['ward']} Ward")
    sel_disease = st.sidebar.selectbox("Select Disease", DISEASES)
    sel_year = st.sidebar.selectbox("Select Year", YEARS)
    
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False}
        st.rerun()

    st.markdown(f"<h2 class='disease-header'>{sel_disease} - {sel_year}</h2>", unsafe_allow_html=True)

    raw_hp_data = fetch_raw_csv(DATA_HP_URL)
    
    if not raw_hp_data.empty:
        df_display = get_disease_block(raw_hp_data, sel_disease, sel_year)
        
        if not df_display.empty:
            # Filter for User's Ward
            ward_col = "Ward" if "Ward" in df_display.columns else df_display.columns[1]
            if st.session_state.auth["role"].lower() != "admin":
                df_display = df_display[df_display[ward_col] == st.session_state.auth["ward"]]
            
            # HP Filtering
            hp_list = df_display["HP Name"].unique().tolist()
            sel_hp = st.selectbox("Select Health Post", ["All Health Posts"] + hp_list)
            
            final_df = df_display.copy()
            if sel_hp != "All Health Posts":
                final_df = final_df[final_df["HP Name"] == sel_hp]
            
            st.dataframe(final_df, use_container_width=True)
            
            # Quick Metric
            total_col = "Total" if "Total" in final_df.columns else (final_df.columns[-1])
            total_cases = pd.to_numeric(final_df[total_col], errors='coerce').sum()
            st.metric(label=f"Total Cases", value=int(total_cases))
            
        else:
            st.warning("Data not found for this selection.")
    else:
        st.error("Could not fetch data from Google Sheet.")
