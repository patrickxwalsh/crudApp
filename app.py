from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import requests
import logging
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Password strength validation function
def check_password_strength(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*()-_=+]', password):
        return False
    return True

# Database setup
def create_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            post_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# create_database()   # DATABASE IS ALREADY CREATED, NO NEED TO RUN THIS METHOD

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not check_password_strength(password):
            flash('Password is not strong enough. It must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character.', 'danger')
            return redirect(url_for('signup'))

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hashed_password))
        conn.commit()
        conn.close()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username_or_email, username_or_email))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            session['username'] = user[1]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard after successful login
        else:
            flash('Invalid username/email or password', 'danger')

        conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM comments")
    comments = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', comments=comments)

@app.route('/create_comment', methods=['POST'])
def create_comment():
    if 'username' not in session:
        flash('Please log in to create a comment', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO comments (content, user_id) VALUES (?, (SELECT id FROM users WHERE username = ?))", (content, session['username']))
        conn.commit()
        conn.close()

        flash('Comment added successfully!', 'success')
        return redirect(url_for('dashboard'))

@app.route('/edit_comment/<int:comment_id>', methods=['GET'])
def edit_comment(comment_id):
    if 'username' not in session:
        flash('Please log in to edit a comment', 'danger')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
    comment = cursor.fetchone()

    conn.close()

    if comment:
        return render_template('dashboard.html', comments=None, edit_comment=comment)
    else:
        flash('Comment not found', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/update_comment/<int:comment_id>', methods=['POST'])
def update_comment(comment_id):
    if 'username' not in session:
        flash('Please log in to update a comment', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("UPDATE comments SET content = ? WHERE id = ?", (content, comment_id))
        conn.commit()
        conn.close()

        flash('Comment updated successfully!', 'success')
        return redirect(url_for('dashboard'))

@app.route('/delete_comment/<int:comment_id>', methods=['GET'])
def delete_comment(comment_id):
    if 'username' not in session:
        flash('Please log in to delete a comment', 'danger')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()

    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)