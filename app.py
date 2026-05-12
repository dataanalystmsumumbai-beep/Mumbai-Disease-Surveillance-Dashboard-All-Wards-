import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Disease Surveillance Dashboard", layout="wide")

# Google Sheet Configuration
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# CSV Export Links
USER_DB_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=79694728"
DATA_MAIN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1152016550"
DATA_HP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1496660724"
DATA_BACKEND_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1815143324"

def get_cleaned_df(url, keyword):
    """
    Downloads CSV and finds the header row automatically by searching for a keyword.
    Removes empty leading/trailing rows and columns.
    """
    try:
        df_raw = pd.read_csv(url, header=None)
        
        # 1. Find the row index that contains our keyword (e.g., 'User ID' or 'Ward')
        header_row_idx = None
        for i, row in df_raw.iterrows():
            if row.astype(str).str.contains(keyword, case=False, na=False).any():
                header_row_idx = i
                break
        
        if header_row_idx is None:
            return pd.DataFrame()

        # 2. Set that row as the header
        df = df_raw.iloc[header_row_idx:].copy()
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

        # 3. Clean column names (strip spaces, handle NaNs)
        df.columns = [str(c).strip() if pd.notna(c) else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
        
        # 4. Remove empty columns/rows
        df = df.loc[:, ~df.columns.str.contains('Unnamed')]
        df = df.dropna(how='all').reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"Error reading data: {e}")
        return pd.DataFrame()

def find_column(df, target_name):
    """Finds a column name that contains the target string, ignoring case."""
    for col in df.columns:
        if target_name.lower() in col.lower():
            return col
    return None

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_ward'] = None

# --- LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔐 Mumbai Disease Surveillance Login")
    
    with st.form("login_form"):
        uid_input = st.text_input("Enter User ID")
        pwd_input = st.text_input("Enter Password", type="password")
        login_submit = st.form_submit_button("Login")

        if login_submit:
            # We look for 'User ID' keyword to find the header row
            users_df = get_cleaned_df(USER_DB_URL, "User ID")
            
            if not users_df.empty:
                # Find the actual column names in the sheet
                id_col = find_column(users_df, "User ID")
                pw_col = find_column(users_df, "Password")
                role_col = find_column(users_df, "Role")
                ward_col = find_column(users_df, "Ward")

                if id_col and pw_col:
                    # Validate login
                    user_match = users_df[(users_df[id_col].astype(str) == str(uid_input)) & 
                                          (users_df[pw_col].astype(str) == str(pwd_input))]
                    
                    if not user_match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = user_match[role_col].values[0] if role_col else "User"
                        st.session_state['user_ward'] = user_match[ward_col].values[0] if ward_col else "Unknown"
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")
                else:
                    st.error("Sheet Structure Error: Could not find 'User ID' or 'Password' columns.")
            else:
                st.error("Could not load User Database. Please check your Google Sheet sharing settings.")

# --- DASHBOARD ---
else:
    role = st.session_state['user_role']
    ward = st.session_state['user_ward']

    st.sidebar.success(f"Login Success: {role}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    if role == "Admin":
        st.title("🏆 Master Surveillance Dashboard")
        
        st.subheader("Disease Trends (PPT Backend)")
        backend_df = get_cleaned_df(DATA_BACKEND_URL, "Disease")
        st.dataframe(backend_df, use_container_width=True)

        st.subheader("Global Ward Data")
        main_df = get_cleaned_df(DATA_MAIN_URL, "Ward")
        if not main_df.empty:
            ward_col = find_column(main_df, "Ward")
            if ward_col:
                selected_ward = st.selectbox("Filter by Ward", main_df[ward_col].unique())
                st.dataframe(main_df[main_df[ward_col] == selected_ward])

    else:
        st.title(f"📍 Ward Report: {ward}")
        
        main_df = get_cleaned_df(DATA_MAIN_URL, "Ward")
        ward_col = find_column(main_df, "Ward")
        if not main_df.empty and ward_col:
            ward_data = main_df[main_df[ward_col] == ward]
            st.subheader(f"Current Statistics for Ward {ward}")
            st.dataframe(ward_data, use_container_width=True)

        hp_df = get_cleaned_df(DATA_HP_URL, "HP Name")
        hp_ward_col = find_column(hp_df, "Ward")
        if not hp_df.empty and hp_ward_col:
            hp_ward_data = hp_df[hp_df[hp_ward_col] == ward]
            st.subheader(f"Health Post Details - {ward}")
            st.dataframe(hp_ward_data, use_container_width=True)
