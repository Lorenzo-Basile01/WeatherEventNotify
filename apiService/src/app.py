from flask import Flask
from models import User, Info_meteo, db
from kafka import KafkaProducer, KafkaConsumer
import time
import requests
import os
import json
import logging
import threading

SECRET_KEY = os.urandom(32)
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql_api/apiDb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    db.session.commit()

def consuma_da_kafka():
    topic_name = 'weatherInformation'
    time.sleep(10)
    consumer = KafkaConsumer(topic_name, bootstrap_servers='kafka:9095')

    while True:
        for key, value in consumer.poll(1.0).items():
            for record in value:
                # record.value contiene il messaggio come bytes
                json_message = record.value.decode('utf-8')
                dictionary_message = json.loads(json_message)
                logging.error(dictionary_message)

                if not db.session.query(User).filter(User.id == dictionary_message['user_id']).first():
                    user = User(id=dictionary_message['user_id'], telegram_chat_id=dictionary_message['t_chat_id'])
                    db.session.add(user)

                info_meteo = Info_meteo(user_id=dictionary_message['user_id'], city=dictionary_message['city'],
                                        t_max=dictionary_message['tmax'], t_min=dictionary_message['tmin'], rain=dictionary_message['state_r'],
                                        snow=dictionary_message['state_s'])
                with app.app_context():
                    db.session.add(info_meteo)
                    db.session.commit()



def send_kafka(message):
    topic_name = 'weatherNotification'
    time.sleep(10)
    producer = KafkaProducer(bootstrap_servers='kafka:9095')
    json_message = json.dumps(message)
    producer.send(topic_name, json_message.encode('utf-8'))

    producer.flush()


def check_weather():
    api_key = 'a5c03ad3d1dedee0979f9ae116dce6ca'

    while True:
        with app.app_context():

        # table_name = 'user'
        # query = text(f"SHOW TABLES LIKE :table_name")
        # result = db.session.execute(query, {'table_name': table_name}).fetchone()
        # if not result:
        #     print('nessuna tabella user')
        #     time.sleep(10)
        #     continue
            users = db.session.query(User).all()
            print('PRIMO loop')
            for user in users:
                print('SECONDO loop')
                user_city_events = db.session.query(Info_meteo).filter(Info_meteo.user_id == user.id).all()
                for user_city_event in user_city_events:
                    print('TERZO loop ', user_city_event.t_min)
                    city_name = user_city_event.city

                    api_url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}'

                    response = requests.get(api_url)
                    weather_data = response.json()
                    weather_list = weather_data['weather']
                    meteo_data = weather_list[0]['main']

                    meteo_data_r = meteo_data_s = 0

                    if meteo_data == 'Rain':
                        meteo_data_r = 1
                    elif meteo_data == 'Snow':
                        meteo_data_s = 1

                    temp_data = weather_data['main']
                    api_t_min = temp_data['temp_min']
                    api_t_min_C = api_t_min-273.15
                    api_t_max = temp_data['temp_max']
                    api_t_max_C = api_t_max-273.15

                    rain = False
                    snow = False
                    t_max = None
                    t_min = None

                    send = False

                    if meteo_data_r == 1 and user_city_event.rain == 1:
                        rain = True
                        send = True
                    if meteo_data_s == 1 and user_city_event.snow == 1:
                        snow = True
                        send = True
                    if user_city_event.t_max is not None and  api_t_max_C >= user_city_event.t_max:
                        t_max = api_t_max_C
                        send = True
                    if user_city_event.t_min is not None and api_t_min_C <= user_city_event.t_min:
                        t_min = api_t_min_C
                        send = True

                    message_payload = {
                        'city': city_name,
                        'state_r': rain,
                        'state_s': snow,
                        'tmax': t_max,
                        'tmin': t_min,
                        't_chat_id': user.telegram_chat_id
                    }
                    if send:
                        send_kafka(message_payload)

        time.sleep(10)



if __name__ == '__main__':
    time.sleep(20)

    # Avvia le due funzioni in thread separati
    kafka_thread = threading.Thread(target=consuma_da_kafka)
    weather_thread = threading.Thread(target=check_weather)

    kafka_thread.start()
    weather_thread.start()

    kafka_thread.join()
    weather_thread.join()