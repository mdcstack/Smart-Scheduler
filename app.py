from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from openai import OpenAI
import os

# Load .env file
load_dotenv()

app = Flask(__name__)

# Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize extensions
bcrypt = Bcrypt(app)
app.secret_key = SECRET_KEY

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["SmartSchedule"]
users_collection = db["users"]

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- AUTH ROUTES ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if users_collection.find_one({"username": username}):
            return "Username already exists!"

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        users_collection.insert_one({"username": username, "password": hashed_pw})
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users_collection.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            session["username"] = username
            return redirect(url_for("index"))
        return "Invalid credentials!"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


# ---------- CHATBOT ROUTES ----------
@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    bot_reply = response.choices[0].message.content.strip()
    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    app.run(debug=True)
