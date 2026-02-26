from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"


conn = sqlite3.connect("quiz.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS units(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER,
    question TEXT,
    o1 TEXT,
    o2 TEXT,
    o3 TEXT,
    o4 TEXT,
    answer TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS results(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    unit_id INTEGER,
    score INTEGER,
    total INTEGER
)
""")


cursor.execute("""
INSERT INTO users (name,email,password,role)
SELECT 'Admin','admin@gmail.com','admin123','admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email='admin@gmail.com')
""")
conn.commit()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
            (request.form['name'],
             request.form['email'],
             request.form['password'],
             'student')
        )
        conn.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (request.form['email'], request.form['password'])
        )
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/admin_panel' if user['role']=='admin' else '/subjects')

        return "Invalid Login"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/admin_panel')
def admin_panel():
    return render_template('admin_panel.html')


@app.route('/add_subject', methods=['GET','POST'])
def add_subject():
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO subjects (name) VALUES (?)",
            (request.form['subject_name'],)
        )
        conn.commit()
        return redirect('/manage_subjects')
    return render_template('add_subject.html')


@app.route('/manage_subjects')
def manage_subjects():
    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()
    return render_template('manage_subjects.html', subjects=subjects)


@app.route('/edit_subject/<int:id>', methods=['GET','POST'])
def edit_subject(id):

    if request.method == 'POST':
        cursor.execute(
            "UPDATE subjects SET name=? WHERE id=?",
            (request.form['subject_name'], id)
        )
        conn.commit()
        return redirect('/manage_subjects')

    cursor.execute("SELECT * FROM subjects WHERE id=?", (id,))
    subject = cursor.fetchone()
    return render_template('edit_subject.html', subject=subject)


@app.route('/delete_subject/<int:id>')
def delete_subject(id):

    cursor.execute("DELETE FROM subjects WHERE id=?", (id,))
    conn.commit()

    return redirect('/manage_subjects')


@app.route('/add_unit', methods=['GET','POST'])
def add_unit():

    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()

    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO units (subject_id,name) VALUES (?,?)",
            (request.form['subject_id'],
             request.form['unit_name'])
        )
        conn.commit()
        return redirect('/admin_panel')

    return render_template('add_unit.html', subjects=subjects)


@app.route('/add_quiz', methods=['GET','POST'])
def add_quiz():

    cursor.execute("SELECT * FROM units")
    units = cursor.fetchall()

    if request.method == 'POST':
        cursor.execute("""
        INSERT INTO questions
        (unit_id,question,o1,o2,o3,o4,answer)
        VALUES (?,?,?,?,?,?,?)
        """, (
            request.form['unit_id'],
            request.form['question'],
            request.form['o1'],
            request.form['o2'],
            request.form['o3'],
            request.form['o4'],
            request.form['ans']
        ))
        conn.commit()
        return redirect('/admin_panel')

    return render_template('add_quiz.html', units=units)

@app.route('/subjects')
def subjects():
    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()
    return render_template('subjects.html', subjects=subjects)

@app.route('/units/<int:subject_id>')
def units(subject_id):
    cursor.execute("SELECT * FROM units WHERE subject_id=?", (subject_id,))
    units = cursor.fetchall()
    return render_template('units.html', units=units)


@app.route('/quiz/<int:unit_id>', methods=['GET','POST'])
def quiz(unit_id):

    cursor.execute("SELECT * FROM questions WHERE unit_id=?", (unit_id,))
    questions = cursor.fetchall()

    if request.method == 'POST':
        score = 0

        for q in questions:
            if request.form.get(str(q['id'])) == q['answer']:
                score += 1

        cursor.execute(
            "INSERT INTO results (user_id,unit_id,score,total) VALUES (?,?,?,?)",
            (session['user_id'], unit_id, score, len(questions))
        )
        conn.commit()

        return f"Your Score: {score}/{len(questions)}"

    return render_template('quiz.html', questions=questions)


@app.route('/view_results')
def view_results():

    cursor.execute("""
    SELECT users.name, results.score, results.total
    FROM results
    JOIN users ON users.id = results.user_id
    """)

    results = cursor.fetchall()
    return render_template('view_results.html', results=results)


if __name__ == "__main__":
    app.run(debug=True)