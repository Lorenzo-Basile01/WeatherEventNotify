from flask import Flask
from models import User, Info_meteo, db
from kafka import KafkaProducer, KafkaConsumer
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge, start_http_server, Counter
import psutil, shutil, time, requests, os, json, logging, threading

SECRET_KEY = os.environ.get('SECRET_KEY')
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql_api/apiDb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
metrics = PrometheusMetrics(app)


memory_usage = Gauge('memory_usage_percent', 'Utilizzo della memoria in percentuale')
cpu_usage = Gauge('cpu_usage_percent', 'Utilizzo della CPU in percentuale')
disk_space_used = Gauge('disk_space_used', 'Disk space used by the application in bytes')
db_connections_total = Counter('db_connections_total', 'Total number of database connections')


def measure_metrics():
    while True:

        memory_percent = psutil.virtual_memory().percent
        memory_usage.set(memory_percent)

        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_usage.set(cpu_percent)

        disk_space = shutil.disk_usage('/')
        disk_space_used.set(disk_space.used)

        time.sleep(5)


def consuma_da_kafka():
    topic_name = 'weatherInformations'
    # time.sleep(10)
    consumer = KafkaConsumer(topic_name, bootstrap_servers='kafka:9095')

    while True:
        for key, value in consumer.poll(1.0).items():
            for record in value:
                json_message = record.value.decode('utf-8')
                dictionary_message = json.loads(json_message)
                logging.error(dictionary_message)
                with app.app_context():
                    db_connections_total.inc()
                    if not db.session.query(User).filter(User.id == dictionary_message['user_id']).first():
                        user = User(id=dictionary_message['user_id'], telegram_chat_id=dictionary_message['t_chat_id'])

                        db.session.add(user)
                        db.session.commit()

                    info_meteo = Info_meteo(user_id=dictionary_message['user_id'], city=dictionary_message['city'],
                                            t_max=dictionary_message['tmax'], t_min=dictionary_message['tmin'],
                                            rain=dictionary_message['state_r'],
                                            snow=dictionary_message['state_s'])

                    db.session.add(info_meteo)
                    db.session.commit()


def send_kafka(message):
    topic_name = 'weatherNotification'
    # time.sleep(10)
    producer = KafkaProducer(bootstrap_servers='kafka:9095')
    json_message = json.dumps(message)
    producer.send(topic_name, json_message.encode('utf-8'))

    producer.flush()


def check_weather():
    api_key = 'a5c03ad3d1dedee0979f9ae116dce6ca'

    while True:
        time.sleep(20)
        with app.app_context():

            db_connections_total.inc()
            users = db.session.query(User).all()

            for user in users:
                db_connections_total.inc()
                user_city_events = db.session.query(Info_meteo).filter(Info_meteo.user_id == user.id).all()
                for user_city_event in user_city_events:

                    city_name = user_city_event.city
                    api_url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}'

                    response = requests.get(api_url)
                    weather_data = response.json()
                    logging.error(weather_data)
                    weather_list = weather_data['weather']
                    meteo_data = weather_list[0]['main']

                    meteo_data_r = meteo_data_s = 0

                    if meteo_data == 'Rain':
                        meteo_data_r = 1
                    elif meteo_data == 'Snow':
                        meteo_data_s = 1

                    temp_data = weather_data['main']
                    api_t_min = temp_data['temp_min']
                    api_t_min_C = api_t_min - 273.15
                    api_t_max = temp_data['temp_max']
                    api_t_max_C = api_t_max - 273.15

                    rain = 0
                    snow = 0
                    t_max = None
                    t_min = None

                    send = False

                    if meteo_data_r == 1 and user_city_event.rain == 1:
                        rain = 1
                        send = True
                    if meteo_data_s == 1 and user_city_event.snow == 1:
                        snow = 1
                        send = True
                    if user_city_event.t_max is not None and api_t_max_C >= user_city_event.t_max:
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




def loop_execution():
    consuma_da_kafka_thread = threading.Thread(target=consuma_da_kafka)
    measure_metrics_thread = threading.Thread(target=measure_metrics)
    check_weather_thread = threading.Thread(target=check_weather)
    consuma_da_kafka_thread.start()
    measure_metrics_thread.start()
    check_weather_thread.start()

    time.sleep(10)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()

    time.sleep(20)
    start_http_server(5002)
    loop_execution()
