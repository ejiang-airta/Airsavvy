import requests

# Your API Key
RAPIDAPI_KEY = "c758d62490msh4cf0b3b0e698d94p10ed5ajsn6b8de9738a86"

# Updated API URL (based on Skyscanner API structure)
url = "https://skyscanner89.p.rapidapi.com/flights/roundtrip/list"  # TRYING A DIFFERENT ENDPOINT

# Updated Query Parameters
querystring = {
    "from": "JFK",                  # Origin IATA Code
    "to": "NCL",                    # Destination IATA Code
    "depart": "2025-03-08",          # Departure Date
    "return": "2025-03-29",          # Return Date
    "adults": "1",                   # Number of Adults
    "currency": "CAD",               # Currency
    "market": "US",                  # Market (Country)
    "locale": "en-US",               # Language
    "cabinClass": "economy"          # Cabin Class
}

# Headers
headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "skyscanner89.p.rapidapi.com"
}

# Make the Request
response = requests.get(url, headers=headers, params=querystring)

# Check Response
if response.status_code == 200:
    print("✅ Success! API Response:")
    print(response.json())
else:
    print(f"❌ Error: {response.status_code} - {response.text}")

# this code working but only returns car rental data:
# import requests

# RAPIDAPI_KEY = "c758d62490msh4cf0b3b0e698d94p10ed5ajsn6b8de9738a86"
# url = "https://skyscanner89.p.rapidapi.com/flights/roundtrip/list"

# # Parameters that worked in your last test (JFK-NCL)
# querystring = {
#     "origin": "JFK",                # IATA code
#     "originId": "JFK",              # Use same as origin
#     "destination": "NCL",           # IATA code
#     "destinationId": "NCL",         # Use same as destination
#     "outDate": "2025-03-08",        # Departure
#     "inDate": "2025-03-29",         # Return
#     "cabinClass": "economy"
# }

# headers = {
#     "x-rapidapi-key": RAPIDAPI_KEY,
#     "x-rapidapi-host": "skyscanner89.p.rapidapi.com"
# }

# response = requests.get(url, headers=headers, params=querystring)
# data = response.json()

# # Parse results (same structure as your last response)
# if "itineraries" in data and data["itineraries"]["results"]:
#     print("Flights found!")
#     for flight in data["itineraries"]["results"][:3]:
#         print(f"Price: {flight['price']['amount']} {flight['price']['currency']}")
# else:
#     print("No flights found. Reasons:")
#     print("- Dates too far ahead (March 2025)")
#     print("- API free tier restrictions")
#     print("- Route not served by airlines")

# # url = "https://skyscanner89.p.rapidapi.com/flights"
# # response = requests.get(url, headers=headers)
# # print("Status Code:", response.status_code)
# # print("New Response:", response.text)

# import requests

# # Your RapidAPI Key
# RAPIDAPI_KEY = "c758d62490msh4cf0b3b0e698d94p10ed5ajsn6b8de9738a86"

# # Adjusted API URL based on RapidAPI's documentation
# url = "https://skyscanner89.p.rapidapi.com/flights/roundtrip/list"

# # Request payload
# payload = {
#     "query": {
#         "market": "US",
#         "locale": "en-US",
#         "currency": "USD",
#         "cabinClass": "economy",
#         "adults": 1,
#         "originPlace": "JFK",
#         "destinationPlace": "LAX",
#         "outboundDate": "2025-03-08",
#         "inboundDate": "2025-03-15"
#     }
# }

# # Headers
# headers = {
#     "content-type": "application/json",
#     "x-rapidapi-key": RAPIDAPI_KEY,
#     "x-rapidapi-host": "skyscanner89.p.rapidapi.com"
# }

# # Make the request
# response = requests.post(url, json=payload, headers=headers)

# # Check Response
# if response.status_code == 200:
#     session_token = response.json().get("sessionToken")
#     print(f"Session Created! Session Token: {session_token}")
# else:
#     print(f"Error: {response.status_code} - {response.text}")
