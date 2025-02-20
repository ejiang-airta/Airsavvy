import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import urllib.parse
import certifi
import ssl

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

# Application code:
# Streamlit UI
st.title("✈️ Cheapest Airfare Finder")
st.write("Enter your travel details below:")

# Add One-way / Round-trip selection
trip_type = st.radio("Select Trip Type:", ["One-way", "Round-trip"])

# Add Direct / Connecting flight filter
flight_type = st.radio("Flight Type:", ["Any", "Nonstop Only"])

# User inputs for FROM/TO locations and travel dates:
from_location = st.text_input("From (Airport Code)", value="YVR")
to_location = st.text_input("To (Airport Code)", value="PEK")

# Departure date input
departure_date = st.date_input("Select Departure Date", datetime.today() + timedelta(days=2))

# Show return date input ONLY if Round-trip is selected
return_date = None
if trip_type == "Round-trip":
    return_date = st.date_input("Select Return Date", departure_date + timedelta(days=7))  # Default return 1 week later


if st.button("🔍 Search Flights"):
    with st.spinner("Searching for the best flight deals..."):
        st.write(f"Searching for flights from **{from_location}** to **{to_location}** on **{departure_date}**...")

        # Format the query
        query = f"Flights from {from_location} to {to_location} on {departure_date.strftime('%Y-%m-%d')}"
        # If Round-trip is selected, add return date
        if trip_type == "Round-trip" and return_date:
            query += f" returning on {return_date.strftime('%Y-%m-%d')}"
        
        print("Query:", query)

        # API request payload
        payload = {
            "source": "google_search",
            "query": query,
            "parse": "true",
            "trip_type": "roundtrip" if trip_type == "Round-trip" else "oneway",  # Match user's selection
            "filters": {"stops": "0" if flight_type == "Nonstop Only" else "any"  # Apply nonstop filter
            }
        }


        # Make the API call
        response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD), verify=certifi.where())
        #response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD), verify=False)

        if response.status_code == 200:
            data = response.json()

            # Extract flight results
            try:
                flights = data["results"][0]["content"]["results"]["flights"]["results"]
                print("FLIGHT TYPES RETURNED:", [flight["type"] for flight in flights])
                
                # Apply filtering for "Nonstop Only"
                if flight_type == "Nonstop Only":
                    flights = [flight for flight in flights if flight["type"].lower() == "nonstop"]
                
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
                    def get_booking_url(flight, from_location, to_location, departure_date, return_date, trip_type):
                        """Generates a direct booking URL for the given airline, or falls back to Google Flights."""
                        airline = flight["airline"]
                        google_flights_url = flight["url"]  # Fallback option

                        # Convert dates to YYYY-MM-DD format
                        formatted_departure_date = departure_date.strftime("%Y-%m-%d")
                        formatted_return_date = return_date.strftime("%Y-%m-%d") if return_date else ""

                        # Airline-specific booking URL patterns
                        AIRLINE_BOOKING_URLS = {
                            "United": f"https://www.united.com/en/us/book-flight?from={from_location}&to={to_location}&departdate={formatted_departure_date}{'&returndate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "American Airlines": f"https://www.aa.com/reservation/find-flights?origin={from_location}&destination={to_location}&departDate={formatted_departure_date}{'&returnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Alaska Airlines": f"https://www.alaskaair.com/planbook/flights/select?from={from_location}&to={to_location}&departure={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "WestJet": f"https://www.westjet.com/en-ca/book-trip/select-flight?origin={from_location}&destination={to_location}&depart={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Delta": f"https://www.delta.com/flight-search/book-a-flight?Origin={from_location}&Destination={to_location}&DepartureDate={formatted_departure_date}{'&ReturnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Air Canada": f"https://www.aircanada.com/ca/en/aco/home/book?origin={from_location}&destination={to_location}&departureDate={formatted_departure_date}{'&returnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "JetBlue": f"https://book.jetblue.com/B6/webqtrip.html?searchType=NORMAL&origin={from_location}&destination={to_location}&depart={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Spirit Airlines": f"https://www.spirit.com/Default.aspx?search={from_location}-{to_location}-{formatted_departure_date}{'-' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Frontier Airlines": f"https://www.flyfrontier.com/booking?from={from_location}&to={to_location}&depart={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Southwest Airlines": f"https://www.southwest.com/air/booking/select.html?originationAirportCode={from_location}&destinationAirportCode={to_location}&departureDate={formatted_departure_date}{'&returnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Hawaiian Airlines": f"https://www.hawaiianairlines.com/book/flights?searchType=TRIP&origin={from_location}&destination={to_location}&date1={formatted_departure_date}{'&date2=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Sun Country Airlines": f"https://www.suncountry.com/booking/select-flights.html?origin={from_location}&destination={to_location}&departureDate={formatted_departure_date}{'&returnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Porter Airlines": f"https://www.flyporter.com/en-ca/book-flights/where-we-fly?origin={from_location}&destination={to_location}&depart={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Air Transat": f"https://www.airtransat.com/en-CA/book/flight?origin={from_location}&destination={to_location}&departureDate={formatted_departure_date}{'&returnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Air France": f"https://www.airfrance.us/cgi-bin/AF/US/en/common/home/flights/ticket-plane.do?origin={from_location}&destination={to_location}&outboundDate={formatted_departure_date}{'&returnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "KLM": f"https://www.klm.com/travel/us_en/apps/ebt/ebt_home.htm?origin={from_location}&destination={to_location}&departureDate={formatted_departure_date}{'&returnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Emirates": f"https://www.emirates.com/us/english/book/flights?from={from_location}&to={to_location}&depart={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Qatar Airways": f"https://www.qatarairways.com/en-us/search-results?Origin={from_location}&Destination={to_location}&DepartureDate={formatted_departure_date}{'&ReturnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Cathay Pacific": f"https://book.cathaypacific.com/en-us/search-results?Origin={from_location}&Destination={to_location}&DepartureDate={formatted_departure_date}{'&ReturnDate=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Singapore Airlines": f"https://www.singaporeair.com/en_UK/us/plan-and-book/your-booking/?origin={from_location}&destination={to_location}&departure={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}",
                            "Korean Air": f"https://www.koreanair.com/booking/search?bookingType=R&origin={from_location}&destination={to_location}&departure={formatted_departure_date}{'&return=' + formatted_return_date if trip_type == 'Round-trip' else ''}"
                        }

                        # Return the correct URL
                        if airline in AIRLINE_BOOKING_URLS:
                            return AIRLINE_BOOKING_URLS[airline]

                        return google_flights_url  # Fallback if airline not listed

                    
                    # Generate the booking URL
                    booking_url = get_booking_url(flight, from_location, to_location, departure_date, return_date, trip_type)

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


