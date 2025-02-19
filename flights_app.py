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
from_location = st.text_input("From (Airport Code)", value="YVR")
to_location = st.text_input("To (Airport Code)", value="LAX")
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

                # Sort flights by price (handling commas in large prices)
                flights = sorted(flights, key=lambda x: int(x["price"].replace("$", "").replace(",", "")))


                # Show only top 3 results
                st.subheader("📌 Top 3 Flight Options:")
                for i, flight in enumerate(flights[:3], 1):
                    st.markdown(f"### ✈️ Option {i}")
                    st.write(f"**Airline:** {flight['airline']}")
                    st.write(f"**Type:** {flight['type']}")
                    st.write(f"**Price:** {flight['price']}")
                    st.write(f"**Duration:** {flight['duration']}")
                    
                    # Add a "Book Now" button with a proper link
                    st.markdown(
                        f'<a href="{flight["url"]}" target="_blank"><button style="background-color:#4CAF50;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Book Now</button></a>',
                        unsafe_allow_html=True
                    )
                    st.write("---")

            except KeyError:
                st.error("No flight data found. Try another search.")
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
