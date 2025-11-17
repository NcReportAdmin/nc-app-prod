import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

def get_google_sheets_client():
    """
    Initialize Google Sheets client using service account credentials
    """
    try:
        # Get credentials from Streamlit secrets
        credentials_dict = st.secrets["google_service_account"]
        
        # Define the scope
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Create credentials
        credentials = Credentials.from_service_account_info(
            credentials_dict, 
            scopes=scope
        )
        
        # Initialize the client
        client = gspread.authorize(credentials)
        return client
    
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        st.error("Please check your Google service account configuration.")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_permissions():
    """
    Load permissions from Google Sheets
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        # Get the Google Sheet ID from secrets
        sheet_id = st.secrets["mNC_account_master_sheet_id"]
        
        # Open the sheet
        sheet = client.open_by_key(sheet_id)
        
        # Get the first worksheet (or specify by name)
        worksheet = sheet.get_worksheet(0)  # First sheet
        # Or use: worksheet = sheet.worksheet("Sheet1")  # By name
        
        # Get all records
        records = worksheet.get_all_records()
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Ensure email column is lowercase for consistency
        if 'email' in df.columns:
            df['email'] = df['email'].str.lower().str.strip()
        
        return df
    
    except Exception as e:
        st.error(f"Failed to load permissions from Google Sheets: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_sheets(sheet_id, sheet_name=None, header_row=0):
    """
    Generic function to load data from Google Sheets
    Args:
        sheet_id: Google Sheet ID
        sheet_name: Name of the worksheet (optional, uses first sheet if None)
        header_row: Row number to use as header (0-indexed)
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        # Open the sheet
        sheet = client.open_by_key(sheet_id)
        
        # Get the specified worksheet
        if sheet_name:
            worksheet = sheet.worksheet(sheet_name)
        else:
            worksheet = sheet.get_worksheet(0)
        
        # Get all records
        all_data = worksheet.get_all_values()
        
        # Convert to DataFrame with specified header row
        if len(all_data) > header_row:
            df = pd.DataFrame(all_data[header_row + 1:], columns=all_data[header_row])
            
            # Clean up empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {str(e)}")
        return pd.DataFrame()

# user_id generation Helper function
def user_id(email: str):
    """
    Generates Gen_app_id as:
    62 + YYYY + first4(email) + MMDD
    Example:
        email 'john.doe@x.com', date 2025-02-03
        -> 622025john0203
    """

    # 1. First 4 characters of email (letters/numbers only)
    clean_email = "".join([c for c in email if c.isalnum()])
    prefix = clean_email[:4].lower().ljust(4, "x")  # ensures at least 4 chars

    # 2. Today's date
    today = datetime.now(pacific)
    yyyy = today.strftime("%Y")
    mmdd = today.strftime("%m%d")

    # 3. Combine
    return f"62{yyyy}{prefix}{mmdd}"


# Streamlit UI
st.set_page_config(page_title="Nature Counter Journal Entry (via Web)", layout="centered")

# Display logo
col1, col2, col3 = st.columns([1.5,2,1])
with col2:
    st.image("logo.png", width=180)

# Timezone San Francisco time (PT)
pacific = pytz.timezone("America/Los_Angeles")

if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None
    st.session_state["user_role"] = None


# Centered Title
st.markdown("<h1 style='text-align: center; font-size: 36px;'>🌿 Nature Counter Journal Entry (via Web)</h1>", unsafe_allow_html=True)

# Add security notice
st.markdown("### Secure Login Portal")
# st.info("🔒 This dashboard uses secure authentication via Google Sheets.")

email = st.text_input("Enter your email to login", placeholder="namexyz@gmail.com").strip().lower()

if email:
    with st.spinner("Authenticating..."):
        permissions = load_permissions()
    
    if permissions.empty:
        st.error("Unable to load permissions. Please contact your administrator.")
        st.stop()
    
    # Check if email exists
    match = permissions[permissions["email"] == email]

    # ---------------------- EXISTING USER ----------------------
    if not match.empty:
        user_data = match.iloc[0]
        st.session_state["user_email"] = email
        st.session_state["user_role"] = user_data["role"]
        st.session_state["user_name"] = user_data.get("ho_username", "User")
        st.session_state["authenticated"] = True

        st.success(f"Welcome back, {st.session_state['user_name']}!")
        #st.info("You are now logged in.")
        #st.write(f"**You are now Logged in as:** {email} | **Role:** {user_data['role']}")
    
    # ---------------------- NEW USER → REGISTRATION ----------------------
    else:
        st.warning("Email not found. Please register.")

        with st.form("registration_form"):
            username = st.text_input("Your Name")
            preferred_lang = st.selectbox("Preferred Language", ["en", "es", "ko", "hi"])
            
            submit_reg = st.form_submit_button("Register")

            if submit_reg:
                if not username:
                    st.error("Name is required.")
                    st.stop()

                # ---- Append to registration Google Sheet ----
                try:
                    client = get_google_sheets_client()
                    reg_sheet_id = st.secrets["mNC_account_master_sheet_id"]
                    reg_ws = client.open_by_key(reg_sheet_id).worksheet("Sheet1")
                    generated_user_id = user_id(email)

                    new_row = [
                        email,
                        username,
                        "user",        # role
                        "", # Gen_app_id
                        generated_user_id, # user_id
                        "", #LMS_app_id
                        preferred_lang,
                        datetime.now(pacific).strftime("%Y-%m-%d"),  # NC date
                        "", "", "", "", "",                  # HO, LMS, App4, App5, group_id
                        "Journal Entry (via Web)",                                # source
                        datetime.now(pacific).strftime("%Y-%m-%d")   # date merged
                    ]

                    reg_ws.append_row(new_row)

                    st.success("Registration successful! Logging you in...")

                    # Auto-login
                    st.session_state["user_email"] = email
                    st.session_state["user_role"] = "user"
                    st.session_state["user_name"] = username
                    st.session_state["authenticated"] = True

                    st.rerun()
                    st.success(f"Welcome {st.session_state['user_name']}!")

                except Exception as e:
                    st.error(f"Failed to register: {e}")
    
    # if match.empty:
    #     st.error("Email not found. Access denied.")
    #     st.error("Please contact your administrator if you believe this is an error.")
    # else:
    #     # Store user data in session state
    #     user_data = match.iloc[0]
    #     st.session_state["user_email"] = email
    #     st.session_state["user_role"] = user_data["role"]
    #     st.session_state["user_name"] = user_data.get("name", "User")
    #     st.session_state["authenticated"] = True

if st.session_state['user_name'] is not None:        
    st.info("Please use the sidebar to access the App.")
st.write("---")     
st.write(f"**You are Logged in as:** {st.session_state['user_name']} | **Role:** {st.session_state["user_role"]}")
# Show logout button if authenticated
if st.session_state.get("authenticated", False):
    
    if st.button("🚪 Logout"):
        for key in ["user_email", "user_role", "user_name", "authenticated"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("You have been logged out.")
        st.rerun()

# Debug info for development (remove in production)
# if st.checkbox("Show Debug Info (Development Only)"):
#     st.write("**Session State:**", st.session_state)
    
#     # Show available users (be careful with this in production!)
#     if st.checkbox("Show Available Users (Admin Only)"):
#         permissions = load_permissions()
#         if not permissions.empty:
#             st.write("**Registered Users:**")
#             # Only show emails and roles, not sensitive data
#             st.dataframe(permissions[['email', 'role']])