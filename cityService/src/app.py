
from flask import Flask, request, jsonify
from models import User, Info_meteo, db
from flask_cors import CORS
import os
import jwt
import logging

SECRET_KEY = os.environ.get('SECRET_KEY')

app = Flask(__name__)
# app.config['SECRET_KEY'] = SECRET_KEY

CORS(app)
CORS(app, origins="http://localhost:5002")

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql:3306/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/cityevents/<token>', methods=['POST'])
def home(token):
    if request.method == 'POST':
        if request.form['rain'] == 1:
            rain = True
        else:
            rain = False

        if request.form['snow'] == 1:
            snow = True
        else:
            snow = False

        if request.form['max_temp'] == '':
            t_max = None
        else:
            t_max = request.form['max_temp']

        if request.form['min_temp'] == '':
            t_min = None
        else:
            t_min = request.form['min_temp']

        logging.error(token)

        decoded_token = jwt.decode(token, key=SECRET_KEY, algorithms=['HS256'])

        info_meteo = Info_meteo(user_id=decoded_token['user_id'], city=request.form['city_name'],
                                t_max=t_max, t_min=t_min, rain=rain,
                                snow=snow)
        db.session.add(info_meteo)
        db.session.commit()
        return jsonify({'state': 0, 'message': 'City event inviato con successo'})


@app.route("/log_out", methods=['GET', 'POST'])
def log_out():
    return jsonify({'state': 0})


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002)
