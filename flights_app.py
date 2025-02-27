import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta, timezone
import urllib.parse
import certifi
import ssl
from sqlalchemy.orm import sessionmaker #, clear_mappers
from create_db import engine, User, FlightSearch, FlightResult
import streamlit_authenticator as stauth

# Remove the coding block below which adds the login/register functionality to main page
# ✅ Redirect to Login if Not Authenticated
# if "user_email" not in st.session_state:
#     st.warning("You must log in first.")
#     st.write("🔑 [Go to Login Page](http://127.0.0.1:5000/login)")
#     #registration logic:
#     st.subheader("📝 Register")
#     register_email = st.text_input("Email")
#     register_password = st.text_input("Password", type="password")
#     register_fullname = st.text_input("Full Name")

#     if st.button("Register"):
#         if register_email and register_password and register_fullname:
#             response = requests.post("http://127.0.0.1:5000/register", json={
#                 "email": register_email,
#                 "password": register_password,
#                 "full_name": register_fullname
#             })
            
#             if response.status_code == 200:
#                 st.success("✅ Registration successful! You can now login.")
#             else:
#                 st.error(f"❌ Registration failed: {response.text}")
#         else:
#             st.warning("⚠️ Please fill in all fields before registering.")


BASE_URL = "http://127.0.0.1:5000"  # Flask API

# Create DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Environment setup:
# Set API credentials (Use environment variables if set)
OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME")
OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD")
API_URL = "https://realtime.oxylabs.io/v1/queries"
# Rmoved hard coded values for OXYLABS_USERNAME and OXYLABS_PASSWORD:
# To set environment variables in Linux/Mac:
# export OXYLABS_USERNAME="your_username"
# export OXYLABS_PASSWORD="your_password"

# Force requests to use system SSL certificates
# requests.get("https://www.google.com", verify=certifi.where())
#ssl_context = ssl.create_default_context(cafile=certifi.where())

# Functional library block:
# Function to generate the correct booking URL
def get_booking_url(flight, from_location, to_location, departure_date, return_date, trip_type):
    """Generates a Google Flights link that directly leads to the selected flight."""
    
    # Convert dates to YYYY-MM-DD format
    formatted_departure_date = departure_date.strftime("%Y-%m-%d")
    formatted_return_date = return_date.strftime("%Y-%m-%d") if return_date else ""

    # Construct Google Flights direct URL
    google_flights_url = (
        f"https://www.google.com/travel/flights?"
        f"q=Flights+from+{from_location}+to+{to_location}+on+{formatted_departure_date}"
    )

    # If round trip, include return date
    if trip_type == "Round-trip":
        google_flights_url += f"+returning+on+{formatted_return_date}"

    google_flights_url += f"&curr={currency}"  # Add currency parameter

    return google_flights_url

# Function to generate the correct numeric price:
def extract_numeric_price(price_str):
    """Extracts the numeric price from a string, returns None if not convertible."""
    try:
        return int(price_str.replace("$", "").replace(",", ""))
    except ValueError:
        return float('inf')  # Assign an infinite value to push it to the end of sorting

