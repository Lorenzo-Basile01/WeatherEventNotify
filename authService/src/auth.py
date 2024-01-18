
from flask import Flask, jsonify, request
from models import User, db
from flask_cors import CORS
import os
import logging
import jwt

SECRET_KEY = os.environ.get('SECRET_KEY')

app = Flask(__name__)
#app.config['SECRET_KEY'] = SECRET_KEY

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql:3306/authDb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route("/register", methods=['POST'])
def user_register():
    if request.method == 'POST':
        if request.form['username'] == '' or request.form['password'] == '' or request.form['telegramChatId'] == '':
            return jsonify({'state': 1})
        else:
            user = User(username=request.form['username'], password=request.form['password'], telegram_chat_id=request.form['telegramChatId'])
            db.session.add(user)
            db.session.commit()

            # Creazione del token con informazioni della sessione
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

            token = jwt.encode({'user_id': user.id, 't_chat_id': user.telegram_chat_id}, key=SECRET_KEY, algorithm='HS256')


            return jsonify({'state': 0, 'token': token})
        else:
            return jsonify({'state': 1})


@app.route("/log_out", methods=['GET', 'POST'])
def log_out():

    return jsonify({'state': 0})


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5001)
