import streamlit as st
from datetime import datetime, timedelta,timezone
from flask import Flask, request, jsonify, session
from sqlalchemy.orm import sessionmaker
from create_db import engine, User
from werkzeug.security import generate_password_hash, check_password_hash
import os
import hashlib
import bcrypt

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")  # For session management

# Create DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

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
    if request.method != "POST":
        return jsonify({"error": "Use a POST request to register."}), 405  # Method Not Allowed

    data = request.get_json()
    
    print("🚀 Received registration request:", data)  # Debugging line

    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    print(f"📩 Email: {email}, 🔑 Password: {password}, 🏷 Full Name: {full_name}")  # Debugging line

    print(email, password, full_name)
    
    if not email or not password or not full_name:
        return jsonify({"error": "Missing required fields"}), 400

    # existing_user = session.query(User).filter_by(email=email).first()
    # if existing_user:
    #     return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password, full_name=full_name, created_at=datetime.now(timezone.utc))
    session.add(new_user)
    session.commit()

    return jsonify({"message": "User registered successfully!"}), 200

# 🚀 User Login Endpoint
from flask import session  # ✅ Ensure Flask session is imported

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    db_session = SessionLocal()  # ✅ Rename to avoid confusion
    user = db_session.query(User).filter_by(email=email).first()

    if user and user.check_password(password):
        session["user_id"] = user.user_id  # ✅ Now using Flask session correctly
        db_session.close()
        return jsonify({"message": "Login successful"}), 200
    else:
        db_session.close()
        return jsonify({"message": "Invalid credentials"}), 401


# 🚀 User Logout Endpoint
@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)  # Remove user session
    return jsonify({"message": "Logged out successfully"}), 200

# 🚀 Get/Update User Profile
@app.route("/profile", methods=["GET", "PUT"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

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
