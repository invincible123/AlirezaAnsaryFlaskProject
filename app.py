from flask import Flask, render_template, request, redirect, session, flash
from os import stat, urandom
import sqlite3, time

app = Flask(__name__)

db = sqlite3.connect('myWebsite.db')
cur = db.cursor()
if stat('myWebsite.db').st_size < 1 :
    cur.execute('CREATE TABLE users (user_name nvarchar(50) UNIQUE, pass_word nvarchar(50), full_name nvarchar(25), add_date unix, resume_body text)')
    cur.execute('CREATE TABLE comments (c_take nvarchar(50), c_give nvarchar(50), c_body text)')
    cur.execute("INSERT INTO users VALUES('admin', 'admin', 'مدیر سایت', NULL, NULL)")
    db.commit()
cur.close()
db.close()

@app.route('/')
def Home():
    db = sqlite3.connect('myWebsite.db')
    cur = db.cursor()
    cur.execute("SELECT full_name, datetime(add_date, 'unixepoch'), user_name FROM users WHERE resume_body IS NOT NULL ORDER BY add_date DESC")
    _rows = cur.fetchall()
    cur.close()
    db.close()
    return render_template("home.html", login = session.get('logged_in'), resume = _rows)

@app.route('/register')
def Register():
    return render_template("signup.html", login = session.get('logged_in'))

@app.route('/login')
def Login():
    return render_template("login.html", login = session.get('logged_in'))

@app.route('/logout')
def Logout():
    session['logged_in'] = False
    return Home()

@app.route('/signup', methods = ['POST'])
def Signup():
    _form = request.form
    if not (_form['un'] == "" or _form['pw'] == "" or _form['fn'] == "") :
        try :
            db = sqlite3.connect('myWebsite.db')
            cur = db.cursor()
            cur.execute('INSERT INTO users (user_name, pass_word, full_name) VALUES (?, ?, ?)', (_form['un'], _form['pw'], _form['fn'],))
            db.commit()
            cur.close()
            db.close()
            session['logged_in'] = True
            session['username'] = _form['un']
            return Home()
        except sqlite3.IntegrityError :
            cur.close()
            db.close()
            flash('Username already exists!')
            return redirect('/register')
    flash('Fill up empty fields!')
    return redirect('/register')

@app.route('/signin', methods = ['POST'])
def Signin():
    _form = request.form
    if not (_form['un'] == "" or _form['pw'] == "") :
        db = sqlite3.connect('myWebsite.db')
        cur = db.cursor()
        cur.execute("SELECT full_name FROM users WHERE user_name = ? AND pass_word = ?", (_form['un'], _form['pw'],))
        row = cur.fetchone()
        if row is None :
            cur.close()
            db.close()
            flash('Wrong Authentication!')
            return redirect('/login')
        else :
            cur.close()
            db.close()
            session['logged_in'] = True
            session['username'] = _form['un']
            return Home()
    flash('Fill up empty fields!')
    return redirect('/login')

@app.route('/panel')
def Panel():
    if session.get('logged_in') :
        db = sqlite3.connect('myWebsite.db')
        cur = db.cursor()
        cur.execute('SELECT add_date FROM users WHERE user_name = ?', (session['username'],))
        resume = True
        if cur.fetchone()[0] is None :
            resume = False
        cur.close()
        db.close()
        return render_template("panel.html", login = session.get('logged_in'), RESUME = resume)
    return Login()

@app.route('/apply', methods = ['POST'])
def Apply():
    _form = request.form
    if not _form['body'] == "" :
        db = sqlite3.connect('myWebsite.db')
        cur = db.cursor()
        cur.execute('UPDATE users SET add_date = ? , resume_body = ? WHERE user_name = ?', (time.time(), _form['body'], session['username'],))
        db.commit()
        cur.close()
        db.close()
        return Home()
    flash('Fill up empty fields!')
    return Panel()

