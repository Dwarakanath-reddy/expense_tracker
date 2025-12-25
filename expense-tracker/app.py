from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change to secure secret for production

DB = 'expense_tracker.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('register.html', error='Username and password are required.')
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      (username, generate_password_hash(password)))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Username already taken.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,))
    expenses = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(expenses)

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400
    description = data.get('description')
    amount = data.get('amount')
    date = data.get('date')
    if not description or amount is None or not date:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO expenses (user_id, description, amount, date) VALUES (?, ?, ?, ?)',
                  (session['user_id'], description, amount, date))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Expense added'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (id, user_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Expense deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary', methods=['GET'])
def get_summary():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('''
            SELECT date, SUM(amount) as total
            FROM expenses
            WHERE user_id = ?
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        ''', (user_id,))
        daily = [{'date': row['date'], 'total': row['total']} for row in c.fetchall()]

        c.execute('''
            SELECT SUBSTR(date, 1, 7) as month, SUM(amount) as total
            FROM expenses
            WHERE user_id = ?
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        ''', (user_id,))
        monthly = [{'month': row['month'], 'total': row['total']} for row in c.fetchall()]

        c.execute('''
            SELECT SUBSTR(date,1,4) as year, SUM(amount) as total
            FROM expenses
            WHERE user_id = ?
            GROUP BY year
            ORDER BY year DESC
        ''', (user_id,))
        yearly = [{'year': row['year'], 'total': row['total']} for row in c.fetchall()]

        conn.close()
        return jsonify({'daily': daily, 'monthly': monthly, 'yearly': yearly})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


