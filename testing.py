import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import urllib.parse
import certifi
import ssl
from pprint import pprint

# # Environment setup:
# # Set API credentials (Use environment variables if set)
# OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME")
# OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD")
# API_URL = "https://realtime.oxylabs.io/v1/queries"

# # # Format the query
# #         query = f"Flights from {from_location} to {to_location} on {departure_date.strftime('%Y-%m-%d')}"
# #         # If Round-trip is selected, add return date
# #         if trip_type == "Round-trip" and return_date:
# #             query += f" returning on {return_date.strftime('%Y-%m-%d')}"
        
# #         print("Query:", query)

# # API request payload



# # Structure payload.
# payload = {
#     'source': 'google_search',
#     'domain': 'nl',
#     'query': 'adidas',
#     'start_page': 11,
#     'pages': 200,
#     'parse': True,
#     'context': [
#         {'key': 'results_language', 'value': 'fr'},
#     ],
# }


# # Get response.
# response = requests.post(API_URL, json=payload, auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD), verify=certifi.where())
# data = response.json()      
# # response = requests.request(
# #     'POST',
# #     'https://realtime.oxylabs.io/v1/queries',
# #     auth=(OXYLABS_USERNAME, OXYLABS_PASSWORD),
# #     json=payload,
# # )

# # Print prettified response to stdout.
# pprint(response.json())
# print(f"DEBUG: Total flights received from API after pagination: {len(data)}")

# code from Deepseek:
# import requests
# import time
import requests
import time

RAPIDAPI_KEY = "c758d62490msh4cf0b3b0e698d94p10ed5ajsn6b8de9738a86"  # Your key

# Step 1: Create Session
create_url = "https://skyscanner-api.p.rapidapi.com/v3/flights/live/itineraryrefresh/create"

payload = {
    "query": {
        "market": "CA",        # Canadian market
        "locale": "en-CA",     # Canadian English
        "currency": "CAD",     # Canadian dollars
        "adults": 1,
        "cabinClass": "economy",
        "queryLegs": [
            {
                "originPlaceId": {"iata": "YVR"},  # Vancouver
                "destinationPlaceId": {"iata": "LAX"},  # Los Angeles
                "date": {
                    "year": 2025,
                    "month": 3,
                    "day": 1
                }
            }
        ]
    }
}

headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "skyscanner-api.p.rapidapi.com",
    "Content-Type": "application/json"
}

# Create session
response = requests.post(create_url, json=payload, headers=headers)

if response.status_code != 200:
    print(f"Error creating session: {response.status_code} - {response.text}")
    exit()

session_data = response.json()
refresh_token = session_data["refreshSessionToken"]
print(f"Session created. Refresh token: {refresh_token}")

# Step 2: Poll Results
poll_url = f"https://skyscanner-api.p.rapidapi.com/v3/flights/live/itineraryrefresh/poll/{refresh_token}"

while True:
    response = requests.get(poll_url, headers={
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "skyscanner-api.p.rapidapi.com"
    })
    
    data = response.json()
    status = data["status"]
    
    if status == "RESULT_STATUS_COMPLETE":
        print("\nFlight results:")
        if len(data["itineraries"]) > 0:
            for idx, itinerary in enumerate(data["itineraries"][:3], 1):
                price = itinerary["price"]["amount"]
                print(f"Itinerary {idx}: {price} CAD")
        else:
            print("No flights found (valid session but empty results)")
        break
        
    elif status == "RESULT_STATUS_INCOMPLETE":
        print(f"Polling... (status: {status})")
        time.sleep(3)
        
    else:
        print(f"Error status: {status}")
        print(data)
        break

# ChatGPT suggested code for testing:

# Replace with your actual RapidAPI key
# rapidapi_key = "7adc9d6b5cmshe51f0b3a73515f6p133e6ajsn82c1f68bb533"

# url = "https://skyscanner-api.p.rapidapi.com/v3e/flights/live/search/create"

