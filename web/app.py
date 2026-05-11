from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_required, LoginManager, UserMixin, current_user, login_user, logout_user
import sqlite3
import logging  # library for logging security events
import bleach  # library for sanitisation of data
from email_validator import validate_email, EmailNotValidError
from zxcvbn import zxcvbn  # password rules
from forms import RegistrationForm, LoginForm, AddProgressForm  # importing classes from forms file
from flask_wtf import FlaskForm  # library to allow use of wtforms
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField  # fields for forms
from wtforms.validators import DataRequired, Length, Email  # validati0on types within forms
from flask_wtf.csrf import CSRFProtect  # allowing CSRF protection
from contextlib import contextmanager
import os
from dotenv import load_dotenv  # use more secure session key
from datetime import datetime

#region init
app = Flask(__name__)
load_dotenv()  # loads .env file
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')  # For sessions and flash messages
if not app.config['SECRET_KEY']:
    raise ValueError("No FLASK_SECRET_KEY set in environment or .env file!")

# Enable CSRF Protection
csrf = CSRFProtect(app)

# Uploads folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create uploads folder if it doesn't exist

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to /login for unauthorized access
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'error'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username
#endregion

#region subroutines
# run user input to remove dangerous content
def clean_input(s: str, allow_html: bool = False) -> str:
    # Strip dangerous content. allow_html=False removes all tags.
    s = s.strip()
    if allow_html:
        # Allow very limited formatting (adjust tags as needed)
        return bleach.clean(s, tags=['p', 'br', 'strong', 'em'], attributes={}, strip=True)
    else:
        # Remove all HTML
        return bleach.clean(s, tags=[], strip=True)
        
def clean_log_title(s: str) -> str:
    # Strip dangerous content. allow_html=False removes all tags.
    s = s.strip()
    # Remove all HTML
    cleaned = bleach.clean(s, tags=[], strip=True)
    return cleaned[:100]

def clean_log_details(s: str) -> str:
    # Strip dangerous content. allow_html=False removes all tags.
    s = s.strip()    
    # Allow very limited formatting (adjust tags as needed)
    return bleach.clean(s, tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'u'], attributes={}, strip=True)

# check if email is a vaild address instead of just a@b.com
def validate_email_strict(email: str) -> tuple[bool, str]:
    try:
        validate_email(email, check_deliverability=False)
        return True, ""
    except EmailNotValidError as e:
        return False, str(e)
    
# implement password rules    
def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "Password must be at least 10 characters"    
    result = zxcvbn(password)
    if result['score'] < 3:
        warning = result['feedback']['warning'] or "Password is too weak"
        suggestions = " ".join(result['feedback']['suggestions'])
        return False, f"{warning} {suggestions}".strip()   
    return True, "Strong password"

# Load user from database
@login_manager.user_loader
def load_user(user_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, username FROM users WHERE id = ?',
                (user_id,)
            )
            user = cursor.fetchone()  # get the first record from query result

        if user:
            # create instance of user class
            return User(id=user['id'], username=user['username'])
        return None

    except Exception as e:
        # Log the error in development, but don't expose it to user
        print(f"Error loading user {user_id}: {e}")  # Replace with proper logging later
        return None

# Database connection function
@contextmanager
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    # to close the db after the processing is complete
    try:
        yield conn  # keep connection open while actively accessing db
    finally:  # when finished        
        conn.close()

#endregion

@app.route('/')
def index():
    # return 'Index page'
    return render_template('login.html')

