from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3
from datetime import date # for default date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, LoginManager, UserMixin, current_user, login_user, logout_user
import json

from quiz_data import questions

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'

# FIX 1: Register chr and ord as Jinja filters (Fixes 'No filter named chr' for A, B, C, D)
app.jinja_env.filters['chr'] = chr
app.jinja_env.filters['ord'] = ord

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
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

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/addprogress', methods = ['GET', 'POST'])
@login_required
def addprogress():
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    
    if request.method == 'POST':
        date = request.form['date']
        title = request.form['title']
        details = request.form['details']
        challenges = request.form['challenges']
        solutions = request.form['solutions']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO progresslogs (user_id, date, title, details, challenges, solutions) VALUES (?, ?, ?, ?, ?, ?)", 
                (current_user.id, date, title, details, challenges, solutions)
            )
            conn.commit()
            flash('Log successful!', 'success')
            conn.close()
            return redirect(url_for('logs')) # Redirect to logs
        except sqlite3.IntegrityError:
            conn.close()
            flash('Please enter a complete log, or change the title (it must be unique).', 'error')
            return redirect(url_for('addprogress'))
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('addprogress'))
        
    return render_template('addprogress.html', username = current_user.username)

@app.route('/dashboard')
@login_required
def dashboard():
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

    # convert SQL below to make secure
    # create table join with users so it also displays the users display name on the screen - html too
    cursor.execute("SELECT date, title, details, challenges, solutions FROM progresslogs WHERE user_id = ? ORDER BY date ASC", (current_user.id,))
    posts = cursor.fetchall()
    conn.close()
    # display no posts if user has none
    # display all post is user has dynamic - for
    
    return render_template('logs.html', posts = posts, username=current_user.username)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            if check_password_hash(user['passward'], password): 
                login_user(User(id=user['id'], username=user['username']))
                session['user_id'] = user['id'] 
                flash('Login successful', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logoff')
@login_required
def logoff():
    logout_user()
    session.pop('user_id', None)
    flash('Log out successful', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        displayName = request.form['displayName']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']

        conn = get_db_connection()
        cursor = conn.cursor()

        if password != confirmPassword:
            flash('passwords do not match', 'error') 
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        try:
            cursor.execute(
                 "INSERT INTO users (username, password, email, display_name) VALUES (?, ?, ?, ?)", 
                 (username, hashed_password, email, displayName)
            )
            conn.commit()
            
            cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
            user=cursor.fetchone()
            login_user(User(id=user['id'], username=user['username']))
            
            flash('Registration successful! You are now logged in.', 'success')
            conn.close()
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register'))
        
    return render_template('register.html')

@app.route('/sdlc')
@login_required
def sdlc():
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))'''
    
    return render_template('sdlc.html', username=current_user.username)

@app.route('/quizz', methods=['GET', 'POST'])
@login_required
def quizz():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes ORDER BY id ASC")
    questions = cursor.fetchall()
    conn.close()

    if 'question_id' not in session or 'score' not in session:
        session['question_id'] = 0
        session['score'] = 0
    
    total_q = len(questions)
    
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        
        current_question_index = session['question_id']
        current_question = questions[current_question_index]
        
        if user_answer and int(user_answer) == current_question['correct_answer']:
            session['score'] += 1
        
        session['question_id'] += 1

        if session['question_id'] >= total_q:
            return redirect(url_for('results'))
        else:
            return redirect(url_for('quizz')) 
    else: 
        if session['question_id'] >= total_q: 
            return redirect(url_for('results'))
        
        current_question_index = session['question_id']
        current_question = questions[current_question_index]
    
        
        return render_template('quizz.html', question=current_question, current_number=current_question_index + 1, total_q=total_q)

@app.route('/results')
@login_required
def results():
    f_score = session.get('score', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM quizzes")
    total_questions = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO score (user_id, score, total_questions, attempt_date) VALUES (?, ?, ?, DATE('now'))",
        (current_user.id, f_score, total_questions)
    )
    conn.commit()
    
    cursor.execute("SELECT id, score, total_questions, attempt_date FROM score WHERE user_id = ? ORDER BY id DESC",(current_user.id,)
    )

    cursor.execute("SELECT MAX(score) FROM score")
    highest_number = cursor.fetchone()[0]

    results = cursor.fetchall()
    conn.close()
    session['question_id'] = 0
    session['score'] = 0

    return render_template('results.html', score=f_score, total=total_questions, results=results, highest_number=highest_number)

if __name__ == '__main__':
    app.run(debug=True)