# headers = {
#     "Content-Type": "application/json",
#     "x-rapidapi-host": "skyscanner-api.p.rapidapi.com",
#     "x-rapidapi-key": rapidapi_key  # Correct API key format for RapidAPI
# }

# data = {
#     "market": "CA",  # Canada
#     "locale": "en-CA",
#     "currency": "CAD",
#     "queryLegs": [
#         {
#             "originPlaceId": "YVR-sky",  # Vancouver International Airport
#             "destinationPlaceId": "PEK-sky",  # Beijing Capital Airport
#             "date": "2025-02-28"
#         }
#     ],
#     "adults": 1,
#     "cabinClass": "CABIN_CLASS_ECONOMY"
# }
# print("Headers:", headers)

# # Send POST request to create session
# response = requests.post(url, headers=headers, json=data)

# # Check response
# if response.status_code == 200:
#     result = response.json()
#     session_token = result.get("sessionToken")  # Extract session token
#     print("✅ Session Created! Token:", session_token)
# else:
#     print("❌ Error:", response.status_code, response.text)

# code from Gemini:

# Replace with your actual API key
# API_KEY = "7adc9d6b5cmshe51f0b3a73515f6p133e6ajsn82c1f68bb533"

# def create_session(origin, destination, departure_date, adults=1):
#     """Creates a live pricing session with Skyscanner API."""

#     url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/v1.0/create"

#     headers = {
#         "X-RapidAPI-Key": API_KEY,
#         "X-RapidAPI-Host": "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
#         "Content-Type": "application/x-www-form-urlencoded"  # Important for POST data
#     }

#     payload = {
#         "country": "US",  # Example: United States
#         "currency": "USD",  # Example: US Dollars
#         "locale": "en-US",  # Example: English (US)
#         "originplace": origin,  # IATA code (e.g., "JFK")
#         "destinationplace": destination,  # IATA code (e.g., "LAX")
#         "outbounddate": departure_date,  # YYYY-MM-DD (e.g., "2024-03-15")
#         "adults": adults  # Number of adult passengers
#         # Add other parameters as needed (e.g., "infants", "children", "cabinclass")
#     }

#     try:
#       response = requests.post(url, headers=headers, data=payload) # Use data parameter for form-urlencoded
#       response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

#       session_info = response.json()
#       #print(json.dumps(session_info, indent=2)) # Print the full JSON for debugging
      
#       if "location" in response.headers: #Check if location header is present
#         poll_url = response.headers["location"]
#         return poll_url
#       else:
#         print("Error: Location header not found in the response.")
#         return None

#     except requests.exceptions.RequestException as e:
#         print(f"Error: {e}")
#         if response.status_code != 200:
#           print(f"Status Code: {response.status_code}")
#           try:
#               error_data = response.json() #Try to get the error message from the API
#               print(f"Error Details: {error_data}")
#           except json.JSONDecodeError:
#               print("Response was not valid JSON")
#         return None


# # Example usage:
# origin_airport = "JFK"
# destination_airport = "LAX"
# departure_date = "2025-03-15"  #YYYY-MM-DD

# poll_url = create_session(origin_airport, destination_airport, departure_date)

# if poll_url:
#   print(f"Poll URL: {poll_url}")
#   # Now you can use the poll_url to retrieve the actual flight data.
# else:
#   print("Failed to create session.")

# # code from RapidAPI:
# import http.client

# conn = http.client.HTTPSConnection("skyscanner89.p.rapidapi.com")

# headers = {
#     'x-rapidapi-key': "7adc9d6b5cmshe51f0b3a73515f6p133e6ajsn82c1f68bb533",
#     'x-rapidapi-host': "skyscanner89.p.rapidapi.com"
# }

# conn.request("GET", "/flights/one-way/list?date=2025-03-08&origin=YVR&destination=PEK&cabinClass=economy", headers=headers)

# res = conn.getresponse()
# data = res.read()

# print(data.decode("utf-8"))
# print(response.status_code, response.text)
