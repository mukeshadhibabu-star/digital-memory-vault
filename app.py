from flask import Flask, render_template, request, redirect, session, send_file
import mysql.connector
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates')
app.secret_key = "my_secret_key"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="muKesh@123",
    database="digital_memory_vault"
)

cursor = db.cursor()


# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, password)
        )
        db.commit()

        return redirect('/login')

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):

            session['user_id'] = user[0]

            cursor.execute(
                "INSERT INTO access_logs(user_id,action) VALUES(%s,%s)",
                (user[0], "Login")
            )
            db.commit()

            return redirect('/dashboard')

        return "Invalid Login"

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template('dashboard.html')


# ---------------- UPLOAD ----------------
@app.route('/upload', methods=['GET', 'POST'])
def upload():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        file = request.files['file']
        category_id = request.form['category']

        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        cursor.execute("""
            INSERT INTO documents
            (user_id, category_id, file_name, file_path)
            VALUES (%s,%s,%s,%s)
        """, (session['user_id'], category_id, unique_filename, filepath))

        db.commit()

        cursor.execute("""
            INSERT INTO access_logs(user_id,action)
            VALUES(%s,%s)
        """, (session['user_id'], "Uploaded File"))

        db.commit()

        return redirect('/files')

    return render_template('upload.html')


# ---------------- FILE LIST ----------------
@app.route('/files')
def files():

    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT documents.id,
               documents.file_name,
               categories.category_name
        FROM documents
        JOIN categories ON documents.category_id = categories.id
        WHERE documents.user_id=%s
    """, (session['user_id'],))

    data = cursor.fetchall()

    return render_template('files.html', files=data)


# ---------------- VIEW FILE ----------------
@app.route('/view/<int:file_id>')
def view_file(file_id):

    cursor.execute(
        "SELECT file_path FROM documents WHERE id=%s",
        (file_id,)
    )

    file = cursor.fetchone()

    if not file:
        return "File Not Found"

    filepath = file[0]

    # Text / Code files
    if filepath.endswith(('.txt', '.py', '.java')):

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return f"<pre>{content}</pre>"

    # PDF / Images
    return send_file(filepath)


# ---------------- DELETE FILE ----------------
@app.route('/delete/<int:file_id>')
def delete_file(file_id):

    cursor.execute(
        "SELECT file_path FROM documents WHERE id=%s",
        (file_id,)
    )

    file = cursor.fetchone()

    if file:

        path = file[0]

        if os.path.exists(path):
            os.remove(path)

        cursor.execute(
            "DELETE FROM documents WHERE id=%s",
            (file_id,)
        )
        db.commit()

    return redirect('/files')


# ---------------- PASSWORD VAULT ----------------
@app.route('/passwords', methods=['GET', 'POST'])
def passwords():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        website = request.form['website']
        username = request.form['username']
        password = request.form['password']

        cursor.execute("""
            INSERT INTO password_vault
            (user_id,website,username,password)
            VALUES(%s,%s,%s,%s)
        """, (session['user_id'], website, username, password))

        db.commit()

        return redirect('/passwords')

    cursor.execute("""
        SELECT website, username, password
        FROM password_vault
        WHERE user_id=%s
    """, (session['user_id'],))

    data = cursor.fetchall()

    return render_template('password_vault.html', data=data)


# ---------------- LOGS ----------------
@app.route('/logs')
def logs():

    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute(
        "SELECT * FROM access_logs WHERE user_id=%s",
        (session['user_id'],)
    )

    data = cursor.fetchall()

    return render_template('logs.html', logs=data)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)