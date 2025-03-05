import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from create_db import engine, User, FlightSearch, FlightResult
import streamlit_authenticator as stauth

# Flask API URL:
BASE_URL = "http://127.0.0.1:5000"

# Create DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Booking.com API via RapidAPI
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Use environment variable for security
API_URL = f"https://{RAPIDAPI_HOST}/api/v1/flights/searchFlights"

# Helper function to format datetime
def parse_datetime_or_none(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    except (TypeError, ValueError):
        return None

# Application UI
st.title("✈️ Cheapest Airfare Finder")

# Authentication UI
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"]:
    st.sidebar.write(f"👤 Logged in as: {st.session_state['user']['email']}")
    user_email = st.session_state["user"]["email"]
    if st.sidebar.button("Logout"):
        requests.post(f"{BASE_URL}/logout")
        st.session_state["user"] = None
        st.rerun()
else:
    st.sidebar.subheader("🔐 Login / Register")
    auth_mode = st.sidebar.radio("Select Mode:", ["Login", "Register"])
    
    if auth_mode == "Login":
        login_email = st.sidebar.text_input("Email", key="login_email")
        login_password = st.sidebar.text_input("Password", type="password", key="login_password")
        if st.sidebar.button("Login"):
            response = requests.post(f"{BASE_URL}/login", json={"email": login_email, "password": login_password})
            if response.status_code == 200:
                user_data = response.json()
                if "user_id" in user_data:
                    st.session_state["user"] = {
                        "email": login_email,
                        "user_id": user_data["user_id"],
                        "session": response.cookies.get("session", None)
                    }
                    st.success(f"✅ Logged in as {login_email}")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Login failed: No user_id returned")
            else:
                st.sidebar.error(f"Invalid credentials (Status: {response.status_code})")

    elif auth_mode == "Register":
        register_email = st.sidebar.text_input("Email", key="register_email")
        register_password = st.sidebar.text_input("Password", type="password", key="register_password")
        full_name = st.sidebar.text_input("Full Name", key="register_fullname")
        if st.sidebar.button("Register"):
            if register_email and register_password and full_name:
                response = requests.post(f"{BASE_URL}/register", json={
                    "email": register_email,
                    "password": register_password,
                    "full_name": full_name
                })
                if response.status_code == 200:
                    st.sidebar.success("✅ Registration successful! Please login.")
                else:
                    st.sidebar.error(f"❌ Registration failed: {response.json().get('error', 'Unknown error')}")
            else:
                st.sidebar.warning("⚠️ Please fill in all fields before registering.")

# Fetch user profile automatically
if st.session_state["user"]:
    user_id = st.session_state["user"]["user_id"]
    session_cookie = st.session_state["user"]["session"]
    
    if "profile_data" not in st.session_state:
        profile_response = requests.get(
            f"{BASE_URL}/profile",
            params={"user_id": user_id},
            cookies={"session": session_cookie}
        )
        if profile_response.status_code == 200:
            st.session_state["profile_data"] = profile_response.json()
        else:
            st.session_state["profile_data"] = {}

    profile_data = st.session_state["profile_data"]
    default_currency = profile_data.get("currency", "USD")
    default_flight_type = profile_data.get("flight_type", "Any")
    default_market = profile_data.get("market", "US")
else:
    default_currency = "USD"
    default_flight_type = "Any"
    default_market = "US"

# --- ✈️ SEARCH INPUT FORM ---
st.subheader("Enter your travel details below:")
currency = st.radio("Select Currency:", ["USD", "CAD"], index=["USD", "CAD"].index(default_currency))
trip_type = st.radio("Select Trip Type:", ["One-way", "Round-trip"])
flight_type = st.radio("Flight Type:", ["Any", "Nonstop Only"], index=["Any", "Nonstop Only"].index(default_flight_type))
top_n = st.slider("Select number of top flights to display:", min_value=3, max_value=10, value=3)

from_location = st.text_input("From (Airport Code)", value="YVR")
to_location = st.text_input("To (Airport Code)", value="PEK")
departure_date = st.date_input("Select Departure Date", datetime.today() + timedelta(days=2))
return_date = None
if trip_type == "Round-trip":
    return_date = st.date_input("Select Return Date", departure_date + timedelta(days=7))

adults = st.number_input("Number of Adults", min_value=1, max_value=5, value=1)
children = st.number_input("Number of Children", min_value=0, max_value=5, value=0)
cabin_class = st.selectbox("Cabin Class", ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], index=0)

# --- SEARCH BUTTON ---
if st.button("🔍 Search Flights"):
    with st.spinner("Searching for the best flight deals..."):
        # Construct API request
        params = {
            "fromId": f"{from_location}.AIRPORT",
            "toId": f"{to_location}.AIRPORT",
            "departDate": departure_date.strftime("%Y-%m-%d"),
            "returnDate": return_date.strftime("%Y-%m-%d") if trip_type == "Round-trip" else "",
            "pageNo": 1,
            "adults": adults,
            "children": f"{children},17" if children > 0 else "0",
            "sort": "BEST",
            "cabinClass": cabin_class,
            "currency_code": currency
        }

        # ✅ Fix: Ensure API headers are ASCII-compatible
        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST.encode("ascii", "ignore").decode(),
            "x-rapidapi-key": RAPIDAPI_KEY.encode("ascii", "ignore").decode()
        }

        try:
            response = requests.get(API_URL, headers=headers, params=params)
            response.raise_for_status()  # Raise an error if the request fails
        except requests.exceptions.RequestException as e:
            st.error(f"❌ API Request Failed: {str(e)}")
            st.stop()

        if response.status_code == 200:
            data = response.json()
            flights = data.get("data", {}).get("flightOffers", [])

            if not flights:
                st.warning("No flights found. Try changing the search criteria.")
            else:
                st.subheader(f"📌 Showing {len(flights[:top_n])} Best Flight Options:")
                for flight in flights[:top_n]:
                    segments = flight.get("segments", [])
                    if not segments:
                        continue

                    departure_segment = segments[0]
                    arrival_segment = segments[-2]  # ✅ FIXED: Correct last arrival segment

                    departure_airport = departure_segment.get("departureAirport", {}).get("name", "Unknown")
                    arrival_airport = arrival_segment.get("arrivalAirport", {}).get("name", "Unknown")
                    departure_time = departure_segment.get("departureTime", "Unknown")
                    arrival_time = arrival_segment.get("arrivalTime", "Unknown")

                    carriers_data = departure_segment.get("legs", [{}])[0].get("carriersData", [{}])
                    airline_name = carriers_data[0].get("name", "Unknown Airline")
                    airline_code = carriers_data[0].get("code", "Unknown")
                    airline_logo = carriers_data[0].get("logo", "")

                    price_info = flight.get("priceBreakdown", {}).get("total", {})
                    price_currency = price_info.get("currencyCode", "USD")
                    price_amount = price_info.get("units", 0)

                    st.markdown(f"{st.image(airline_logo, width=10)} {airline_name} ({airline_code})")
                    st.write(f"💲 Price: {price_currency} {price_amount}")
                    st.write(f"🛫 {departure_airport} → {arrival_airport}")
                    st.write(f"⏰ {departure_time} → {arrival_time}")
                    st.image(airline_logo, width=50)
                    st.write("---")

        else:
            st.error(f"❌ API Error: {response.status_code} - {response.text}")