import sqlite3
#import SQLAlchemy

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Users Table
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    gender = Column(String)
    flight_type = Column(String)
    currency = Column(String)
    market = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="user")
    flight_searches = relationship("FlightSearch", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

# Subscription Table
class Subscription(Base):
    __tablename__ = 'subscription'
    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    plan_name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String)
    price = Column(Float)
    payment_method = Column(String)
    subscription_type = Column(String)

    user = relationship("User", back_populates="subscriptions")

# Flight_Search Table
class FlightSearch(Base):
    __tablename__ = 'flight_search'
    search_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    origin = Column(String)
    destination = Column(String)
    departure_date = Column(DateTime)
    return_date = Column(DateTime, nullable=True)
    trip_type = Column(String)
    search_URL = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="flight_searches")
    flight_results = relationship("FlightResult", back_populates="search")
    alerts = relationship("Alert", back_populates="search")

# Flight_Results Table
class FlightResult(Base):
    __tablename__ = 'flight_results'
    result_id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey('flight_search.search_id'))
    airline = Column(String)
    price = Column(Float)
    flight_number = Column(String)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    duration = Column(String)
    stops = Column(Integer)
    booking_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    search = relationship("FlightSearch", back_populates="flight_results")

# Alerts Table
class Alert(Base):
    __tablename__ = 'alerts'
    alert_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    search_id = Column(Integer, ForeignKey('flight_search.search_id'))
    alert_type = Column(String)
    price_change = Column(Float)
    alert_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="alerts")
    search = relationship("FlightSearch", back_populates="alerts")

# SQLite Database
engine = create_engine('sqlite:///flight_search_app.db')

# Create tables
Base.metadata.create_all(engine)

print("✅ Database tables created successfully!")
