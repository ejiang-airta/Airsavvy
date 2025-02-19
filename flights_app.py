import streamlit as st
import requests
import json
import os

# Set API credentials (Use environment variables if set)
OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME", "YOUR_USERNAME")
OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD", "YOUR_PASSWORD")
API_URL = "https://realtime.oxylabs.io/v1/queries"

# Streamlit UI
st.title("✈️ Cheapest Airfare Finder")
st.write("Enter your travel details below:")

# User inputs
from_location = st.text_input("From (Airport Code)", value="SFO")
to_location = st.text_input("To (Airport Code)", value="JFK")
travel_date = st.date_input("Travel Date")

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
        response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD))

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
                    duration_hours = int(flight["duration"].split("h")[0])
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
                    # Define known airline booking URLs
                    AIRLINE_BOOKING_SITES = {
                        "Air Canada": "https://www.aircanada.com",
                        "Delta": "https://www.delta.com",
                        "JetBlue": "https://www.jetblue.com",
                        "United": "https://www.united.com",
                        "American Airlines": "https://www.aa.com",
                        "Southwest": "https://www.southwest.com",
                        "Alaska Airlines": "https://www.alaskaair.com",
                        "WestJet": "https://www.westjet.com"
                    }

                    # Determine the correct booking URL
                    def get_booking_url(flight):
                        airline = flight["airline"]
                        google_flights_url = flight["url"]

                        # If the airline has a known booking website, use it
                        if airline in AIRLINE_BOOKING_SITES:
                            return AIRLINE_BOOKING_SITES[airline]
                        else:
                            return google_flights_url  # Fallback to Google Flights link

                    # Generate the booking URL
                    booking_url = get_booking_url(flight)

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


