from flask import Flask, request, render_template
from models.database import db

app = None

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.sqlite3'
    db.init_app(app)
    app.app_context().push()
    return app

app = create_app()

from controllers.controller import *

if __name__ == '__main__':
    app.run() 