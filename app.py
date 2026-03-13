from flask import Flask, render_template, request, redirect, session
import pickle
import re
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# load model
model = pickle.load(open("models/model.pkl","rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl","rb"))

# DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]','',text)
    return text


def predict_news(news):

    news = clean_text(news)
    vector = vectorizer.transform([news])

    prediction = model.predict(vector)
    probability = model.predict_proba(vector)

    fake_prob = probability[0][0]
    real_prob = probability[0][1]

    if prediction[0] == 0:
        result = "FAKE NEWS"
        confidence = round(fake_prob * 100,2)
    else:
        result = "REAL NEWS"
        confidence = round(real_prob * 100,2)

    return result, confidence, round(fake_prob*100,2), round(real_prob*100,2)


# LOGIN PAGE
@app.route("/")
def login_page():
    return render_template("login.html")


# LOGIN PROCESS
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
    ).fetchone()

    conn.close()

    if user:
        session["user"] = username
        return redirect("/dashboard")
    else:
        return "Invalid Login"


# REGISTER
@app.route("/register", methods=["POST"])
def register():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()

    conn.execute(
        "INSERT INTO users (username,password) VALUES (?,?)",
        (username,password)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# FORGOT PASSWORD
@app.route("/forgot", methods=["POST"])
def forgot():

    email = request.form["email"]

    return f"Password reset link sent to {email}"


# LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# CLEAR HISTORY
@app.route("/clear_history")
def clear_history():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    conn.execute("DELETE FROM history")

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# DASHBOARD
@app.route("/dashboard", methods=["GET","POST"])
def home():

    if "user" not in session:
        return redirect("/")

    result = None
    confidence = None
    fake_prob = 0
    real_prob = 0

    conn = get_db()

    if request.method == "POST":

        news = request.form["news"]

        result, confidence, fake_prob, real_prob = predict_news(news)

        # SAVE HISTORY IN DATABASE
        conn.execute(
            "INSERT INTO history (text,result) VALUES (?,?)",
            (news[:80] + "...", result)
        )

        conn.commit()

    # LOAD ONLY LAST 10 HISTORY
    history = conn.execute(
        "SELECT * FROM history ORDER BY id DESC LIMIT 10"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        result=result,
        confidence=confidence,
        fake_prob=fake_prob,
        real_prob=real_prob,
        history=history
    )


if __name__ == "__main__":
    app.run(debug=True)