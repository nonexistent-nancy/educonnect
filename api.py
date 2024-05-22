from flask import Blueprint, redirect, request, session, jsonify, abort
from utils import hepatitis_c
import sqlite3
from hashlib import sha256
from utils.transfem import TransactionHandler, Transaction
from datetime import datetime, timedelta
from oapi import app as OauthAPI


app = Blueprint("APIv1",__name__)
app.register_blueprint(OauthAPI, url_prefix="/oauth")
db = sqlite3.connect("school.db", check_same_thread=False)

hpc = hepatitis_c.Hepatitis_C(app)

handler = TransactionHandler()

def add_grade(value, id, subid):
    cur = db.cursor()
    cur.execute("SELECT * FROM grade WHERE assigned_to=? AND subject=?", (id, subid))
    user_grades = cur.fetchall()
    cur.close()
    user_grades = [
        {
            'id': i[0],
            'assigned_at': i[1],
            'value': i[2],
            'assigned_to': i[3],
            'subject': i[4]
        }
        for i in user_grades
    ]
    after = user_grades.copy()


    new_grade = {
        'id': len(user_grades) + 1,
        'assigned_at': datetime.now(),
        'value': value,
        'assigned_to': id,
        'subject': subid
    }
    after.append(new_grade)
    t = Transaction(hpc.current_user, "add_grade", user_grades, after)
    handler.add_transaction(t)

def subject(id):
    cur = db.cursor()
    cur.execute("SELECT * FROM subject WHERE id=?", (id,))
    res = cur.fetchone()
    cur.close()
    return {
        "id": res[0],
        "fullName": res[1],
        "shortName": res[2],
        "teacher": res[3]
    }

def subject_id(name):
    cur = db.cursor()
    cur.execute("SELECT * FROM subject WHERE shortName=? OR id=? OR fullName=?", (name,name,name))
    res = cur.fetchone()
    cur.close()
    return res[0]

@app.route("/users/<int:id>/assign_grade", methods=["POST"])
def assign_grade_to(id):
    if not hpc.is_authenticated: abort(401)
    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()
    cur.close()
    print(res[3].lower())
    if str(res[3]).lower() != "2": abort(403)
    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE id=?", (id,))
    res = cur.fetchone()
    cur.close()
    add_grade(request.json['value'], id, subject_id(request.json['subject']))
    if not res: abort(404)
    today = datetime.now()
    
    return jsonify({'status': 'pending', 
        'transaction': handler.transactions[-1].__dict__,
        'id': handler.transactions.index(handler.transactions[-1]),
        'promise': { # Promises are what the user can expect to happen in the future. This is a promise that the grade will be assigned by the end of the day.
            'state': 'before_commit',
            'next_commit_at': datetime(today.year, today.month, today.day, 23, 59, 59).isoformat(),
            'next_commit_in': (datetime(today.year, today.month, today.day, 23, 59, 59) - today).total_seconds(),
            'promise_url': '/api/v1/transactions/' + str(handler.transactions.index(handler.transactions[-1]))
    }})



@app.route("/users/me")
def me():
    if not hpc.is_authenticated: abort(401)
    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()
    cur.close()
    cur = db.cursor()
    grades = cur.fetchall()
    cur.close()
    data = {
        "id": res[0],
        "username": hpc.current_user,
        "rank": res[3],
        "school": res[4],
        "level": res[5],
    }
    
    return jsonify(data)

