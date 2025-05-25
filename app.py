import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from chatbot import get_chat_response

# ✅ Load environment variables
load_dotenv(dotenv_path="config/.env")

# ✅ MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["EVO_AI_DB"]
users = db["users"]
chat_history = db["chat_history"]

# ✅ Initialize Flask App
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ✅ Routes
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("chatbot"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = users.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            return redirect(url_for("chatbot"))
        return "Invalid credentials."
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        users.insert_one({"email": email, "password": password})
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/chatbot")
def chatbot():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("chat.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.json["message"]
    user_id = session.get("user_id", "guest")
    response = get_chat_response(user_input, user_id)
    chat_history.insert_one({"user_id": user_id, "user_input": user_input, "bot_response": response})
    return jsonify({"response": response})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
