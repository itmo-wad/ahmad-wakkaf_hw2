from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import bcrypt
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "ahmad_key"

# Configure upload folder for profile pictures
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client.get_database('wad')
records = db.users

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")

        user_record = records.find_one({"username": user})
        if user_record:
            user_password = user_record['password']
            if bcrypt.checkpw(password.encode('utf-8'), user_password):
                session['username'] = user
                return redirect(url_for("profile"))
        flash("Credentials not correct", 'error')
        return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if the username already exists
        if records.find_one({"username": username}):
            flash(f'Username "{username}" already exists. Choose a different username.', 'error')
            return render_template("signup.html")  # Render signup page with error

        # Hash and salt the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user into the database
        user_data = {"username": username, "email": email, "password": hashed_password}
        records.insert_one(user_data)

        # Store the username in the session
        session["username"] = username

        flash("Account created successfully!", 'success')  # Success message
        return redirect(url_for("profile"))  # Redirect to profile page

    return render_template("signup.html")

@app.route('/profile', methods=["GET", "POST"])
def profile():
    if 'username' not in session:
        return redirect(url_for("login"))

    username = session['username']
    user_record = records.find_one({"username": username})

    email = user_record.get('email')
    profile_picture = user_record.get('profile_picture', '/static/images/default-profile.png')  # Default profile picture

    if request.method == "POST":
        # Handle password change
        if 'current-password' in request.form and 'new-password' in request.form:
            current_password = request.form.get('current-password')
            new_password = request.form.get('new-password')

            if not bcrypt.checkpw(current_password.encode('utf-8'), user_record['password']):
                return render_template("profile.html", username=username, email=email, profile_picture=profile_picture, password_message="Current password is incorrect")
                
            else:
                hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                records.update_one({"username": username}, {"$set": {"password": hashed_new_password}})
                return render_template("profile.html", username=username, email=email, profile_picture=profile_picture, password_message="Password updated successfully")
               
        # Handle profile picture update
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                records.update_one({"username": username}, {"$set": {"profile_picture": f"/static/uploads/{filename}"}})
                flash('Profile picture updated successfully', 'success')
                return redirect(url_for("profile"))
               
        # Handle profile information update
        if 'new-username' in request.form and 'new-email' in request.form:
            new_username = request.form.get('new-username')
            new_email = request.form.get('new-email')
            existing_user = records.find_one({"username": new_username})
            if existing_user:
                flash(f'Username "{new_username}" already exists. Choose a different username.', 'error')
                return render_template("profile.html", username=username, email=email, profile_picture=profile_picture)

            records.update_one({"username": username}, {"$set": {"username": new_username, "email": new_email}})
            session['username'] = new_username  # Update session username
            username = session['username']
            user_record = records.find_one({"username": username})
            email = user_record.get('email')
            profile_picture = user_record.get('profile_picture', '/static/images/default-profile.png')
            flash('Profile information updated successfully.', 'success')
            return render_template("profile.html", username=username, email=email, profile_picture=profile_picture)
                 
    return render_template("profile.html", username=session['username'], email=email, profile_picture=profile_picture)

@app.route('/logout')
def logout():
    if "username" in session:
        session.pop('username')
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)