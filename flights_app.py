import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import urllib.parse
import certifi
import ssl

# Force requests to use system SSL certificates
# requests.get("https://www.google.com", verify=certifi.where())
ssl_context = ssl.create_default_context(cafile=certifi.where())


# Set API credentials (Use environment variables if set)
OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME", "ejiang1_Hq6Ex")
OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD", "Airtahero_3308")
API_URL = "https://realtime.oxylabs.io/v1/queries"

# Streamlit UI
st.title("✈️ Cheapest Airfare Finder")
st.write("Enter your travel details below:")

# User inputs
from_location = st.text_input("From (Airport Code)", value="YVR")
to_location = st.text_input("To (Airport Code)", value="PEK")
travel_date = st.date_input("Travel Date", value=datetime.now().date() + timedelta(days=2))

if st.button("🔍 Search Flights"):
    with st.spinner("Searching for the best flight deals..."):
        st.write(f"Searching for flights from **{from_location}** to **{to_location}** on **{travel_date}**...")

        # Format the query
        query = f"Flights from {from_location} to {to_location} on {travel_date}"

        # API request payload
        payload = {
            "source": "google_search",
            "query": query,
            "parse": "true"
        }

        # Make the API call
        response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD), verify=certifi.where())
        #response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD), verify=False)

        if response.status_code == 200:
            data = response.json()

            # Extract flight results
            try:
                flights = data["results"][0]["content"]["results"]["flights"]["results"]
                
                if not flights:
                    st.warning("No flights found. Try a different search.")

                # Sort flights by price (ascending order)
                flights = sorted(flights, key=lambda x: int(x["price"].replace("$", "").replace(",", "")))

                # Find the lowest price for comparison
                lowest_price = int(flights[0]["price"].replace("$", "").replace(",", ""))

                # Show only top 3 results
                st.subheader("📌 Top 3 Flight Options:")
                for i, flight in enumerate(flights[:3], 1):
                    st.markdown(f"### ✈️ Option {i}")
                    st.write(f"**Airline:** {flight['airline']}")
                    st.write(f"**Type:** {flight['type']}")
                    st.write(f"**Price:** {flight['price']}")
                    st.write(f"**Duration:** {flight['duration']}")

                    # ✅ Generate Pros & Cons
                    pros = []
                    cons = []

                    # Check flight type
                    if flight["type"].lower() == "nonstop":
                        pros.append("No layovers ✅")
                    else:
                        cons.append("Has layovers ❌")

                    # Check flight duration
                    # Extract duration correctly
                    duration_str = flight["duration"]

                    # Handle "1d 5h 30m" format
                    days = 0
                    if "d" in duration_str:
                        parts = duration_str.split("d")
                        days = int(parts[0].strip())  # Extract number of days
                        duration_str = parts[1].strip()  # Remove "1d" part

                    # Extract hours correctly
                    hours = 0
                    if "h" in duration_str:
                        hours = int(duration_str.split("h")[0].strip())

                    # Convert total duration to hours
                    duration_hours = (days * 24) + hours

                    if duration_hours < 6:
                        pros.append("Short travel time ✅")
                    elif duration_hours > 12:
                        cons.append("Long travel time ❌")

                    # Compare price
                    price_int = int(flight["price"].replace("$", "").replace(",", ""))
                    if price_int == lowest_price:
                        pros.append("Cheapest option ✅")
                    elif price_int > (lowest_price * 1.5):  # If more than 50% higher than the cheapest
                        cons.append("Expensive compared to cheapest option ❌")

                    # Display Pros & Cons
                    if pros:
                        st.write("**✅ Pros:**")
                        for pro in pros:
                            st.write(f"- {pro}")

                    if cons:
                        st.write("**❌ Cons:**")
                        for con in cons:
                            st.write(f"- {con}")

                    # Add a "Book Now" button with a proper link
                    # st.markdown(
                    #     f'<a href="{flight["url"]}" target="_blank"><button style="background-color:#4CAF50;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Book Now</button></a>',
                    #     unsafe_allow_html=True
                    # )
                    
                    # Function to generate the correct booking URL
                    def get_booking_url(flight, from_location, to_location, travel_date):
                        airline = flight["airline"]
                        google_flights_url = flight["url"]  # Default fallback

                        # Convert travel_date to required format (YYYY-MM-DD)
                        formatted_date = travel_date.strftime("%Y-%m-%d")
                        # Define airline-specific booking URL templates (only for airlines that support deep linking)
                        AIRLINE_BOOKING_URLS = {
                            "United": "https://www.united.com/en/us/book-flight?from={FROM}&to={TO}&departdate={DATE}",
                            "American Airlines": "https://www.aa.com/reservation/find-flights?origin={FROM}&destination={TO}&departDate={DATE}",
                            "Alaska Airlines": "https://www.alaskaair.com/planbook/flights/select?from={FROM}&to={TO}&departure={DATE}",
                            "WestJet": "https://www.westjet.com/en-ca/book-trip/select-flight?origin={FROM}&destination={TO}&depart={DATE}"
                        }

                        # If the airline has a known booking site with deep linking
                        if airline in AIRLINE_BOOKING_URLS:
                            return AIRLINE_BOOKING_URLS[airline]
                        # if airline in AIRLINE_BOOKING_URLS:
                        #     return AIRLINE_BOOKING_URLS[airline].format(FROM=from_location, TO=to_location, DATE=formatted_date)
                        
                        # 🔹 Fallback Option: Use Google Flights Deep Link
                        google_flights_deep_link = f"https://www.google.com/travel/flights?q=Flights+from+{from_location}+to+{to_location}+on+{formatted_date}"
                        
                        return google_flights_deep_link
                    
                    # Generate the booking URL
                    booking_url = get_booking_url(flight, from_location, to_location, travel_date)

                    # Add a "Book Now" button with the correct link
                    st.markdown(
                        f'<a href="{booking_url}" target="_blank"><button style="background-color:#4CAF50;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Book Now</button></a>',
                        unsafe_allow_html=True
                    )
                    st.write("---")

            except KeyError:
                st.error("No flight data found. Try another search.")
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")


