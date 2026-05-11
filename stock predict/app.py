from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, LoginManager, UserMixin, current_user, login_user, logout_user
import bleach 
from email_validator import EmailNotValidError, validate_email
from zxcvbn import zxcvbn
from forms import RegistrationForm, LoginForm, AddProgressForm # importing classes form forms
from flask_wtf import FlaskForm # libary to allow for use of wtforms
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField # fields
from wtforms.validators import DataRequired, Length, Email # validation types within forms
from flask_wtf.csrf import CSRFProtect # allows CSRF protection
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from quiz_data import questions


app = Flask(__name__)
load_dotenv() # loads .env file
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') # for sessions and flash messages
if not app.config['SECRET_KEY']:
    raise ValueError('No FLASK_SECRET_KEY set in enviroment or .env file! ')

csrf = CSRFProtect(app)

app.jinja_env.filters['chr'] = chr
app.jinja_env.filters['ord'] = ord

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# message when login required
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'error'

class User(UserMixin):
    def __init__(self,id, username):
        self.id = id
        self.username =  username

def clean_input(s: str, allow_html: bool = False) -> str:
    #strip dangouros content: allow_html=false removes all tags.
    s=s.strip()
    # remove all html
    if allow_html:
        return bleach.clean(s, tags=['p', 'br', 'strong', 'em'], attributes=(), strip=True)
    else:     
        return bleach.clean(s, tags=[], strip=True)

def clean_log_title(s: str) -> str:
    #strip dangouros content: allow_html=false removes all tags.
    s=s.strip()
    # remove all html
    cleaned = bleach.clean(s, tags=[], strip=True)
    return cleaned[100]

def clean_log_details(s: str) -> str:
    #strip dangouros content: allow_html=false removes all tags.
    s=s.strip()
    # allow every listed formatting (adjust tags as needed)
    return bleach.clean(s, tags=['p', 'br', 'strong', 'em', 'ul', 'el', 'li' 'u'], attributes=(), strip=True)


#check if email is a valid adress instead of just acb.com
def validate_email_strict(email: str) -> tuple[bool, str]:
    try:
        validate_email(email, check_deliverablity=False)
    except EmailNotValidError as e:
        return False, str(e)

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "Password must be atkeast 10 characters"
    
    result =zxcvbn(password)
    if result['score'] <3:
        warning = result['feedback']['warning'] or "Password is too weak"
        suggestions = " ".join(result['feedback']['suggestions'])
        return False, f"{warning} {suggestions}".strip()
    return True, "Strong password"

@login_manager.user_loader
def load_user(user_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, username FROM Users WHERE id = ?',
                (user_id)
            )
            user = cursor.fetchone()

        if user:
            return User(id=user['id'], username=user['username'])
        return None

    except Exception as e:
        # Log the error in development, but don't expose it to user
        print(f"Error loading user {user_id}: {e}")  # Replace with proper logging later
        return None

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.row # allows accessing columns by name
    try:
        yield conn
    finally: 
        conn.close()

def get_db_connection(): # connect to the database.db 
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    # redirect to the login page 
    return render_template('dashboard.html')

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
                    "INSERT INTO ProgressLogs (user_id, date, title, details, image_path) VALUES (?, ?, ?, ?, ?)",
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
    # dashboard page
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    
    return render_template('login.html', username=current_user.username)

@app.route('/logs', methods = ['GET', 'POST'])
@login_required
def logs():
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Select logs for the current user ordered by date
    cursor.execute("SELECT date, title, details, challenges, solutions FROM progresslogs WHERE user_id = ? ORDER BY date ASC", (current_user.id,))
    posts = cursor.fetchall()
    conn.close()

    # Render logs page
    return render_template('logs.html', posts = posts, username=current_user.username)

@app.route('/edit_log', methods = ['GET', 'POST'])
@login_required
def edit_log():
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    
    if request.method == 'POST':
        # Retrieve form data for the update
        new_date = request.form['date']
        new_title = request.form['title']
        new_details = request.form['details']
        new_challenges = request.form['challenges']
        new_solutions = request.form['solutions']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Update progress logs 
            cursor.execute(
                "UPDATE progresslogs SET date = ?, title = ?, details = ?, challenges = ?, solutions = ? WHERE user_id = ? AND title = ?",
                (new_date, new_title, new_details, new_challenges, new_solutions, current_user.id, new_title)
            )
            conn.commit()
            flash('Log successful!', 'success')
            conn.close()
            return redirect(url_for('logs')) 
        except sqlite3.IntegrityError:
            conn.close()
            flash('Please enter a complete log, or change the title (it must be unique).', 'error')
            return redirect(url_for('edit_log'))
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('edit_log'))
        
    # Render edit_log page
    return render_template('edit_log.html', username = current_user.username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # if user logged in send to dashboard
        return redirect(url_for('dashboard'))
    
    form = LoginForm()  # reference to the login form class

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
                user_row = cursor.fetchone()

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

    """  
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # SELECT user by username
        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Check the hashed password
            if check_password_hash(user['password'], password): 
                # Log the user
                login_user(User(id=user['id'], username=user['username']))
                # Set a session variable
                session['user_id'] = user['id'] 
                flash('Login successful', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Password mismatch
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))
        else:
            # User not found
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
    # Render login page
    return render_template('login.html', form=form)"""

@app.route('/logoff')
@login_required
def logoff():
    # Logs out the current user and clears session data. Requires user login.
    logout_user()
    session.pop('user_id', None) # Clear the custom session ID
    flash('Log out successful', 'success')
    return redirect(url_for('login'))

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
                    """INSERT INTO Users (username, hashed_password, email, display_name)
                       VALUES (?, ?, ?, ?)""",
                    (username, hashed_password, email, displayName)
                )
                conn.commit()

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

