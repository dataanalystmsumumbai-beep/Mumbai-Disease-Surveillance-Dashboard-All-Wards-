import streamlit as st
import pandas as pd

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Public Health Dashboard",
    layout="wide"
)

# =========================================================
# GOOGLE SHEET CONFIG
# =========================================================
SHEET_ID = "1NkDvWNpZCqeGIQmGCm3VPHvYV9fUzsn1Ln5sbS3l4Qk"

# USER DATABASE SHEET
USER_DB_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid=79694728"
)

# MAIN DATA SHEET
DATA_MAIN_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid=1152016550"
)

# =========================================================
# DATA FETCH FUNCTION
# =========================================================
@st.cache_data(ttl=300)
def fetch_and_clean_data(url, target_keyword):
    """
    Fetch CSV from Google Sheets and automatically detect
    table header row using target keyword.
    """

    try:
        # Read raw data
        df_raw = pd.read_csv(
            url,
            header=None,
            dtype=str
        )

        # Remove completely empty rows/columns
        df_raw = df_raw.dropna(how="all")
        df_raw = df_raw.dropna(axis=1, how="all")

        # Reset index
        df_raw = df_raw.reset_index(drop=True)

        start_row = None

        # Find header row
        for r_idx, row in df_raw.iterrows():

            row_values = (
                row.fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            if target_keyword.lower() in row_values.values:
                start_row = r_idx
                break

        # If keyword not found
        if start_row is None:
            st.error(f"Keyword '{target_keyword}' not found in sheet.")
            return pd.DataFrame()

        # Slice dataframe from header row
        df = df_raw.iloc[start_row:].reset_index(drop=True)

        # Set first row as header
        headers = (
            df.iloc[0]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df.columns = headers

        # Remove header row
        df = df[1:].reset_index(drop=True)

        # Clean again
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")

        # Remove extra spaces from all string columns
        df = df.applymap(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        return df

    except Exception as e:

        st.error("❌ Data Fetch Error")
        st.exception(e)

        return pd.DataFrame()


# =========================================================
# SESSION STATE
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = ""
    st.session_state.user_ward = ""
    st.session_state.user_id = ""

# =========================================================
# LOGIN PAGE
# =========================================================
if not st.session_state.logged_in:

    st.title("🔐 Public Health Dashboard Login")

    st.markdown("---")

    with st.form("login_form"):

        user_input = st.text_input("User ID")
        pass_input = st.text_input("Password", type="password")

        login_btn = st.form_submit_button("Sign In")

    if login_btn:

        with st.spinner("Loading User Database..."):

            users_df = fetch_and_clean_data(
                USER_DB_URL,
                "User ID"
            )

        # Debug Option
        # st.dataframe(users_df)

        if users_df.empty:

            st.error(
                "❌ Could not load User Database.\n\n"
                "Please check:\n"
                "- Google Sheet sharing permission\n"
                "- Correct Sheet GID\n"
                "- Internet connection"
            )

        else:

            required_cols = [
                "User ID",
                "Password",
                "Role",
                "Ward"
            ]

            missing_cols = [
                col for col in required_cols
                if col not in users_df.columns
            ]

            if missing_cols:

                st.error(
                    f"❌ Missing columns: {missing_cols}"
                )

                st.write("Detected Columns:")
                st.write(users_df.columns.tolist())

            else:

                # Convert to string
                users_df["User ID"] = users_df["User ID"].astype(str)
                users_df["Password"] = users_df["Password"].astype(str)

                # Match credentials
                match = users_df[
                    (users_df["User ID"] == str(user_input).strip()) &
                    (users_df["Password"] == str(pass_input).strip())
                ]

                if not match.empty:

                    st.session_state.logged_in = True
                    st.session_state.user_role = (
                        match.iloc[0]["Role"]
                    )
                    st.session_state.user_ward = (
                        match.iloc[0]["Ward"]
                    )
                    st.session_state.user_id = (
                        match.iloc[0]["User ID"]
                    )

                    st.success("✅ Login Successful")

                    st.rerun()

                else:

                    st.error("❌ Invalid Username or Password")

# =========================================================
# DASHBOARD
# =========================================================
else:

    role = st.session_state.user_role
    ward = st.session_state.user_ward
    user_id = st.session_state.user_id

    # =====================================================
    # SIDEBAR
    # =====================================================
    st.sidebar.title("👤 User Details")

    st.sidebar.write(f"**User:** {user_id}")
    st.sidebar.write(f"**Role:** {role}")
    st.sidebar.write(f"**Ward:** {ward}")

    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout"):

        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.session_state.user_ward = ""
        st.session_state.user_id = ""

        st.rerun()

    # =====================================================
    # MAIN PAGE
    # =====================================================
    st.title("📊 Public Health Dashboard")

    with st.spinner("Loading Dashboard Data..."):

        main_df = fetch_and_clean_data(
            DATA_MAIN_URL,
            "Ward"
        )

    if main_df.empty:

        st.error(
            "❌ Could not load Dashboard Data"
        )

    else:

        st.success("✅ Data Loaded Successfully")

        st.markdown("---")

        # =================================================
        # ADMIN ACCESS
        # =================================================
        if role.lower() == "admin":

            st.subheader("🛡️ Admin Access - Full Data")

            st.write(f"Total Records: {len(main_df)}")

            st.dataframe(
                main_df,
                use_container_width=True
            )

        # =================================================
        # NORMAL USER ACCESS
        # =================================================
        else:

            if "Ward" not in main_df.columns:

                st.error(
                    "❌ 'Ward' column not found in Main Data"
                )

            else:

                filtered_df = main_df[
                    main_df["Ward"].astype(str).str.strip()
                    == str(ward).strip()
                ]

                st.subheader(f"🏥 Ward {ward} Data")

                st.write(f"Total Records: {len(filtered_df)}")

                st.dataframe(
                    filtered_df,
                    use_container_width=True
                )
