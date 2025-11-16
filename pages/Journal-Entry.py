# journal basic code

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import requests

# ---- Google Sheets setup ----
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"], scopes=scope
)
client = gspread.authorize(creds)

# Replace with your Journal Google Sheet ID
JOURNAL_SHEET_ID = st.secrets["journal_data_sheet_id"]
journal_ws = client.open_by_key(JOURNAL_SHEET_ID).worksheet("Journal")

journal_df = pd.DataFrame(journal_ws.get_all_records())

def col(df, name):
    """Find column in df regardless of spacing or case."""
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

# Session state defaults
for key in ["n_name", "zip_code", "city", "state", "country"]:
    st.session_state.setdefault(key, "")

# ---- Simulated login (replace with your login app) ----
if "user_email" not in st.session_state:
    st.session_state["user_email"] = "test@example.com"
    st.session_state["user_name"] = "Test User"

# ---- Journal Entry Form ----
st.title("🌿 Nature Journal Entry")

with st.form("journal_form"):
    # Required fields
    ts_date = st.date_input("Select date", value=datetime.today())
    ts_time = st.time_input("Select time", value=datetime.now().time())
    timestamp = datetime.combine(ts_date, ts_time)

    n_duration = st.number_input("Duration in minutes", min_value=1, max_value=1440, step=5)

    # === Smart Place Picker ===
    place_selection = st.selectbox(
        "Nature Place Name",
        options=["-- Add New Place --"] + existing_places,
        index=0
    )
    #n_name = st.text_input("Nature Place Name")

    # === ZIP → City, State, Country Auto Lookup ===
    # Prepare fields
    city = ""
    state = ""
    country = ""
    zip_code = ""
    use_zip_lookup = True  # will disable when loading from existing data

    # --------------------------------------------------------
    # CASE 1 — Existing Place Selected
    # --------------------------------------------------------
    if place_selection != "-- Add New Place --":
        st.session_state.n_name = place_selection

        prev = journal_df[journal_df[name_col] == place_selection]

        if not prev.empty:
            latest = prev.iloc[-1]

            st.session_state.zip_code = latest[zip_col]
            st.session_state.city = latest[city_col]
            st.session_state.state = latest[state_col]
            st.session_state.country = latest[country_col]

        st.session_state.zip_code = st.text_input("Zip Code", value=st.session_state.zip_code)
        st.session_state.city     = st.text_input("City",     value=st.session_state.city)
        st.session_state.state    = st.text_input("State",    value=st.session_state.state)
        st.session_state.country  = st.text_input("Country",  value=st.session_state.country)

    # --------------------------------------------------------
    # CASE 2 — Add New Place (ZIP Lookup)
    # --------------------------------------------------------
    else:
        st.session_state.n_name = st.text_input("Enter New Place Name", value=st.session_state.n_name)
        st.session_state.zip_code = st.text_input("Zip Code", value=st.session_state.zip_code)

        if len(st.session_state.zip_code) == 5:
            try:
                r = requests.get(f"https://api.zippopotam.us/us/{st.session_state.zip_code}")
                if r.status_code == 200:
                    data = r.json()
                    st.session_state.country = data["country"]
                    st.session_state.state = data["places"][0]["state abbreviation"]
                    cities = sorted({p["place name"] for p in data["places"]})
                    st.session_state.city = st.selectbox("City", cities)
            except:
                pass

        if not st.session_state.city:
            st.session_state.city = st.text_input("City", value=st.session_state.city)
        if not st.session_state.state:
            st.session_state.state = st.text_input("State", value=st.session_state.state)
        if not st.session_state.country:
            st.session_state.country = st.text_input("Country", value=st.session_state.country)

    # Read-only state/country
    #st.text_input("State", state, disabled=True)
    #st.text_input("Country", country, disabled=True)

    #zip_code = st.text_input("Zip Code")
    #country = st.text_input("Country")

    # Optional fields
    activities = st.multiselect("Activities", ["Walk", "Hike", "Garden", "Other"])
    jnotes = st.text_area("Journal Notes")
    #city = st.text_input("City (optional)")
    #state = st.text_input("State (optional)")

    submitted = st.form_submit_button("Submit Entry")

    # if submitted:
    #     new_entry = [
    #         st.session_state["user_name"],
    #         st.session_state["user_email"],
    #         str(timestamp),
    #         n_duration,
    #         n_name,
    #         zip_code,
    #         country,
    #         ", ".join(activities),
    #         jnotes,
    #         city,
    #         state
    #     ]
    #     journal_ws.append_row(new_entry)
    #     st.success("✅ Journal entry saved!")

    if submitted:
        # Combine date + time into a single datetime
        timestamp = datetime.combine(ts_date, ts_time)

        # Compute End Date Time from duration
        end_dt = timestamp + timedelta(minutes=int(n_duration))

        # Build a nice n_Place string
        n_place = f"{n_name}, {city} {state} {country}".strip().replace("  ", " ")

        # Activities as comma-separated text
        activities_str = ", ".join(activities)

        # Build row in EXACT column order of the sheet:
        new_entry = [
            "",                               # Status (blank for now)
            st.session_state["user_name"],    # User Name
            st.session_state["user_email"],   # User email
            timestamp.strftime("%m/%d/%y %I:%M %p"),  # Timestamp
            n_duration,                       # n_Duration
            end_dt.strftime("%m/%d/%y %I:%M %p"),     # End Date Time
            n_name,                           # n_Name
            city,                             # City
            state,                            # State
            zip_code,                         # Zip
            country,                          # Country
            n_place,                          # n_Place
            "",                               # n_Lati (no data yet)
            "",                               # n_Long (no data yet)
            "",                               # n_park_nbr (no data yet)
            activities_str,                   # n_activity
            jnotes                            # n_notes
        ]

        journal_ws.append_row(new_entry, value_input_option="USER_ENTERED")
        st.success("✅ Journal entry saved!")