@app.route('/add_progress', methods=['GET', 'POST'])
@login_required
def add_progress():
    form = AddProgressForm()  # for prevention of CSRF

    if form.validate_on_submit():
        date_str = form.date.data.strftime('%Y-%m-%d')   # Convert date to string
        title = clean_log_title(form.title.data)  # input sanitisation
        details = clean_log_details(form.details.data)

        # Uploading images
        image_path = None  # initialising image_path
        if form.image.data and form.image.data.filename:
            file = form.image.data  # store image into variable
            print(f"DEBUG: File received - Filename: {file.filename}")
            print(f"DEBUG: File content type: {file.content_type}")

            filename = secure_filename(file.filename)  # run the filename through werkzeug
            unique_filename = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"  # adding metadata to file name
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)  # set the file path with the folder so the app knows where to store the file

            try:
                # upload file to the server
                file.save(file_path)
                image_path = f"uploads/{unique_filename}"
                print(f"DEBUG: Image successfully saved to: {file_path}")
                print(f"DEBUG: image_path saved in DB will be: {image_path}")
            except Exception as e:
                print(f"ERROR saving image: {e}")
                flash(f'Failed to save image: {str(e)}', 'warning')
        else:
            print("DEBUG: No image file was uploaded or filename was empty")


        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO progressLogs (user_id, date, title, details, image_path) VALUES (?, ?, ?, ?, ?)",
                    (current_user.id, date_str, title, details, image_path)
                )
                conn.commit()

            flash('Progress log added successfully!', 'success')
            return redirect(url_for('view_progress'))

        except Exception as e:
            flash('An error occurred while saving your progress.', 'error')
            print(f"ERROR saving progress: {e}")
            import traceback
            traceback.print_exc()  # Print full traceback in console

    return render_template('addProgress.html', form=form, username=current_user.username)
      
@app.route('/dashboard')
@login_required
def dashboard():
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    return render_template('dashboard.html', username=current_user.username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # if user logged in, send to dashboard
        return redirect(url_for('dashboard'))
    
    form = LoginForm()  # reference to the login form class - creating a loginform object

    if form.validate_on_submit():  # run the following code if the data in it is valid
        username = form.username.data.strip()  # cleaning the username and storing it
        password = form.password.data

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # check if user exists - if so return id, username, hashed pw
                cursor.execute( 
                    "SELECT id, username, password FROM users WHERE username = ?",
                    (username,)
                )
                user_row = cursor.fetchone()  # storing the first result

            # IF not null, and passwords match
            if user_row and check_password_hash(user_row['password'], password):
                user = User(id=user_row['id'], username=user_row['username'])
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')

        except Exception as e:
            flash('An error occurred during login. Please try again.', 'error')

    return render_template('login.html', form=form)

@app.route('/logoff')
@login_required
def logoff():
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
    else:'''
    # session.pop('user_id', None)
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))
    # add a link to base.html to run this route -- in the navbar

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        username = clean_input(form.username.data)
        displayName = clean_input(form.displayName.data)
        email = clean_input(form.email.data)
        password = form.password.data

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                hashed_password = generate_password_hash(password)

                cursor.execute(
                    """INSERT INTO Users (username, password, email, display_name)
                       VALUES (?, ?, ?, ?)""",
                    (username, hashed_password, email, displayName)
                )
                conn.commit()  # finalise data in table / save data from query

                # automatically log new user in
                cursor.execute("SELECT id, username FROM Users WHERE username = ?", (username,))
                user_row = cursor.fetchone()

            if user_row:
                new_user = User(id=user_row['id'], username=user_row['username'])
                login_user(new_user)
                flash('Registration successful! Welcome!', 'success')
                return redirect(url_for('dashboard'))

        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')

    return render_template('register.html', form=form)

@app.route('/view_progress', methods=['GET', 'POST'])
@login_required
def view_progress():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, date, title, details, image_path
                   FROM ProgressLogs
                   WHERE user_id = ?
                   ORDER BY date DESC, id DESC""",  # Newer entries first
                (current_user.id,)
            )
            posts = cursor.fetchall()

        return render_template('viewProgress.html', posts=posts, username=current_user.username)

    except Exception as e:
        flash('Error loading your progress logs.', 'error')
        print(f"Error loading progress: {e}")

if __name__ == '__main__':
    app.run(debug=True)