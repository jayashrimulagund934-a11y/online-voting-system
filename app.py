from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.secret_key = "voting_secret_key"

# ---------------- DATABASE ---------------- #

def init_db():

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Voters Table
    c.execute('''

    CREATE TABLE IF NOT EXISTS voters (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        phone TEXT UNIQUE,

        voted INTEGER DEFAULT 0
    )

    ''')

    # Candidates Table
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

# ---------------- ADD DEFAULT CANDIDATES ---------------- #

def add_candidates():

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM candidates")

    if c.fetchone()[0] == 0:

        c.execute(
            "INSERT INTO candidates(name) VALUES('Arjun Sharma')"
        )

        c.execute(
            "INSERT INTO candidates(name) VALUES('Priya Patel')"
        )

        c.execute(
            "INSERT INTO candidates(name) VALUES('Rahul Kumar')"
        )

    conn.commit()
    conn.close()

add_candidates()

# ---------------- HOME PAGE ---------------- #

@app.route('/')
def home():

    return render_template('index.html')

# ---------------- LOGIN PAGE ---------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        phone = request.form['phone']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Check voter
        c.execute(
            "SELECT * FROM voters WHERE phone=?",
            (phone,)
        )

        voter = c.fetchone()

        # Already voted
        if voter:

            if voter[2] == 1:

                conn.close()

                return '''

                <h2 style="font-family:sans-serif;
                text-align:center;
                margin-top:50px;
                color:red;">

                You already voted!

                </h2>

                '''

        else:

            c.execute(
                "INSERT INTO voters(phone) VALUES(?)",
                (phone,)
            )

            conn.commit()

        conn.close()

        return redirect(f'/vote/{phone}')

    return render_template('login.html')

# ---------------- VOTING PAGE ---------------- #

@app.route('/vote/<phone>', methods=['GET', 'POST'])
def vote(phone):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Submit Vote
    if request.method == 'POST':

        candidate_id = request.form['candidate']

        # Add vote
        c.execute(

            "UPDATE candidates SET votes = votes + 1 WHERE id=?",

            (candidate_id,)
        )

        # Mark voter
        c.execute(

            "UPDATE voters SET voted=1 WHERE phone=?",

            (phone,)
        )

        conn.commit()
        conn.close()

        return render_template('success.html')

    # Show candidates
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

        # Default Credentials
        if username == "admin" and password == "1234":

            session['admin'] = True

            return redirect('/admin')

        else:

            return '''

            <h2 style="
            text-align:center;
            color:red;
            margin-top:50px;
            font-family:sans-serif;">

            Invalid Username or Password

            </h2>

            '''

    return '''

    <html>

    <head>

    <title>Admin Login</title>

    <style>

    body{

        font-family:sans-serif;

        display:flex;

        justify-content:center;

        align-items:center;

        height:100vh;

        background:linear-gradient(
        135deg,
        #0f172a,
        #2563eb
        );
    }

    .box{

        background:white;

        padding:40px;

        border-radius:20px;

        width:300px;

        text-align:center;
    }

    input{

        width:100%;

        padding:12px;

        margin:10px 0;
    }

    button{

        width:100%;

        padding:12px;

        background:#2563eb;

        color:white;

        border:none;

        border-radius:10px;
    }

    </style>

    </head>

    <body>

    <div class="box">

    <h2>🔐 Admin Login</h2>

    <form method="POST">

    <input type="text"
    name="username"
    placeholder="Username"
    required>

    <input type="password"
    name="password"
    placeholder="Password"
    required>

    <button type="submit">
    Login
    </button>

    </form>

    </div>

    </body>

    </html>

    '''

# ---------------- ADMIN RESULTS ---------------- #

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

# ---------------- EDIT CANDIDATES ---------------- #

@app.route('/admin/edit', methods=['GET', 'POST'])
def admin_edit():

    if not session.get('admin'):

        return redirect('/admin-login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # SAVE CHANGES
    if request.method == 'POST':

        # UPDATE OLD CANDIDATES
        c.execute("SELECT id FROM candidates")

        ids = c.fetchall()

        for candidate_id in ids:

            new_name = request.form.get(
                f'name_{candidate_id[0]}'
            )

            if new_name:

                c.execute(

                    "UPDATE candidates SET name=? WHERE id=?",

                    (new_name, candidate_id[0])
                )

        # ADD NEW CANDIDATES
        for key in request.form:

            if key.startswith("new_candidate_"):

                candidate_name = request.form[key]

                if candidate_name.strip() != "":

                    c.execute(

                        "INSERT INTO candidates(name) VALUES(?)",

                        (candidate_name,)
                    )

        conn.commit()
        conn.close()

        return redirect('/admin')

    # SHOW CANDIDATES
    c.execute("SELECT * FROM candidates")

    candidates = c.fetchall()

    conn.close()

    return render_template(

        'admin_edit.html',

        candidates=candidates
    )

# ---------------- DELETE CANDIDATE ---------------- #

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

    session.pop('admin', None)

    return redirect('/')

# ---------------- RUN APP ---------------- #

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )