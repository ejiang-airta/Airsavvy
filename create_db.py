from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import clear_mappers

clear_mappers()  # ✅ Clears any previously cached mappers

Base = declarative_base()

# ✅ Users Table
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    flight_type = Column(String, nullable=True)  # Nonstop or Any
    currency = Column(String, nullable=True)  # USD or CAD
    market = Column(String, nullable=True)  # Market Region (US, CA, etc.)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships:
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    flight_searches = relationship("FlightSearch", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hashes and sets the password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Validates a password against the stored hash"""
        return check_password_hash(self.password_hash, password)

# ✅ Subscription Table
class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    plan_name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    payment_method = Column(String, nullable=True)
    subscription_type = Column(String, nullable=True)

    user = relationship("User", back_populates="subscriptions")

# ✅ Flight Search Table
class FlightSearch(Base):
    __tablename__ = 'flight_search'

    search_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    trip_type = Column(String, nullable=False)  # One-way or Round-trip
    search_URL = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="flight_searches")
    flight_results = relationship("FlightResult", back_populates="search", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="search", cascade="all, delete-orphan")

# ✅ Flight Results Table
class FlightResult(Base):
    __tablename__ = 'flight_results'

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    search_id = Column(Integer, ForeignKey('flight_search.search_id'), nullable=False)
    airline = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    flight_number = Column(String, nullable=True)
    departure_time = Column(DateTime, nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    duration = Column(String, nullable=False)
    stops = Column(Integer, nullable=True)
    booking_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    retrieved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    search = relationship("FlightSearch", back_populates="flight_results")

# ✅ Alerts Table
class Alert(Base):
    __tablename__ = 'alerts'

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    search_id = Column(Integer, ForeignKey('flight_search.search_id'), nullable=False)
    alert_type = Column(String, nullable=False)  # e.g., "Price Drop", "Availability Change"
    price_change = Column(Float, nullable=True)
    alert_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="alerts")
    search = relationship("FlightSearch", back_populates="alerts")

# ✅ SQLite Database Connection
engine = create_engine('sqlite:///flight_search_app.db')

# ✅ Create Tables in Database
Base.metadata.create_all(engine)

print("✅ Database tables created successfully!")
