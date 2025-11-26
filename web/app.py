from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3
from datetime import date 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, LoginManager, UserMixin, current_user, login_user, logout_user

from quiz_data import questions

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'

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

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id),)
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user['id'], username = user['username'])
    return None

def get_db_connection(): # connect to the database.db 
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    # redirect to the login page 
    return render_template('dashboard.html')

@app.route('/addprogress', methods = ['GET', 'POST'])
@login_required
def addprogress():
    # inesure login
    '''if 'user_id' not in session: 
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    
    if request.method == 'POST':
        # retrive data
        date = request.form['date']
        title = request.form['title']
        details = request.form['details']
        challenges = request.form['challenges']
        solutions = request.form['solutions']

        conn = get_db_connection()
        cursor = conn.cursor()

        try: # Insert the log entry into the progresslogs table
            cursor.execute(
                "INSERT INTO progresslogs (user_id, date, title, details, challenges, solutions) VALUES (?, ?, ?, ?, ?, ?)", 
                (current_user.id, date, title, details, challenges, solutions)
            )
            conn.commit()
            flash('Log successful!', 'success')
            conn.close()
            return redirect(url_for('logs')) 
        except sqlite3.IntegrityError:
            # Handles errors like duplicate titles if the title column is set to UNIQUE
            conn.close()
            flash('Please enter a complete log, or change the title (it must be unique).', 'error')
            return redirect(url_for('addprogress'))
        except Exception as e:
            # Generic error handling
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('addprogress'))
        
        # Render addprogress page
    return render_template('addprogress.html', username = current_user.username)

@app.route('/dashboard')
@login_required
def dashboard():
    # dashboard page
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    
    return render_template('dashboard.html', username=current_user.username)

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

@app.route('/login', methods = ['GET', 'POST'])
def login():
    # Insecure Login
    """ 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        print("connected to db")
        cursor.execute(f"SELECT * FROM users WHERE username = '{username}' AND passward = '{password}'")
        user = cursor.fetchone()
        conn.close()
        print('checked sql')
        if user:
            print('user')
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            print('no user')
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))"""
    
    # Secure Login

    # If the user is already logged in, redirect to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
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
    return render_template('login.html')

@app.route('/logoff')
@login_required
def logoff():
    # Logs out the current user and clears session data. Requires user login.
    logout_user()
    session.pop('user_id', None) # Clear the custom session ID
    flash('Log out successful', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    # new user registration.

    # if user logged in redirect to dashboard.
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Retrieve form data
    if request.method == 'POST':
        username = request.form['username']
        displayName = request.form['displayName']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if passwords match
        if password != confirmPassword:
            flash('passwords do not match', 'error') 
            return redirect(url_for('register'))
        
        # Hash the password for secure storage
        hashed_password = generate_password_hash(password)
        
        try:
            # Insert the new user into the database
            cursor.execute(
                 "INSERT INTO users (username, password, email, display_name) VALUES (?, ?, ?, ?)", 
                 (username, hashed_password, email, displayName))
            conn.commit()

            # Immediately log the new user in after successful registration
            cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
            user=cursor.fetchone()
            login_user(User(id=user['id'], username=user['username']))
            
            flash('Registration successful! You are now logged in.', 'success')
            conn.close()
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            # Handles duplicate username or email if columns are unique
            conn.close()
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    # Render register page   
    return render_template('register.html')

@app.route('/sdlc')
@login_required
def sdlc():
    #insecure login required
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    # render SDLC page
    return render_template('sdlc.html', username=current_user.username)

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

if __name__ == '__main__':
    # Run the application in debug mode
    app.run(debug=True)