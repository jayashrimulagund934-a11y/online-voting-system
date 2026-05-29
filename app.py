from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "voting_secret_key"

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS voters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        voted INTEGER DEFAULT 0
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        votes INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- DEFAULT CANDIDATES ---------------- #

def add_candidates():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM candidates")

    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO candidates(name) VALUES('Arjun Sharma')")
        c.execute("INSERT INTO candidates(name) VALUES('Priya Patel')")
        c.execute("INSERT INTO candidates(name) VALUES('Rahul Kumar')")

    conn.commit()
    conn.close()

add_candidates()

# ---------------- HOME ---------------- #

@app.route('/')
def home():
    return render_template('index.html')

# ---------------- LOGIN ---------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        phone = request.form['phone']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT * FROM voters WHERE phone=?", (phone,))
        voter = c.fetchone()

        if voter:
            if voter[2] == 1:
                conn.close()
                return "<h2 style='color:red;text-align:center;'>You already voted!</h2>"

        else:
            c.execute("INSERT INTO voters(phone) VALUES(?)", (phone,))
            conn.commit()

        conn.close()

        return redirect(f'/vote/{phone}')

    return render_template('login.html')

# ---------------- VOTE ---------------- #

@app.route('/vote/<phone>', methods=['GET', 'POST'])
def vote(phone):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # SUBMIT VOTE
    if request.method == 'POST' and 'candidate' in request.form:

        candidate_id = request.form['candidate']

        c.execute(
            "UPDATE candidates SET votes = votes + 1 WHERE id=?",
            (candidate_id,)
        )

        c.execute(
            "UPDATE voters SET voted=1 WHERE phone=?",
            (phone,)
        )

        conn.commit()
        conn.close()

        return render_template('success.html')

    # LOAD CANDIDATES
    c.execute("SELECT * FROM candidates")
    candidates = c.fetchall()

    conn.close()

    return render_template(
        'vote.html',
        candidates=candidates
    )

# ---------------- ADMIN LOGIN ---------------- #

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "1234":
            session['admin'] = True
            return redirect('/admin')

        return "<h3 style='color:red;text-align:center;'>Invalid Login</h3>"

    return '''
    <h2 style="text-align:center;">Admin Login</h2>

    <form method="POST" style="text-align:center;">

        <input name="username"
        placeholder="Username"><br><br>

        <input type="password"
        name="password"
        placeholder="Password"><br><br>

        <button type="submit">
            Login
        </button>

    </form>
    '''

# ---------------- ADMIN ---------------- #

@app.route('/admin')
def admin():

    if not session.get('admin'):
        return redirect('/admin-login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM candidates")
    candidates = c.fetchall()

    conn.close()

    return render_template(
        'admin.html',
        candidates=candidates
    )

# ---------------- EDIT ---------------- #

@app.route('/admin/edit', methods=['GET', 'POST'])
def admin_edit():

    if not session.get('admin'):
        return redirect('/admin-login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':

        c.execute("SELECT id FROM candidates")
        ids = c.fetchall()

        for cid in ids:

            new_name = request.form.get(f'name_{cid[0]}')

            if new_name:
                c.execute(
                    "UPDATE candidates SET name=? WHERE id=?",
                    (new_name, cid[0])
                )

        for key in request.form:

            if key.startswith("new_candidate_"):

                name = request.form[key]

                if name.strip():
                    c.execute(
                        "INSERT INTO candidates(name) VALUES(?)",
                        (name,)
                    )

        conn.commit()
        conn.close()

        return redirect('/admin')

    c.execute("SELECT * FROM candidates")
    candidates = c.fetchall()

    conn.close()

    return render_template(
        'admin_edit.html',
        candidates=candidates
    )

# ---------------- DELETE ---------------- #

@app.route('/admin/delete/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):

    if not session.get('admin'):
        return redirect('/admin-login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "DELETE FROM candidates WHERE id=?",
        (candidate_id,)
    )

    conn.commit()
    conn.close()

    return redirect('/admin/edit')

# ---------------- LOGOUT ---------------- #

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ---------------- RUN ---------------- #

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )