from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'  # For sessions and flash messages


# Database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

@app.route('/')
def index():
    # return 'Index page'
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
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
            return redirect(url_for('login'))
    

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
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
                f"INSERT INTO users (username, passward, email, display_name) VALUES ('{username}', '{password}', '{email}', {displayName}')"
            )
            conn.commit()
            flash('Registation succesful! please log in.', ' success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists', 'error')
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register'))
        
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)