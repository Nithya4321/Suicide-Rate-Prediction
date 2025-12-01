from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pickle

app = Flask(__name__)
app.secret_key = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Load ML model and encoders
with open("pickle/model.pkl", "rb") as f:
    model = pickle.load(f)

with open("pickle/robust.pkl", "rb") as f:
    robust = pickle.load(f)

with open("pickle/label.pkl", "rb") as f:
    label = pickle.load(f)
    label_country = label["country"]
    label_year = label["year"]

# Define countries for dropdown
countries = ['Albania', 'Argentina', 'Australia', 'Austria', 'Bahamas', 'Belgium', 'Brazil',
             'Canada', 'Chile', 'Colombia', 'Croatia', 'Cuba', 'Czech Republic', 'Denmark',
             'Ecuador', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'India', 'Ireland',
             'Israel', 'Italy', 'Japan', 'Mexico', 'Netherlands', 'New Zealand', 'Norway',
             'Poland', 'Portugal', 'Republic of Korea', 'Romania', 'Russian Federation',
             'Slovakia', 'Slovenia', 'South Africa', 'Spain', 'Sri Lanka', 'Sweden',
             'Switzerland', 'Thailand', 'Turkey', 'Ukraine', 'United Kingdom', 'United States']

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))

# Create DB once
with app.app_context():
    db.create_all()

# Home page
@app.route("/")
def home():
    return render_template("home.html", countries=countries)

# Show Register Page + Handle Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(username=username).first():
            return render_template("register.html", message="Username already exists.")

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

# Show Login Page + Handle Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]  # Get the email from the form
        password = request.form["password"]  # Get the password from the form

        # Query the database for a user with the provided email
        user = User.query.filter_by(email=email).first()  # Filter by email, not username
        if user and check_password_hash(user.password, password):
            session["username"] = user.username  # Store the username in session (optional)
            return redirect("/index")  # Redirect to home page after successful login
        else:
            return render_template("login.html", message="Invalid credentials.")  # Show error message on failure

    return render_template("login.html")
# Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

# Prediction route
@app.route("/index", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        try:
            country = request.form["country"]
            year = int(request.form["year"])
            gender = int(request.form["gender"])
            age_group = int(request.form["age_group"])
            suicide_count = int(request.form["suicide_count"])
            population = int(request.form["population"])
            gdp_for_year = int(request.form["gdp_for_year"])
            gdp_per_capita = int(request.form["gdp_per_capita"])
            generation = int(request.form["generation"])

            country_encoded = label_country.transform([country])[0]
            year_encoded = label_year.transform([year])[0]
            scaled = robust.transform([[suicide_count, population, gdp_for_year, gdp_per_capita]])
            suicide_count, population, gdp_for_year, gdp_per_capita = scaled[0]

            prediction = model.predict([[country_encoded, year_encoded, gender, age_group,
                                         suicide_count, population, gdp_for_year,
                                         gdp_per_capita, generation]])
            output = round(prediction[0], 3)
            result = f"Suicide Rate is {output} per 100k population."
        except Exception as e:
            result = f"Error in prediction: {e}"

        return render_template("index.html", countries=countries, prediction_text=result)

    return render_template("index.html", countries=countries)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
