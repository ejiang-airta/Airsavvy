import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from create_db import engine, User, FlightSearch, FlightResult

# Configuration
# Booking.com API
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_URL = f"https://{RAPIDAPI_HOST}/api/v1/flights/searchFlights"

# Flask API
BASE_URL = "http://127.0.0.1:5000"

# Create DB session
SessionLocal = sessionmaker(bind=engine)

def safe_strftime(dt, fmt="%b %d, %H:%M"):
    return dt.strftime(fmt) if dt else "N/A"

def parse_datetime(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    except (TypeError, ValueError):
        return None
    
def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{int(hours)}h {int(minutes):02d}m"

def get_luggage(segment):
    try:
        checked = sum(item['luggageAllowance']['maxPiece'] 
                  for item in segment['travellerCheckedLuggage'])
    except (KeyError, IndexError):
        checked = 0
        
    try:
        cabin = sum(item['luggageAllowance']['maxPiece'] 
                for item in segment['travellerCabinLuggage'])
    except (KeyError, IndexError):
        cabin = 0
    
    return f"{checked} checked, {cabin} cabin"

# Streamlit UI
st.title("✈️ Smart Flight Finder")

# Authentication
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"]:
    st.sidebar.write(f"👤 Logged in as: {st.session_state['user']['email']}")
    if st.sidebar.button("Logout"):
        requests.post(f"{BASE_URL}/logout")
        st.session_state["user"] = None
        st.rerun()
else:
    st.sidebar.subheader("🔐 Login / Register")
    auth_mode = st.sidebar.radio("Select Mode:", ["Login", "Register"])
    
    if auth_mode == "Login":
        login_email = st.sidebar.text_input("Email")
        login_password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            response = requests.post(f"{BASE_URL}/login", json={"email": login_email, "password": login_password})
            if response.status_code == 200:
                user_data = response.json()
                st.session_state["user"] = {
                    "email": login_email,
                    "user_id": user_data["user_id"],
                    "session": response.cookies.get("session")
                }
                st.rerun()

    elif auth_mode == "Register":
        register_email = st.sidebar.text_input("Email")
        register_password = st.sidebar.text_input("Password", type="password")
        full_name = st.sidebar.text_input("Full Name")
        if st.sidebar.button("Register"):
            response = requests.post(f"{BASE_URL}/register", json={
                "email": register_email,
                "password": register_password,
                "full_name": full_name
            })
            if response.status_code == 200:
                st.sidebar.success("Registration successful! Please login.")

# Search Form
st.subheader("Search Flights")
col1, col2 = st.columns(2)
with col1:
    from_loc = st.text_input("From (IATA)", value="YVR")
with col2:
    to_loc = st.text_input("To (IATA)", value="PEK")

currency = st.radio("Select Currency:", ["USD", "CAD"], index=0)  # Add currency options
depart_date = st.date_input("Departure", datetime.today() + timedelta(days=2))
trip_type = st.radio("Trip Type", ["One-way", "Round-trip"], horizontal=True)
return_date = st.date_input("Return Date", depart_date + timedelta(days=20)) if trip_type == "Round-trip" else None
top_n = st.slider("Number of top flights to display", 3, 10, 5)  # Restored Top N

cabin_class = st.selectbox("Cabin Class", ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"])
adults = st.number_input("Adults", 1, 5, 1)
children = st.number_input("Children", 0, 5, 0)
flight_type = st.radio("Stops", ["Any", "Nonstop Only"], horizontal=True)

if st.button("🔍 Find Flights"):
    with st.spinner("Searching flights..."):
        session = None
        try:
            # Database setup
            session = SessionLocal()
            flight_search = FlightSearch(
                user_id=st.session_state["user"]["user_id"] if st.session_state["user"] else None,
                origin=from_loc,
                destination=to_loc,
                departure_date=depart_date,
                return_date=return_date,
                trip_type=trip_type,
                created_at=datetime.now()
            )
            session.add(flight_search)
            session.commit()

            # API Request
            params = {
                "currency_code": currency,
                "fromId": f"{from_loc}.AIRPORT",
                "toId": f"{to_loc}.AIRPORT",
                "departDate": depart_date.strftime("%Y-%m-%d"),
                "returnDate": return_date.strftime("%Y-%m-%d") if return_date else "",
                "adults": adults,
                "children": f"{children},17" if children else "0",
                "cabinClass": cabin_class,
                "sort": "CHEAPEST"
            }

            headers = {
                "x-rapidapi-host": RAPIDAPI_HOST.encode("ascii", "ignore").decode(),
                "x-rapidapi-key": RAPIDAPI_KEY.encode("ascii", "ignore").decode()
            }

            response = requests.get(API_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            # print(data) # Debugging print data
            # print("_______________________________")

            # Process flights
            processed_offers = []
            for offer in data.get("data", {}).get("flightOffers", []):
                try:
                    price_data = offer['priceBreakdown']['total']
                    price = price_data['units'] + price_data['nanos']/1e9
                    currency = price_data.get('currencyCode', currency)
                    
                    # Get outbound and return segments
                    outbound = offer['segments'][0]
                    return_flight = offer['segments'][1] if len(offer['segments']) > 1 else None
                    
                    # Process outbound flight
                    outbound_leg = outbound['legs'][0]
                    outbound_carrier = outbound_leg['carriersData'][0]
                    outbound_airline = outbound_carrier.get('name', 'Unknown')
                    outbound_flight_num = outbound_leg.get('flightInfo', {}).get('flightNumber', '')
                    outbound_logo = outbound_carrier.get("logo", "")
                    #outbound_airport = outbound['departureAirport']['cityName']
                    
                    # Process return flight if exists
                    return_info = {}
                    if return_flight:
                        return_leg = return_flight['legs'][0]
                        return_carrier = return_leg['carriersData'][0]
                        return_airline = return_carrier.get('name', 'Unknown')
                        return_logo = return_carrier.get("logo", "")
                        return_info = {
                            'airline': return_carrier.get('name', 'Unknown'),
                            'flight_num': return_leg.get('flightInfo', {}).get('flightNumber', ''),
                            'departure': parse_datetime(return_flight['departureTime']),
                            'arrival': parse_datetime(return_flight['arrivalTime']),
                            'duration': format_duration(return_flight['totalTime']),
                            'stops': len(return_flight['legs']) - 1,
                            'luggage': get_luggage(return_flight),
                            'logo': return_logo
                        }

                    processed_offers.append({
                        'price': price,
                        'currency': currency,
                        'outbound': {
                            'airline': outbound_airline,
                            'flight_num': outbound_flight_num,
                            'departure': parse_datetime(outbound['departureTime']),
                            'arrival': parse_datetime(outbound['arrivalTime']),
                            'duration': format_duration(outbound['totalTime']),
                            'stops': len(outbound['legs']) - 1,
                            'luggage': get_luggage(outbound),
                            'logo': outbound_logo
                        },
                        'return': return_info if return_flight else None,
                        'booking_url': offer.get('deepLink') or f"https://flights.booking.com/flights/{from_loc}-{to_loc}/"
                    })
                    
                except (KeyError, IndexError) as e:
                    continue
            # print(processed_offers) # Debugging print processed_offers

            # Display results
            st.title(f"✈️ {from_loc} ↔ {to_loc} Flight Deals")
            st.markdown(f"## **Top {(top_n)} Cheapest {'Round-trip' if return_date else 'One-way'} Options**")

            for idx, offer in enumerate(processed_offers[:top_n], 1):
                with st.container(border=True):
                    # Header row with option number, price, and book button
                    col_header = st.columns([3, 2, 1])

                    # Modify URL generation to include currency
                    booking_url = f"https://flights.booking.com/flights/{from_loc}.AIRPORT-{to_loc}.AIRPORT/"
                    booking_url += f"?type={'ROUNDTRIP' if return_date else 'ONEWAY'}"
                    booking_url += f"&adults={adults}&cabinClass={cabin_class.upper()}"
                    booking_url += f"&from={from_loc}.AIRPORT&to={to_loc}.AIRPORT"
                    booking_url += f"&depart={depart_date.strftime('%Y-%m-%d')}"
                    if trip_type and return_date:
                        booking_url += f"&return={return_date.strftime('%Y-%m-%d')}"
                    booking_url += f"&currency={currency}&sort=CHEAPEST"  
                   
                    with col_header[0]:
                        st.markdown(f"### Option {idx}")
                    with col_header[1]:
                        st.markdown(f"#### {offer['currency']} {offer['price']:,.2f}")
                    with col_header[2]:
                        if offer['booking_url']:
                            st.markdown(
                                f'<a href="{booking_url}" target="_blank"><button style="background-color:#4CAF50;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Book Now</button></a>',
                                unsafe_allow_html=True)
                        else:
                            st.write("")  # Empty placeholder
        
                    # Flight details columns
                    flight_cols = st.columns(2)
        
                    # Outbound Flight
                    with flight_cols[0]:
                        # Use columns for logo + text
                        col_logo, col_text = st.columns([1, 4])
                        with col_logo:
                            if offer['outbound']['logo']:
                                st.image(offer['outbound']['logo'], width=50, output_format="auto")
                        with col_text:
                            st.markdown(f"**{offer['outbound']['airline']}**  \nFlight {offer['outbound']['flight_num']}")
                        st.write(f"🛫 Outbound: {outbound['departureAirport']['cityName']} → {outbound['arrivalAirport']['cityName']}")
                        st.write(f"**Departure:** {safe_strftime(offer['outbound']['departure'], '%b %d, %Y %H:%M')}")
                        st.write(f"**Arrival:** {safe_strftime(offer['outbound']['arrival'], '%b %d, %Y %H:%M')}")
                        st.write(f"**Duration:** {offer['outbound']['duration']}")
                        st.write(f"**Stops:** {offer['outbound']['stops']} | **Luggage:** {offer['outbound']['luggage']}")

                    # Return Flight (if exists)
                    if offer['return']:
                        with flight_cols[1]:
                             # Use columns for logo + text
                            col_logo_ret, col_text_ret = st.columns([1, 4])
                            with col_logo_ret:
                                if offer['return']['logo']:
                                    st.image(offer['return']['logo'], width=50, output_format="auto")
                            with col_text_ret:
                                st.markdown(f"**{offer['return']['airline']}**  \nFlight {offer['return']['flight_num']}")  # Fixed here

                            st.write(f"🛬 Return: {return_flight['departureAirport']['cityName']} → {return_flight['arrivalAirport']['cityName']}")
                            st.write(f"**Departure:** {safe_strftime(offer['return']['departure'], '%b %d, %Y %H:%M')}")
                            st.write(f"**Arrival:** {safe_strftime(offer['return']['arrival'], '%b %d, %Y %H:%M')}")
                            st.write(f"**Duration:** {offer['return']['duration']}")
                            st.write(f"**Stops:** {offer['return']['stops']} | **Luggage:** {offer['return']['luggage']}")

                    #st.markdown("---")
                    
    
                    # # Return details if available
                    # if offer['return']:
                    #     with st.expander(f"🛬 Return: {to_loc} → {from_loc}", expanded=True):
                    #         col1, col2 = st.columns([1, 4])
                    #         with col1:
                    #             logo = AIRLINE_LOGOS.get(offer['return']['airline'])
                    #             if logo:
                    #                 st.image(logo, width=60)
                    #         with col2:
                    #             st.write(f"**{offer['return']['airline']}** (Flight {offer['return']['flight_num']})")
                    #             st.write(f"**Departure:** {safe_strftime(offer['return']['departure'], '%b %d, %Y %H:%M')}")
                    #             st.write(f"**Arrival:** {safe_strftime(offer['return']['arrival'], '%b %d, %Y %H:%M')}")
                    #             st.write(f"**Duration:** {offer['return']['duration']}")
                    #             st.write(f"**Stops:** {offer['return']['stops']} | **Luggage:** {offer['return']['luggage']}")
                    
                    #st.markdown("---")


                # Save result (ensure your FlightResult model matches these fields)
                # session.add(FlightResult(
                #     search_id=flight_search.search_id,
                #     airline=flight['airlines'],
                #     price=flight['price'],
                #     flight_number=flight['flight_nums'],
                #     departure_time=flight['departure'],
                #     arrival_time=flight['arrival'],
                #     duration=(flight['arrival'] - flight['departure']).total_seconds() // 60,
                #     stops=flight['stops'],
                #     baggage_info=flight['baggage'],
                #     booking_url=flight['booking_url'],    # Changed from 'url' to 'booking_url'
                #     retrieved_at=datetime.now()
                # ))

            session.commit()

        except Exception as e:
            st.error(f"Error: {str(e)}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()