# Helper function
def parse_datetime_or_none(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


# Application code:
# Streamlit UI
st.title("✈️ Cheapest Airfare Finder")

# Adding the authentication UI and user profile:
# 🚀 Authentication UI
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

    # Selection for login or register
    auth_mode = st.sidebar.radio("Select Mode:", ["Login", "Register"])

    if auth_mode == "Login":
        login_email = st.sidebar.text_input("Email", key="login_email")
        login_password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login"):
            headers = {"Content-Type": "application/json"}  # Ensure JSON content type
            response = requests.post(f"{BASE_URL}/login", json={"email": login_email, "password": login_password}, headers=headers)

            if response.status_code == 200:
                try:
                    user_data = response.json()  # Extract JSON response

                    if "user_id" in user_data:  # ✅ Ensure user_id is extracted
                        st.session_state["user"] = {
                            "email": login_email,
                            "user_id": user_data["user_id"],  # ✅ Ensure user_id is stored
                            "session": response.cookies.get("session", None)  # ✅ Extract session cookie if available
                        }
                        st.success(f"✅ Logged in as {login_email}")  # Debug success message
                        st.rerun()  # Refresh UI after login
                    else:
                        st.sidebar.error("❌ Login failed: No user_id returned")
                except json.JSONDecodeError:
                    st.sidebar.error("❌ Unexpected response from server.")
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

                try:
                    response_json = response.json()
                    if response.status_code == 200:
                        st.sidebar.success("✅ Registration successful! Please login.")
                    else:
                        st.sidebar.error(f"❌ Registration failed: {response_json.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    st.sidebar.error("❌ Unexpected response from server.")
            else:
                st.sidebar.warning("⚠️ Please fill in all fields before registering.")

# 🚀 User Profile Section (Only Show When User Clicks Button)
if st.session_state["user"]:
    st.subheader("🛠️ Update Preferences")

    if "profile_data" not in st.session_state:
        if st.button("Fetch Profile Data"):
            st.write("Debug: Current session state ->", st.session_state)  # Debugging

            if "user_id" in st.session_state["user"] and "session" in st.session_state["user"]:
                user_id = st.session_state["user"]["user_id"]
                session_cookie = st.session_state["user"]["session"]

                profile_response = requests.get(
                    f"{BASE_URL}/profile",
                    params={"user_id": user_id},
                    cookies={"session": session_cookie}  # Send session cookie
                )

                st.write("Debug: Profile API response ->", profile_response.status_code, profile_response.text)  # Debugging

                if profile_response.status_code == 200:
                    st.session_state["profile_data"] = profile_response.json()
                    st.success("✅ Profile data loaded successfully!")
                else:
                    st.error("❌ Failed to fetch profile data. Check login status.")
            else:
                st.error("User not logged in properly.")

    
    # Only show preferences form if profile data exists
    if "profile_data" in st.session_state:
        profile_data = st.session_state["profile_data"]

        currency = st.selectbox("Currency", ["USD", "CAD"], index=["USD", "CAD"].index(profile_data.get("currency", "USD")))
        flight_type = st.selectbox("Flight Type", ["Any", "Nonstop"], index=["Any", "Nonstop"].index(profile_data.get("flight_type", "Any")))
        market = st.text_input("Market", value=profile_data.get("market", "US"))

        if st.button("Save Preferences"):
            if "user_id" in st.session_state["user"] and "session" in st.session_state["user"]:
                user_id = st.session_state["user"]["user_id"]
                session_cookie = st.session_state["user"]["session"]

                update_response = requests.put(
                    f"{BASE_URL}/profile",
                    json={"currency": currency, "flight_type": flight_type, "market": market},
                    params={"user_id": user_id},
                    cookies={"session": session_cookie}  # ✅ Ensure session cookie is included
                )

                st.write("Debug: Profile Update API response ->", update_response.status_code, update_response.text)  # Debugging

                if update_response.status_code == 200:
                    st.success("✅ Preferences updated successfully!")
                else:
                    st.error(f"❌ Failed to update: {update_response.json().get('error', 'Unauthorized access')}")
            else:
                st.error("❌ Missing user authentication data.")
st.write("---")
#after the authentication block start the search:
st.write("Enter your travel details below:")

# Allow users to select currency (USD/CAD):
currency = st.radio("Select Currency:", ["USD", "CAD"])

# Add One-way / Round-trip selection
trip_type = st.radio("Select Trip Type:", ["One-way", "Round-trip"])

# Add Direct / Connecting flight filter
flight_type = st.radio("Flight Type:", ["Any", "Nonstop Only"])

# Allow user to select the number of top flights to display (between 3 and 10)
top_n = st.slider("Select number of top flights to display:", min_value=3, max_value=10, value=3)

# User inputs for FROM/TO locations and travel dates:
from_location = st.text_input("From (Airport Code)", value="YVR")
to_location = st.text_input("To (Airport Code)", value="PEK")

# Departure date input
departure_date = st.date_input("Select Departure Date", datetime.today() + timedelta(days=2))

# Allow users to choose sorting criteria:
# sort_option = st.selectbox(
#     "Sort flights by:",
#     ["Lowest Price", "Shortest Duration", "Preferred Airline"]
# )

# Show return date input ONLY if Round-trip is selected
return_date = None
if trip_type == "Round-trip":
    return_date = st.date_input("Select Return Date", departure_date + timedelta(days=7))  # Default return 1 week later

if st.button("🔍 Search Flights"):
    with st.spinner("Searching for the best flight deals..."):
        print("🚩 Starting Search Flights Logic")

        session = SessionLocal()

        #user_email = "service@airta.co"
        user = session.query(User).filter_by(email=user_email).first()
        from sqlalchemy.orm import joinedload

        user = session.query(User).options(joinedload(User.alerts)).filter_by(email=user_email).first()


        if not user:
            print(f"❌ User '{user_email}' NOT found!")
            st.error(f"User '{user_email}' not found in the database!")
            session.close()

        print(f"✅ User found! (User ID: {user.user_id})")
        st.success(f"✅ User found! (User ID: {user.user_id})")

        query = f"Flights from {from_location} to {to_location} on {departure_date.strftime('%Y-%m-%d')}"
        if trip_type == "Round-trip" and return_date:
            query += f" returning on {return_date.strftime('%Y-%m-%d')}"
        
        print(f"🚩 Query: {query}")

        payload = {
            "source": "google_search",
            "query": query,
            "parse": "true",
            "limit": 10,
            "pages": 3,
            "curr": currency
        }

        print("🚩 Sending request to Oxylabs API... Bypassing for testing")

        # Mock response instead of calling Oxylabs API
        data = {
            "results": [
                {
                    "content": {
                        "results": {
                            "flights": {
                                "results": [
                                    {
                                        "airline": "Air Canada",
                                        "price": "$199",
                                        "type": "nonstop",
                                        "duration": "5h 30m",
                                        "Flight Number": "AC123",
                                        "Departure Time": "2025-03-01 10:00:00",
                                        "Arrival Time": "2025-03-01 15:30:00"
                                    },
                                    {
                                        "airline": "Delta",
                                        "price": "$250",
                                        "type": "1-stop",
                                        "duration": "7h 45m",
                                        "Flight Number": "DL456",
                                        "Departure Time": "2025-03-01 08:00:00",
                                        "Arrival Time": "2025-03-01 15:45:00"
                                    }
                                ]
                            }
                        }
                    }
                }
            ]
        }

        print("✅ Using mock flight data.")

        # Bypass API failure and continue with fake results
        flights = data["results"][0]["content"]["results"]["flights"]["results"]

        # bypassing the API call for debugging:
        #response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD), verify=certifi.where())

        # if response.status_code == 200:
        #     print("✅ Received 200 OK from Oxylabs API.")
        #     data = response.json()

        #     flights = []
        #     for result in data.get("results", []):
        #         flights.extend(result.get("content", {}).get("results", {}).get("flights", {}).get("results", []))

        #     print(f"🚩 Flights extracted from API: {len(flights)}")

        #     if flights:
        #         flight_search = FlightSearch(
        #             user_id=user.user_id,
        #             origin=from_location,
        #             destination=to_location,
        #             departure_date=departure_date,
        #             return_date=return_date if trip_type == "Round-trip" else None,
        #             trip_type=trip_type.lower(),
        #             search_URL=query,
        #             created_at=datetime.now()
        #         )
        #         session.add(flight_search)
        #         session.commit()
        #         print(f"✅ Flight search recorded! (Search ID: {flight_search.search_id})")
        #         st.success(f"✅ Flight search recorded! (Search ID: {flight_search.search_id})")

        #         for flight in flights[:top_n]:
        #             try:
        #                 print("🚩 Inserting flight result:", flight)  # detailed debug
        #                 flight_result = FlightResult(
        #                     search_id=flight_search.search_id,
        #                     airline=flight["airline"],
        #                     price=float(flight["price"].replace("$", "").replace(",", "")),
        #                     flight_number=flight.get("Flight Number", "N/A"),
        #                     departure_time=parse_datetime_or_none(flight.get("Departure Time")),
        #                     arrival_time=parse_datetime_or_none(flight.get("Arrival Time")),
        #                     duration=flight["duration"],
        #                     stops=flight["type"],
        #                     booking_url=get_booking_url(
        #                         flight, from_location, to_location, departure_date, return_date, trip_type
        #                     ),
        #                     created_at=datetime.now(),
        #                     retrieved_at=datetime.now()
        #                 )
        #                 session.add(flight_result)
        #                 session.commit()
        #                 print(f"✅ Inserted flight result successfully (ID: {flight_result.result_id})")
        #                 st.success(f"✅ Inserted flight result: {flight['airline']} at ${flight_result.price}")

        #             except Exception as e:
        #                 session.rollback()
        #                 print(f"❌ Failed inserting flight result due to error: {e}")
        #                 st.error(f"❌ Failed inserting flight result: {e}")
        # else:
        #     print(f"❌ API Error: {response.status_code} - {response.text}")
        #     st.error(f"API Error: {response.status_code} - {response.text}")

        session.close()
        print("🚩 Database session closed.")

# --- END DATABASE INTEGRATION ---

        # Extract flight results
        try:
            flights = data["results"][0]["content"]["results"]["flights"]["results"]
            print("FLIGHT TYPES RETURNED:", [flight["type"] for flight in flights])
            print(f"DEBUG: Total flights received from API: {len(flights)}")

            # Apply filtering for "Nonstop Only"
            if flight_type == "Nonstop Only":
                flights = [flight for flight in flights if flight["type"].lower() == "nonstop"]
            
            if not flights:
                st.warning("No flights found. Try a different search.")
                session.close()
                print("Session closed at line 159.")

            # Sort flights by price (ascending order)
            flights = sorted(flights, key=lambda x: extract_numeric_price(x["price"]))

            # Find the lowest price for comparison
            lowest_price = int(flights[0]["price"].replace("$", "").replace(",", ""))

            # Show only top N results
            st.subheader(f"📌 Top {top_n} Flight Options:")

            for i, flight in enumerate(flights[:top_n], 1):
                st.markdown(f"### ✈️ Option {i}")
                st.write(f"**Airline:** {flight['airline']}")
                st.write(f"**Type:** {flight['type']}")
                st.write(f"**Price:** {flight['price']}")
                st.write(f"**Duration:** {flight['duration']}")

                pros = []
                cons = []

                if flight["type"].lower() == "nonstop":
                    pros.append("No layovers ✅")
                else:
                    cons.append("Has layovers ❌")

                duration_str = flight["duration"]
                days = int(duration_str.split("d")[0]) if "d" in duration_str else 0
                hours = int(duration_str.split("h")[0].split()[-1]) if "h" in duration_str else 0
                duration_hours = (days * 24) + hours

                if duration_hours < 6:
                    pros.append("Short travel time ✅")
                elif duration_hours > 12:
                    cons.append("Long travel time ❌")

                price_int = int(flight["price"].replace("$", "").replace(",", ""))
                if price_int == lowest_price:
                    pros.append("Cheapest option ✅")
                elif price_int > (lowest_price * 1.5):
                    cons.append("Expensive compared to cheapest option ❌")

                if pros:
                    st.write("**✅ Pros:**")
                    for pro in pros:
                        st.write(f"- {pro}")

                if cons:
                    st.write("**❌ Cons:**")
                    for con in cons:
                        st.write(f"- {con}")

                booking_url = get_booking_url(flight, from_location, to_location, departure_date, return_date, trip_type)
                st.markdown(
                    f'<a href="{booking_url}" target="_blank"><button style="background-color:#4CAF50;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Book Now</button></a>',
                    unsafe_allow_html=True
                )
                st.write("---")

        except KeyError:
            st.error("No flight data found. Try another search.")