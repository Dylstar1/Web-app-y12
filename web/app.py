from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3
from datetime import date # for default date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, LoginManager, UserMixin, current_user, login_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'  # For sessions and flash messages

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

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

@app.route('/')
def index():
    # return 'Index page'
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

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO progresslogs (user_id, date, title, details) VALUES (?, ?, ?, ?)", (current_user.id, date, title, details))
            conn.commit()
            flash('Log succesful!', ' success')
            conn.close()
            # give feedback to user 
            # redirect to dashboard -- later ti view logs instead
        except sqlite3.IntegrityError:
            conn.close()
            flash('Please enter a complere log.', 'error')
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
    cursor.execute("SELECT date, title, details FROM progresslogs WHERE user_id = ? ORDER BY date ASC", (current_user.id,))
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

        # cursor.execute("SELECT id, username, password FROM users WHERE username = ? AND password = ?", (username, generate_password_hash(password)))
        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        # "INSERT INTO users (username, password, email, display_name) VALUES (?, ?, ?, ?)", (username, generate_password_hash(password), email, displayName)

        user = cursor.fetchone()
        conn.close()

        if user:
            if check_password_hash(user['password'], password):
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
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
        return redirect(url_for('login'))
    else:'''
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

         # Insecure: Plain-text password comparison
        conn = get_db_connection()
        cursor = conn.cursor()

        # Using parameterized query to avoid SQL injection, but password is still plain-text
        # exists = cursor.execute(f"SELECT COUNT(username) FROM Users WHERE username = '{username}'")
        if password != confirmPassword:
            flash('passwords do not match', 'error') 
            return redirect(url_for('register'))
        
        try:
            cursor.execute(
                 "INSERT INTO users (username, password, email, display_name) VALUES (?, ?, ?, ?)", (username, generate_password_hash(password), email, displayName)
            )
            conn.commit()
            cursor.execute('SELECT id, username FROM users WHERE username = ?', (username))
            user=cursor.fetchone
            login_user(User(id=user['id'], username=user['username']))
            flash('Registation succesful! please log in.', ' success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register'))
        
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)