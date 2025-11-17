# ===============================================================
# 🌿 NATURE JOURNAL — NO FORM (Live Updating)
# ===============================================================

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import requests
import pytz


# ================================
# 1. Google Sheets Auth
# ================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"], scopes=scope
)
client = gspread.authorize(creds)

# Journal sheet
JOURNAL_SHEET_ID = st.secrets["journal_data_sheet_id"]
journal_ws = client.open_by_key(JOURNAL_SHEET_ID).worksheet("Journal")
journal_df = pd.DataFrame(journal_ws.get_all_records())


# ================================
# 2. Helper: Find column in DF
# ================================
def col(df, name):
    for c in df.columns:
        if c.strip().lower() == name.strip().lower():
            return c
    return None

zip_col = col(journal_df, "Zip")
city_col = col(journal_df, "City")
state_col = col(journal_df, "State")
country_col = col(journal_df, "Country")
name_col = col(journal_df, "n_Name")

existing_places = sorted([p for p in journal_df[name_col].unique() if p])


# =====================================
# 3. Session State Initialization
# =====================================
DEFAULT_FIELDS = ["n_name", "zip_code", "city", "state", "country"]

for f in DEFAULT_FIELDS:
    st.session_state.setdefault(f, "")

st.session_state.setdefault("last_place_choice", "")


# =====================================
# 4. Cached ZIP Lookup
# =====================================
@st.cache_data(ttl=86400)
def lookup_zip(zip_code):
    try:
        r = requests.get(f"https://api.zippopotam.us/us/{zip_code}")
        if r.status_code == 200:
            data = r.json()
            cities = sorted({p["place name"] for p in data["places"]})
            return {
                "country": data["country"],
                "state": data["places"][0]["state abbreviation"],
                "cities": cities
            }
    except:
        return None
    return None


# =====================================
# 5. Simulated Login
# =====================================
# st.session_state.setdefault("user_email", "test@example.com")
# st.session_state.setdefault("user_name", "Test User")

if st.session_state['user_name'] is not None:
        
    # =====================================
    # 6. LIVE Journal UI
    # =====================================
    st.markdown(
        "<h1 style='font-size: 32px;'>🌿 Nature Counter Journal Entry (via Web)</h1>",
        unsafe_allow_html=True
    )

    st.write(f"**You are Logged in as:** {st.session_state['user_name']} | **Role:** {st.session_state["user_role"]}")
    # ========================================================
    # Date,Time and Duration FIELDS
    # ========================================================

    # Timezone San Francisco time (PT)
    pacific = pytz.timezone("America/Los_Angeles")

    ts_date = st.date_input("Select date", value=datetime.now(pacific))
    ts_time = st.time_input("Select time", value=datetime.now(pacific).time())
    n_duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440, step=5,key="duration_field")

    # -------------------------------
    # LIVE PLACE PICKER (Instant Update)
    # -------------------------------
    place_selection = st.selectbox(
        "Nature Place Name",
        ["", "-- Add New Place --"] + existing_places,
        index=0,
        key="place_select"
    )

    # Reset when place changes
    if place_selection != st.session_state.last_place_choice:
        for f in ["zip_code", "city", "state", "country","n_name"]:
            st.session_state[f] = ""
        st.session_state.last_place_choice = place_selection


    # ========================================================
    # CASE 1 — Existing Place (auto-fill instantly)
    # ========================================================
    if place_selection not in ["", "-- Add New Place --"]:
        st.session_state.n_name = place_selection

        prev = journal_df[journal_df[name_col] == place_selection]
        if not prev.empty:
            latest = prev.iloc[-1]

            st.session_state.zip_code = str(latest[zip_col])
            st.session_state.city = latest[city_col]
            st.session_state.state = latest[state_col]
            st.session_state.country = latest[country_col]

            st.session_state.zip_code = st.text_input("Zip Code", st.session_state.zip_code)
            st.session_state.city = st.text_input("City", st.session_state.city)
            st.session_state.state = st.text_input("State", st.session_state.state)
            st.session_state.country = st.text_input("Country", st.session_state.country)

    # ========================================================
    # CASE 2 — New Place (ZIP lookup instantly)
    # ========================================================
    elif place_selection == "-- Add New Place --":

        st.session_state.n_name = st.text_input("Enter New Place Name", st.session_state.n_name)

        st.session_state.zip_code = st.text_input("Zip Code", st.session_state.zip_code)

        if len(st.session_state.zip_code) == 5 and st.session_state.zip_code.isnumeric():
            result = lookup_zip(st.session_state.zip_code)
            if result:
                st.session_state.country = result["country"]
                st.session_state.state = result["state"]

                if len(result["cities"]) > 1:
                    st.session_state.city = st.selectbox("City", result["cities"])
                else:
                    st.session_state.city = result["cities"][0]
        st.session_state.city = st.text_input("City", st.session_state.city)
        st.session_state.state = st.text_input("State", st.session_state.state)
        st.session_state.country = st.text_input("Country", st.session_state.country)

    # ========================================================
    # ALWAYS SHOW LOCATION FIELDS (Reactive)
    # ========================================================


    # ========================================================
    # OTHER JOURNAL FIELDS
    # ========================================================
    activities = st.multiselect("Activities", ["Walk", "Hike", "Garden", "Other"],key="activities_field")
    jnotes = st.text_area("Journal Notes")


    # ========================================================
    # SAVE BUTTON
    # ========================================================
    if st.button("Submit Entry"):

        timestamp = datetime.combine(ts_date, ts_time)
        end_dt = timestamp + timedelta(minutes=int(n_duration))

        n_place = (
            f"{st.session_state.n_name}, "
            f"{st.session_state.city} {st.session_state.state} {st.session_state.country}"
        ).replace("  ", " ").strip()

        new_entry = [
            "",
            st.session_state["user_name"],
            st.session_state["user_email"],
            timestamp.strftime("%m/%d/%y %I:%M %p"),
            n_duration,
            end_dt.strftime("%m/%d/%y %I:%M %p"),
            st.session_state.n_name,
            st.session_state.city,
            st.session_state.state,
            st.session_state.zip_code,
            st.session_state.country,
            n_place,
            "",
            "",
            "",
            ", ".join(activities),
            jnotes
        ]

        journal_ws.append_row(new_entry, value_input_option="USER_ENTERED")
        st.success("✅ Journal entry saved!")


        # # ---- RESET ALL FIELDS ----
        # for key in ["n_name", "zip_code", "city", "state", "country",
        #             "place_select", "last_place_choice"]:
        #     if key in st.session_state:
        #         del st.session_state[key]

        # st.rerun()

else :
    st.write(f"Please login using the sidebar")