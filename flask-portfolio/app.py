from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import requests
import os


app = Flask(__name__)


# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "secret-key-123")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///portfolio.db"
)
app.config["GITHUB_USERNAME"] = os.environ.get("GITHUB_USERNAME", "YOUR_USERNAME")


# Extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)


class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(100))


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Track visits
@app.before_request
def track_visits():
    if request.endpoint and request.endpoint != "static":
        try:
            visit = Visitor(page=request.path)
            db.session.add(visit)
            db.session.commit()
        except Exception:
            db.session.rollback()


# Routes
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/projects")
def projects():
    # Try to fetch GitHub repos for the configured username
    username = app.config.get("GITHUB_USERNAME")
    repos = []
    if username and username != "YOUR_USERNAME":
        github_url = f"https://api.github.com/users/{username}/repos"
        try:
            resp = requests.get(github_url, timeout=5)
            if resp.status_code == 200:
                repos = resp.json()
        except Exception:
            repos = []

    return render_template("projects.html", repos=repos)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


@app.route("/analytics")
@login_required
def analytics():
    total_visits = Visitor.query.count()
    home_visits = Visitor.query.filter_by(page="/").count()
    return render_template(
        "analytics.html", total_visits=total_visits, home_visits=home_visits
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)