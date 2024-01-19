from flask import Flask, request, jsonify
from models import User, Info_meteo, db
from flask_cors import CORS
from kafka import KafkaProducer
from urllib.parse import quote
import time
import os
import jwt
import logging
import json

SECRET_KEY = os.environ.get('SECRET_KEY')
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql_city/cityDb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

topic_name = 'weatherInformations'


def send_kafka(message):
    time.sleep(10)
    producer = KafkaProducer(bootstrap_servers='kafka:9095')
    json_message = json.dumps(message)
    producer.send(topic_name, json_message.encode('utf-8'))

    producer.flush()


@app.route('/cityevents/<token>', methods=['POST'])
def home(token):
    if request.method == 'POST':
        if request.form['rain'] == 1:
            rain = 1
        else:
            rain = 0

        if request.form['snow'] == 1:
            snow = 1
        else:
            snow = 0

        if request.form['max_temp'] == '':
            t_max = None
        else:
            t_max = request.form['max_temp']

        if request.form['min_temp'] == '':
            t_min = None
        else:
            t_min = request.form['min_temp']

        logging.error(token)

        encoded_token = quote(token)
        decoded_token = jwt.decode(encoded_token, key=SECRET_KEY, algorithms=['HS256'])

        if not db.session.query(User).filter(User.id == decoded_token['user_id']).first():
            user = User(id=decoded_token['user_id'], telegram_chat_id=decoded_token['t_chat_id'])
            db.session.add(user)

        info_meteo = Info_meteo(user_id=decoded_token['user_id'], city=request.form['city_name'],
                                t_max=t_max, t_min=t_min, rain=rain,
                                snow=snow)

        db.session.add(info_meteo)
        db.session.commit()

        message_payload = {
            'user_id': decoded_token['user_id'],
            'city': info_meteo.city,
            'state_r': info_meteo.rain,
            'state_s': info_meteo.snow,
            'tmax': info_meteo.t_max,
            'tmin': info_meteo.t_min,
            't_chat_id': decoded_token['t_chat_id']
        }

        send_kafka(message_payload)

        return jsonify({'state': 0, 'message': 'City event inviato con successo'})


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == '__main__':
    app.run()
