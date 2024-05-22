from flask import Blueprint, redirect, request, session, jsonify, abort
from utils import hepatitis_c
import sqlite3
from hashlib import sha256
from utils.transfem import TransactionHandler, Transaction
from datetime import datetime, timedelta

app = Blueprint("APIv1",__name__)
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

def auth():
    access_token = request.headers.get("Authorization")
    if not access_token:
        abort(401)
    
    cur = db.cursor()
    print(access_token)
    cur.execute(
        "SELECT * FROM oauth_sessions WHERE token=?", (access_token,)
    )

    res = cur.fetchone()
    print(res)
    cur.close()
    if not res:
        abort(401)
    client,user, tok, expires = res
    if datetime.now().timestamp() > expires:
        cur = db.cursor()
        cur.execute("DELETE FROM oauth_sessions WHERE token=?", (access_token,))
        db.commit()
        cur.close()
        abort(401)

    return client,user, tok, expires

@app.route("/users/me")
def me():
    _, user, _, _ = auth()
    cur = db.cursor()
    cur.execute("SELECT * FROM user WHERE id=?", (user,))
    res = cur.fetchone()
    cur.close()
    data = {
        "id": res[0],
        "username": res[1],
        "rank": res[3],
        "school": res[4],
        "level": res[5],
        "display_name": res[6]
    }
    
    return jsonify(data)

@app.route("/users/me/grades")
def grades():
    user, _, _, _ = auth()
    cur = db.cursor()
    cur.execute("SELECT * FROM grade WHERE assigned_to=?", (user,))
    res = cur.fetchall()
    cur.close()
    return jsonify([
        {
            'id': i[0],
            'assigned_at': i[1],
            'value': i[2],
            'assigned_to': i[3],
            'subject': subject(i[4])["shortName"]
        }
        for i in res
    ])