@app.route('/sdlc')
@login_required
def sdlc():
    #insecure login required
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    # render SDLC page
    return render_template('sdlc.html', username=current_user.username)
"""?
@app.route('/flashcards', methods=['GET', 'POST'])
@login_required
def flashcards():
    # handles flashcards 
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all quiz/flashcard entries
    cursor.execute("SELECT * FROM quizzes ORDER BY ID ASC")
    card = cursor.fetchall()
    conn.close()

    # Clear existing quiz session state if present
    session.pop('question_id', None)
    session.pop('score', None)

    cards = len(card) 

    # Initialize or retrieve current card index 
    if 'card_id' not in session:
        session['card_id'] = 0

    # Initialize or retrieve flip state
    if 'flipside' not in session:
        session['flipside'] = False
        
    current_index = session['card_id']

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'flip':
            # Toggle the flip state
            session['flipside'] = not session['flipside'] 
        
        elif action == 'next':
            # Move to the next card, reset flip state
            session['flipside'] = False
            if current_index < cards - 1:
                session['card_id'] += 1
                
        elif action == 'previous':
            # Move to the previous card, reset flip state
            session['flipside'] = False 
            if current_index > 0:
                session['card_id'] -= 1
        
        return redirect(url_for('flashcards'))
    
    # reset cards if max cards are exceeded
    if current_index >= cards:
        current_index = 0
        session['card_id'] = 0
        
    if cards > 0:
        current_card = card[current_index]
        current_number = current_index + 1
        flipside = session['flipside'] 

    return render_template('flashcards.html', question=current_card, current_number=current_number, cards=cards, flipside=flipside)
   
@app.route('/quizz', methods=['GET', 'POST'])
@login_required
def quizz():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all quiz questions
    cursor.execute("SELECT * FROM quizzes ORDER BY id ASC")
    questions = cursor.fetchall()
    conn.close()

    # Clear flashcard session state if present
    session.pop('flashcard_id', None)
    
    # Initialize quiz state if not set
    if 'question_id' not in session or 'score' not in session:
        session['question_id'] = 0
        session['score'] = 0
    
    elif 'question_id' not in session:
        session['question_id'] = 0

    total_q = len(questions)
    
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        
        current = session['question_id']
        current_question = questions[current]

        # Get the correct answer index
        correct_answer = current_question['correct_answer']
        correct = chr(ord('A') + correct_answer)

        # Check if an answer was provided and if it's incorrect
        if user_answer and int(user_answer) != current_question['correct_answer']:
            flash(f'Incorrect. The correct answer is {correct}', 'error')

        # Check if an answer was provided and if it's correct
        if user_answer and int(user_answer) == current_question['correct_answer']:
            session['score'] += 1
            flash('Correct', 'success')
        # Move to the next question
        session['question_id'] += 1

        # Check if the quiz is finished
        if session['question_id'] >= total_q:
            return redirect(url_for('results'))
        else:
            return redirect(url_for('quizz')) 
        
    else: # GET request
        # Check if the quiz is already finishe
        if session['question_id'] >= total_q: 
            return redirect(url_for('results'))
        
        # Get the current question details
        current = session['question_id']
        current_question = questions[current]

        return render_template('quizz.html', question=current_question, current_number=current + 1, total_q=total_q)
    
@app.route('/results')
@login_required
def results():
    # Retrieve the final score from the session
    f_score = session.get('score', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the total number of questions
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    total_questions = cursor.fetchone()[0]

    # Insert the latest score into the scores table
    cursor.execute(
        "INSERT INTO score (user_id, score, total_questions, attempt_date) VALUES (?, ?, ?, DATE('now'))",
        (current_user.id, f_score, total_questions)
    )
    conn.commit()
    
    # Fetch all past scores for the user
    cursor.execute("SELECT id, score, total_questions, attempt_date FROM score WHERE user_id = ? ORDER BY id DESC",(current_user.id,)
    )

    # Calculate the highest score achieved
    cursor.execute("SELECT MAX(score) FROM score")
    highest_number = cursor.fetchone()[0]

    results = cursor.fetchall()
    conn.close()

    # Reset quiz state for a new attempt
    session['question_id'] = 0
    session['score'] = 0
    
    return render_template('results.html', score=f_score, total=total_questions, results=results, highest_number=highest_number)
"""
if __name__ == '__main__':
    # Run the application in debug mode
    app.run(debug=True)