@app.route("/users/me/grades")
def my_grades():
    if not hpc.is_authenticated: abort(401)
    cur = db.cursor()
    cur.execute("SELECT id FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()[0]
    cur.close()
    cur = db.cursor()
    cur.execute("SELECT * FROM grade WHERE assigned_to=?", (res, ))
    users_grades = cur.fetchall()
    cur.close()
    return jsonify({
        "grades": [
            {
                "subject": subject(i[0]),
                'value': i[2],
                'assigned': datetime.fromtimestamp(int(i[3])).isoformat()
            } for i in users_grades
        ]
    })

@app.route("/login", methods=["POST"])
def login():
    username = request.json['username']
    password = request.json['password']

    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE username=? AND password=?", (username, sha256(password.encode()).hexdigest()))
    res = cur.fetchone()
    cur.close()
    if not res:
        abort(401)
    hpc.login_user(username)
    return jsonify({'status': 'ok'})

@app.route("/public/key")
def public_key():
    cur = db.cursor()
    cur.execute("SELECT public_key FROM school_configuration")
    res = cur.fetchone()
    cur.close()
    return jsonify({'public_key': res[0].decode()})

@app.route("/transactions/<int:id>")
def transaction(id):
    if not hpc.is_authenticated: abort(401)
    if id >= len(handler.transactions): abort(404)
    return jsonify(handler.transactions[id].__dict__)

@app.route("/transactions/mine")
def transactions_by_me():
    if not hpc.is_authenticated: abort(401)
    cur = db.cursor()
    cur.execute("SELECT id FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()[0]
    cur.close()
    return jsonify([i.__dict__ for i in handler.transactions if i.user == res])

@app.route("/transactions/*")
def transactions_affecting_me():
    if not hpc.is_authenticated: abort(401)
    cur = db.cursor()
    cur.execute("SELECT id FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()[0]
    cur.close()
    results = []
    for i in handler.transactions:
        if res in [j.get('assigned_to') for j in i.before] or res in [j.get('assigned_to') for j in i.after]:
            results.append(i)

    return jsonify([i.__dict__ for i in results])

@app.route("/transactions/<int:id>/dispute", methods=["POST"])
def dispute_transaction(id):
    if not hpc.is_authenticated: abort(401)
    if id >= len(handler.transactions): abort(404)
    handler.transactions[id].dispute()
    return jsonify({'status': 'ok'})

@app.route("/transactions/disputed")
def disputed_transactions():
    if not hpc.is_authenticated: abort(401)
    cur = db.cursor()
    cur.execute("SELECT privilege FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()
    cur.close()
    if res[0] != 3: abort(403)
    return jsonify([i.__dict__ for i in handler.transactions if i.disputed])

@app.route("/transactions/<int:id>/resolve", methods=["POST"])
def resolve_dispute(id):
    if not hpc.is_authenticated: abort(401)
    if id >= len(handler.transactions): abort(404)
    cur = db.cursor()
    cur.execute("SELECT privilege FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()
    cur.close()
    if res[0] != 3: abort(403)
    handler.transactions[id].disputed = False
    return jsonify({'status': 'ok'})

@app.route("/transactions/<int:id>/delete", methods=["POST"])
def delete_transaction(id):
    if not hpc.is_authenticated: abort(401)
    if id >= len(handler.transactions): abort(404)
    cur = db.cursor()
    cur.execute("SELECT privilege FROM user WHERE username=?", (hpc.current_user,))
    res = cur.fetchone()
    cur.close()
    if res[0] != 3: abort(403)
    handler.transactions.pop(id)
    return jsonify({'status': 'ok'})


@app.route("/oauth/authorize", methods=["POST"])
def authorize():
    cur = db.cursor()
    code = request.json['code']
    client_secret = request.json['client_secret']
    print(request.json)
    cur.execute("SELECT client_secret FROM oauth_apps WHERE client_id=?", (request.json['client_id'],))
    res = cur.fetchone()

    cur.close()
    print(client_secret, res[0])
    if not res or res[0] != client_secret: abort(403)
    if not res: abort(404)
    
    cur = db.cursor()
    cur.execute("SELECT code, user_id FROM oauth_codes WHERE client_id=?", (request.json['client_id'],))
    print(request.json['client_id'])
    res = cur.fetchone()
    cur.close()
    if not res: abort(404)
    print(res[0], code)
    
    if res[0] == code:
        bearer_token = sha256(code.encode()).hexdigest()
        expiry = datetime.now() + timedelta(days=30)
        cur = db.cursor()
        # client_id,user_id,token,expiry
        cur.execute("INSERT INTO oauth_sessions (client_id, user_id, token, token_expires) VALUES (?, ?, ?, ?)", (request.json['client_id'], res[1], bearer_token, expiry.timestamp()))
        db.commit()
        cur.close()
        cur = db.cursor()
        cur.execute("DELETE FROM oauth_codes WHERE client_id=?", (request.json['client_id'],))
        db.commit()
        cur.close()
        return jsonify({'token': bearer_token, 'expires': expiry.timestamp()})
    else:
        print("Code mismatch")
        abort(403)