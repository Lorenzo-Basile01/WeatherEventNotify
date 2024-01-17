import json

from flask import Flask, render_template, flash, redirect, url_for, jsonify, request
from forms import RegistrationForm, LoginForm
from models import User, db
from flask_login import login_user, current_user, LoginManager, logout_user
from flask_cors import CORS
import os
import logging
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get('SECRET_KEY')

app = Flask(__name__)
#app.config['SECRET_KEY'] = SECRET_KEY

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql:3306/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(int(user_id))
    return None




@app.route("/register", methods=['POST'])
def user_register():
    if request.method == 'POST':
        logging.error(request.form['username'])
        if request.form['username'] == '' or request.form['password'] == '' or request.form['telegramChatId'] == '':
            return jsonify({'state': 1})
        else:
            user = User(username=request.form['username'], password=request.form['password'], telegram_chat_id=request.form['telegramChatId'])
            db.session.add(user)
            db.session.commit()
            # login_user(user)
            # id_user = current_user.id
            # Creazione del token con informazioni della sessione

            #expiration_time = datetime.utcnow() + timedelta(days=1)

            #payload = {'user_id': user.id, 'exp': expiration_time}
            logging.error(SECRET_KEY)
            token = jwt.encode({'user_id': user.id}, key=SECRET_KEY, algorithm='HS256')

            return jsonify({'state': 0, 'token': token})



@app.route("/login", methods=['POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']  # Utilizza l'operatore di accesso diretto []
        password = request.form['password']

        if db.session.query(User).filter(User.username == username,
                                         User.password == password).first():
            user = db.session.query(User).filter(User.username == username,
                                                 User.password == password).first()
            login_user(user)
            id_user = current_user.id


            print(id_user)
            return jsonify({'state': 1, 'token': token})
        else:
            return jsonify({'state': 0})


@app.route("/log_out", methods=['GET', 'POST'])
def log_out():
    logout_user()
    return jsonify({'state': 0})


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5001)