@app.route('/password', methods = ['POST'])
def Password():
    _form = request.form
    if not (_form['old'] == "" or _form['new'] == "" or _form['renew'] == "") :
        if _form['new'] != _form['renew'] :
            flash("Passwords don't match!")
            return Panel()
        db = sqlite3.connect('myWebsite.db')
        cur = db.cursor()
        cur.execute('SELECT pass_word FROM users WHERE user_name = ?', (session['username'],))
        _password = cur.fetchone()[0]
        if _form['old'] != _password:
            cur.close()
            db.close()
            flash('Wrong password!')
            return Panel()
        cur.execute('UPDATE users SET pass_word = ? WHERE user_name = ?', (_form['new'], session['username'],))
        db.commit()
        cur.close()
        db.close()
        return Home()
    flash('Fill up empty fields!')
    return Panel()

@app.route("/resume/<string:user_name>/")
def Resume(user_name):
    db = sqlite3.connect('myWebsite.db')
    cur = db.cursor()
    cur.execute("SELECT full_name, resume_body, user_name FROM users WHERE user_name = ?", (user_name,))
    _row = cur.fetchone()
    cur.execute("SELECT c_body, c_give FROM comments WHERE c_take = ?", (user_name,))
    _comment = cur.fetchall()
    cur.close()
    db.close()
    isAdmin = False
    if session.get('logged_in'):
        if session['username'] == 'admin':
            isAdmin = True
    return render_template('resume.html', login = session.get('logged_in'), ROW = _row, CMT = _comment, MODE = isAdmin)

@app.route("/comment/<string:user_name>", methods = ['POST'])
def Comment(user_name):
    _form = request.form
    if not _form['c_body'] == "" :
        db = sqlite3.connect('myWebsite.db')
        cur = db.cursor()
        sender = "Guest"
        if session.get('logged_in') == True :
            sender = session['username']
        cur.execute('INSERT INTO comments VALUES(?, ?, ?)', (user_name, sender, _form['c_body'],))
        db.commit()
        cur.close()
        db.close()
    return Resume(user_name)

@app.route("/delete/<string:user_name>", methods = ['POST'])
def Delete(user_name):
    db = sqlite3.connect('myWebsite.db')
    cur = db.cursor()
    cur.execute('UPDATE users SET add_date = NULL , resume_body = NULL WHERE user_name = ?', (user_name,))
    db.commit()
    cur.close()
    db.close()
    return Home()

@app.route("/edit/<string:user_name>", methods = ['POST'])
def EditResume(user_name):
    db = sqlite3.connect('myWebsite.db')
    cur = db.cursor()
    cur.execute('SELECT resume_body, user_name FROM users WHERE user_name = ?', (user_name,))
    _row = cur.fetchone()
    cur.close()
    db.close()
    return render_template("editResume.html", login = session.get('logged_in'), ROW = _row)

@app.route("/update/<string:user_name>", methods = ['POST'])
def UpdateResume(user_name):
    _form = request.form
    db = sqlite3.connect('myWebsite.db')
    cur = db.cursor()
    cur.execute('UPDATE users SET add_date = ? , resume_body = ? WHERE user_name = ?', (time.time(), _form['body'], user_name,))
    db.commit()
    cur.close()
    db.close()
    return Resume(user_name)

@app.route('/source')
def Source():
    if session.get('logged_in') :
        if session['username'] == 'admin' :
            f = open('source.txt', 'r', encoding="utf-8")
            src = f.read()
            f.close()
            return render_template("source.html", login = session.get('logged_in'), src_body = src)
        else :
            return Panel()
    return Login()

@app.route('/editSource')
def EditSource():
    if session.get('logged_in'):
        if session['username'] == 'admin':
            f = open('source.txt', 'r', encoding="utf-8")
            src = f.read()
            f.close()
            return render_template("editSource.html", login = True, src_body = src)
        else:
            return Panel()
    else:
        return Login()

@app.route('/updateSource', methods = ['POST'])
def UpdateSource():
    inp = request.form['body']
    f = open('source.txt', 'w', encoding = 'utf-8', newline='')
    f.writelines(inp)
    f.close()
    return Source()

if __name__=="__main__":
    app.secret_key = urandom(12)
    app.run()