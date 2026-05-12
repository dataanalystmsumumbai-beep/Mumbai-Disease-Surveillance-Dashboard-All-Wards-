import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Public Health Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"

@st.cache_data(ttl=60)
def fetch_and_clean_data(url, target_keyword):
    try:
        # Load raw CSV without headers
        df_raw = pd.read_csv(url, header=None, dtype=str).fillna("")
        
        # 1. Search for the exact cell containing target_keyword
        start_row, start_col = None, None
        for r_idx, row in df_raw.iterrows():
            for c_idx, value in enumerate(row):
                if str(value).strip().replace("\n", " ") == target_keyword:
                    start_row, start_col = r_idx, c_idx
                    break
            if start_row is not None:
                break
        
        if start_row is not None:
            # 2. Slice from that row onwards
            df = df_raw.iloc[start_row:].copy()
            
            # 3. Set the first row as headers and clean them
            df.columns = df.iloc[0].str.strip().replace("\n", " ")
            df = df[1:].reset_index(drop=True)
            
            # 4. Filter out any columns that are empty
            df = df.loc[:, df.columns.notna()]
            df = df.loc[:, ~df.columns.str.contains('^Unnamed|^nan', case=False)]
            
            # 5. Clean leading/trailing spaces from all data cells
            df = df.map(lambda x: str(x).strip() if x else "")
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

# Session State Setup
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "user_role": "", "user_ward": "", "user_id": ""})

# --- LOGIN SECTION ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    
    with st.form("login_form"):
        u_input = st.text_input("User ID").strip()
        p_input = st.text_input("Password", type="password").strip()
        submit = st.form_submit_button("Sign In")
        
        if submit:
            # Look for the table starting with 'User ID'
            users_df = fetch_and_clean_data(USER_DB_URL, "User ID")
            
            if not users_df.empty:
                # Debugging view (Only if login fails repeatedly)
                # st.write("Columns found:", users_df.columns.tolist())
                
                # Check credentials
                match = users_df[
                    (users_df["User ID"] == u_input) & 
                    (users_df["Password"] == p_input)
                ]
                
                if not match.empty:
                    st.session_state.update({
                        "logged_in": True,
                        "user_role": match.iloc[0]["Role"],
                        "user_ward": match.iloc[0]["Ward"],
                        "user_id": match.iloc[0]["User ID"]
                    })
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. Please check the sheet data.")
            else:
                st.error("Could not find 'User ID' table in the sheet. Check GID and cell D4.")

# --- DASHBOARD SECTION ---
else:
    st.sidebar.title(f"User: {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title(f"📊 Dashboard - {st.session_state.user_ward} Ward")
    
    # Load Main Data searching for 'Ward' keyword
    main_df = fetch_and_clean_data(DATA_MAIN_URL, "Ward")
    
    if not main_df.empty:
        if str(st.session_state.user_role).lower() == "admin":
            st.subheader("Master Data (Admin View)")
            st.dataframe(main_df, use_container_width=True)
        else:
            st.subheader(f"Records for {st.session_state.user_ward}")
            if "Ward" in main_df.columns:
                filtered = main_df[main_df["Ward"] == st.session_state.user_ward]
                st.dataframe(filtered, use_container_width=True)
            else:
                st.warning("Data loaded, but 'Ward' column was not identified.")
    else:
        st.info("No dashboard data found in the linked sheet.")
