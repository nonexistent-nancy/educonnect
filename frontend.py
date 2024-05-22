from flask import Blueprint, render_template, redirect, request, abort, session
from utils import hepatitis_c
import sqlite3
from hashlib import sha256
from datetime import datetime
from utils.basec import generate_string

SCOPE_MAP = {
    "identity": "Wissen, wer du bist",
    "grades": "Noten einsehen",
}

app = Blueprint("skibidiFrontend", __name__)
db = sqlite3.connect("school.db", check_same_thread=False)

hpc = hepatitis_c.Hepatitis_C(app)
@app.errorhandler(401)
def unauthorized(e):
    return redirect("/app/login")

@app.route("/login")
def login_GET():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form['username']
    password = request.form['password']

    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE username=? AND password=?", (username, sha256(password.encode()).hexdigest()))
    res = cur.fetchone()
    cur.close()
    if not res:
        abort(401)
    hpc.login_user(username)
    return redirect("/app/dashboard")

@app.route("/oauth2/authorize")
def o_authorize():
    if not hpc.is_authenticated:
        abort(401)
    client_id = request.args.get("client_id")
    cur = db.cursor()
    cur.execute("SELECT * FROM oauth_apps WHERE client_id=?", (client_id,))
    res = cur.fetchone()
    cur.close()
    session['csrf_token'] = generate_string(64)

    if not res:
        abort(400)
    else:
        return render_template("authorize.html", app=res, user=hpc.current_user, scopes=SCOPE_MAP, csrf_token=session['csrf_token'])

@app.route("/oauth2/grant")
def grant():
    if not hpc.is_authenticated:
        abort(401)
    client_id = request.args.get("client_id")
    if session.get("csrf_token") != request.args.get("csrf_token"):
        abort(400)
    session.pop("csrf_token")
    cur = db.cursor()
    cur.execute("SELECT * FROM oauth_apps WHERE client_id=?", (client_id,))
    res = cur.fetchone()
    cur.close()
    code = generate_string(64)
    redirect_uri = res[4]
    session['oauth_code'] = code
    cur = db.cursor()
    cur.execute("SELECT id FROM user WHERE username=?", (hpc.current_user,))
    user_id = cur.fetchone()[0]
    cur.close()
    cur = db.cursor()

    cur.execute("INSERT INTO oauth_codes (code, client_id, user_id) VALUES (?, ?, ?)", (code, client_id, user_id))
    db.commit()
    cur.close()
    print("Redirecting to", redirect_uri)
    return render_template("redirect.html", url=f"{redirect_uri}?code={code}")

@app.route("/dashboard")
def dashboard():
    if not hpc.is_authenticated:
        abort(401)
    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()
    cur.close()
    cur = db.cursor()
    cur.execute("SELECT * FROM grade WHERE assigned_to=?", (res[0],))
    grades = cur.fetchall()
    cur.close()
    return render_template("dashboard.html", user=res, grades=grades)

@app.route("/prefs/apps")
def apps():
    if not hpc.is_authenticated:
        abort(401)
    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()
    cur.close()
    cur = db.cursor()
    cur.execute("SELECT * FROM oauth_sessions WHERE user_id=?", (res[0],))
    auths = cur.fetchall()
    cur.close()
    print(auths)
    apps = []
    for auth in auths:
        cur = db.cursor()
        cur.execute("SELECT * FROM oauth_apps WHERE client_id=?", (auth[0],))
        app = cur.fetchone()
        cur.close()
        apps.append(app)
    return render_template("apps.html", user=res, scopes=SCOPE_MAP, apps=apps)