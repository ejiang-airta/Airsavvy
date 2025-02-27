import streamlit as st
from datetime import datetime, timedelta,timezone
from flask import Flask, request, jsonify, session
from sqlalchemy.orm import sessionmaker
from create_db import engine, User, SessionLocal
from werkzeug.security import generate_password_hash, check_password_hash
import os
import hashlib
import bcrypt
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401  # Returns 401 if not logged in
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")  # For session management

# Create DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

@app.route("/profile", methods=["GET"])
def get_profile():
    """Retrieve the user's profile preferences."""
    
    db_session = SessionLocal()  # ✅ Create a proper DB session

    # First, check if the user is authenticated via session
    user_email = session.get("user_email")  # Flask session

    # If session-based authentication fails, allow user_id parameter
    if not user_email:
        user_id = request.args.get("user_id")  # Try getting user_id from URL
        if not user_id:
            db_session.close()
            return jsonify({"error": "Unauthorized - No session or user_id"}), 401

        user = db_session.query(User).filter_by(user_id=user_id).first()
    else:
        user = db_session.query(User).filter_by(email=user_email).first()

    if not user:
        db_session.close()
        return jsonify({"error": "User not found"}), 404

    # ✅ Close DB session after fetching user
    profile_data = {
        "email": user.email,
        "flight_type": user.flight_type or "Any",
        "currency": user.currency or "USD",
        "market": user.market or "US"
    }
    db_session.close()

    return jsonify(profile_data)

@app.route("/profile", methods=["PUT"])
def update_profile():
    if "user_email" not in session:
        return jsonify({"error": "Unauthorized access"}), 401
    
    data = request.json
    session_db = SessionLocal()
    user = session_db.query(User).filter_by(email=session["user_email"]).first()
    
    if not user:
        session_db.close()
        return jsonify({"error": "User not found"}), 404
    
    user.currency = data.get("currency", user.currency)
    user.flight_type = data.get("flight_type", user.flight_type)
    user.market = data.get("market", user.market)

    session_db.commit()
    session_db.close()
    
    return jsonify({"message": "Profile updated successfully!"})

st.title("🔑 User Login / Sign Up")

# ✅ Step 1: Check if User is Already Logged In
if "user_email" in st.session_state:
    st.success(f"Welcome back, {st.session_state['user_email']}!")
    if st.button("Log Out"):
        del st.session_state["user_email"]
        st.rerun()
    st.stop()

# ✅ Step 2: Login Form
login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

with login_tab:
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log In"):
        user = session.query(User).filter_by(email=email).first()
        if user and user.password_hash == hashlib.sha256(password.encode()).hexdigest():
            st.success("✅ Login successful!")
            st.session_state["user_email"] = email  # ✅ Store user session
            st.rerun()
        else:
            st.error("❌ Invalid email or password.")

with signup_tab:
    st.subheader("Create an Account")
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Sign Up"):
        existing_user = session.query(User).filter_by(email=new_email).first()
        if existing_user:
            st.error("❌ Email already exists. Try logging in.")
        else:
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            new_user = User(email=new_email, password_hash=hashed_password, full_name="New User")
            session.add(new_user)
            session.commit()
            st.success("✅ Account created successfully! You can now log in.")

# 🚀 User Registration Endpoint
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    print(f"🚀 Received registration request: {data}")  # Debugging print

    # ✅ Create a new SQLAlchemy session
    db_session = SessionLocal()

    # Check if user already exists
    existing_user = db_session.query(User).filter_by(email=email).first()
    if existing_user:
        db_session.close()
        return jsonify({"error": "User already exists"}), 400

    # Hash password
    hashed_password = generate_password_hash(password)

    # ✅ Create new user
    new_user = User(email=email, password_hash=hashed_password, full_name=full_name)

    # ✅ Add user to session and commit
    db_session.add(new_user)
    db_session.commit()
    db_session.close()

    return jsonify({"message": "User registered successfully!"}), 200

# 🚀 User Login Endpoint
from flask import session  # ✅ Ensure Flask session is imported

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    db_session = SessionLocal()  # ✅ Create a SQLAlchemy session
    user = db_session.query(User).filter_by(email=email).first()

    if user and user.check_password(password):
        # ✅ Explicitly return user_id in JSON response
        session["user_id"] = user.user_id  # ✅ Store user_id in Flask session

        return jsonify({
            "message": "Login successful",
            "user_id": user.user_id  # ✅ Explicitly send `user_id`
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# 🚀 User Logout Endpoint
@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)  # Remove user session
    return jsonify({"message": "Logged out successfully"}), 200

# 🚀 Get/Update User Profile
@app.route("/profile", methods=["GET", "PUT"])
def profile():
    user_id = session.get("user_id")  # ✅ Try getting from session
    if not user_id:
        user_id = request.args.get("user_id")  # ✅ Try getting from request (for debugging)

    if not user_id:
        return jsonify({"error": "Unauthorized - No session or user_id"}), 401


    session_db = SessionLocal()
    user = session_db.query(User).filter_by(user_id=user_id).first()

    if request.method == "GET":
        session_db.close()
        return jsonify({
            "email": user.email,
            "full_name": user.full_name,
            "flight_type": user.flight_type,
            "currency": user.currency,
            "market": user.market,
        })

    if request.method == "PUT":
        data = request.json
        user.flight_type = data.get("flight_type", user.flight_type)
        user.currency = data.get("currency", user.currency)
        user.market = data.get("market", user.market)
        
        session_db.commit()
        session_db.close()
        return jsonify({"message": "Profile updated successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
