# journal basic code

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

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

    n_name = st.text_input("Nature Place Name")
    zip_code = st.text_input("Zip Code")
    country = st.text_input("Country")

    # Optional fields
    activities = st.multiselect("Activities", ["Walk", "Hike", "Garden", "Other"])
    jnotes = st.text_area("Journal Notes")
    city = st.text_input("City (optional)")
    state = st.text_input("State (optional)")

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

