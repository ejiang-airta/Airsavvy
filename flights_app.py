import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import urllib.parse
import certifi
import ssl
from sqlalchemy.orm import sessionmaker
from create_db import engine, User, FlightSearch, FlightResult

# Create DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

        user_email = "service@airta.co"
        user = session.query(User).filter_by(email=user_email).first()

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

        print("🚩 Sending request to Oxylabs API...")
        response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD), verify=certifi.where())

        if response.status_code == 200:
            print("✅ Received 200 OK from Oxylabs API.")
            data = response.json()

            flights = []
            for result in data.get("results", []):
                flights.extend(result.get("content", {}).get("results", {}).get("flights", {}).get("results", []))

            print(f"🚩 Flights extracted from API: {len(flights)}")

            if flights:
                flight_search = FlightSearch(
                    user_id=user.user_id,
                    origin=from_location,
                    destination=to_location,
                    departure_date=departure_date,
                    return_date=return_date if trip_type == "Round-trip" else None,
                    trip_type=trip_type.lower(),
                    search_URL=query,
                    created_at=datetime.now()
                )
                session.add(flight_search)
                session.commit()
                print(f"✅ Flight search recorded! (Search ID: {flight_search.search_id})")
                st.success(f"✅ Flight search recorded! (Search ID: {flight_search.search_id})")

                for flight in flights[:top_n]:
                    try:
                        print("🚩 Inserting flight result:", flight)  # detailed debug
                        flight_result = FlightResult(
                            search_id=flight_search.search_id,
                            airline=flight["airline"],
                            price=float(flight["price"].replace("$", "").replace(",", "")),
                            flight_number=flight.get("Flight Number", "N/A"),
                            departure_time=parse_datetime_or_none(flight.get("Departure Time")),
                            arrival_time=parse_datetime_or_none(flight.get("Arrival Time")),
                            duration=flight["duration"],
                            stops=flight["type"],
                            booking_url=get_booking_url(
                                flight, from_location, to_location, departure_date, return_date, trip_type
                            ),
                            created_at=datetime.now(),
                            retrieved_at=datetime.now()
                        )
                        session.add(flight_result)
                        session.commit()
                        print(f"✅ Inserted flight result successfully (ID: {flight_result.result_id})")
                        st.success(f"✅ Inserted flight result: {flight['airline']} at ${flight_result.price}")

                    except Exception as e:
                        session.rollback()
                        print(f"❌ Failed inserting flight result due to error: {e}")
                        st.error(f"❌ Failed inserting flight result: {e}")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            st.error(f"API Error: {response.status_code} - {response.text}")

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