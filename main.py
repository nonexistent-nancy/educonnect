from flask import Flask, render_template, redirect, session, request
import sqlite3
from api import app as API
from frontend import app as Frontend


app = Flask("skibidi_schulserver")
app.config['SECRET_KEY'] = 'meep'
app.register_blueprint(API, url_prefix="/api/v1")
app.register_blueprint(Frontend, url_prefix="/app")

@app.errorhandler(401)
def unauthorized(e):
    return redirect("/app/login")

if __name__ == "__main__":
    app.run(debug=True, port=5000)