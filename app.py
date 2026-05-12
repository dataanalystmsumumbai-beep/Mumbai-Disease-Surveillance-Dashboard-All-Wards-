import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

@st.cache_data(ttl=300)
def fetch_and_clean_data(url, target_keyword):
    try:
        # Load raw CSV
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        # Search for the header row
        start_row, start_col = None, None
        for r_idx, row in df_raw.iterrows():
            for c_idx, value in enumerate(row):
                if str(value).strip().lower() == target_keyword.lower():
                    start_row, start_col = r_idx, c_idx
                    break
            if start_row is not None:
                break
        
        if start_row is not None:
            df = df_raw.iloc[start_row:].copy()
            df.columns = df.iloc[0].str.strip()
            df = df[1:].reset_index(drop=True)
            
            # Remove empty columns and rows
            df = df.dropna(axis=1, how='all')
            df = df.dropna(axis=0, how='all')
            
            # --- FIX: Changed applymap to map for Pandas compatibility ---
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

# Session State
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "user_role": "", "user_ward": "", "user_id": ""})

# --- LOGIN SECTION ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    with st.form("login_form"):
        user_input = st.text_input("User ID")
        pass_input = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            users_df = fetch_and_clean_data(USER_DB_URL, "User ID")
            if not users_df.empty:
                # Login Logic
                match = users_df[(users_df["User ID"] == str(user_input).strip()) & 
                                 (users_df["Password"] == str(pass_input).strip())]
                if not match.empty:
                    st.session_state.update({
                        "logged_in": True,
                        "user_role": match.iloc[0]["Role"],
                        "user_ward": match.iloc[0]["Ward"],
                        "user_id": match.iloc[0]["User ID"]
                    })
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            else:
                st.error("Database connection failed.")

# --- DASHBOARD SECTION ---
else:
    st.sidebar.title(f"Hello, {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title(f"📊 Dashboard - {st.session_state.user_ward} Ward")
    
    main_df = fetch_and_clean_data(DATA_MAIN_URL, "Ward")
    
    if not main_df.empty:
        if str(st.session_state.user_role).lower() == "admin":
            st.write("Full Data Access")
            st.dataframe(main_df, use_container_width=True)
        else:
            # Filter by Ward
            filtered_df = main_df[main_df["Ward"] == st.session_state.user_ward]
            st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("No data found for this ward.")
