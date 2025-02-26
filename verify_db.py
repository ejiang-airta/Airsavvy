from sqlalchemy.orm import sessionmaker
from create_db import engine, User

# Create a new session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Fetch all users
users = session.query(User).all()

if users:
    print("\n✅ Current users in the database:")
    for user in users:
        print(f"🔹 ID: {user.user_id}, Email: {user.email}, Full Name: {user.full_name}")
else:
    print("\n⚠️ No users found in the database.")

session.close()

# from sqlalchemy.orm import sessionmaker
# from create_db_old import engine, User, FlightSearch, FlightResult

# # Create DB session
# SessionLocal = sessionmaker(bind=engine)
# session = SessionLocal()

# # Check Users Table
# print("\n--- Users Table ---")
# users = session.query(User).all()
# for user in users:
#     print(f"User ID: {user.user_id}, Email: {user.email}, Currency: {user.currency}, Created: {user.created_at}")

# # Check FlightSearch Table
# print("\n--- Flight Searches ---")
# searches = session.query(FlightSearch).all()
# for search in searches:
#     print(f"Search ID: {search.search_id}, User ID: {search.user_id}, Origin: {search.origin}, Destination: {search.destination}, Trip Type: {search.trip_type}, Search URL: {search.search_URL}, Created: {search.created_at}")

# # Check FlightResult Table
# print("\n--- Flight Results ---")
# results = session.query(FlightResult).all()
# for result in results:
#     print(f"Result ID: {result.result_id}, Search ID: {result.search_id}, Airline: {result.airline}, Price: {result.price}, Departure: {result.departure_time}, Arrival: {result.arrival_time}, Duration: {result.duration}, Booking URL: {result.booking_url}, Retrieved at: {result.retrieved_at}")

# session.close()
