from threading import Thread
from kafka import KafkaConsumer
from prometheus_client import Gauge, start_http_server
import telepot
import json, asyncio, time, os, logging, shutil, psutil, schedule
from flask import Flask
from models import User, Info_meteo, db

# Recupera le variabili d'ambiente
SECRET_KEY = os.environ.get('SECRET_KEY')
db_user = os.environ.get('MYSQL_USER')
db_password = os.environ.get('MYSQL_PASSWORD')
db_name = os.environ.get('MYSQL_DATABASE')
db_serv_name = os.environ.get('DB_SERV_NAME')

# configurazione app flask
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{db_user}:{db_password}@{db_serv_name}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

telegram_token = '6731451948:AAHNHAVNRG2EI89uGxPE7b0g11v3FZTpadk'

# metriche prometheus
memory_usage = Gauge('memory_usage_percent', 'Utilizzo della memoria in percentuale')
cpu_usage = Gauge('cpu_usage_percent', 'Utilizzo della CPU in percentuale')
disk_space_used = Gauge('disk_space_used', 'Spazio del disco usato dal servizio in bytes')


# async
def consuma_da_kafka():
    TOPIC_NAME = 'weatherNotification'
    consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers='kafka:9095')
    while True:
        for key, value in consumer.poll(300.0).items():
            for record in value:
                json_message = record.value.decode('utf-8')
                dictionary_message = json.loads(json_message)
                #logging.error(dictionary_message)
                with app.app_context():
                    if db.session.query(Info_meteo).filter((Info_meteo.city == dictionary_message['city']) &
                                                           (Info_meteo.user_id == dictionary_message['user_id'])).first():
                        continue
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
                # await send_t_message(dictionary_message)


# async
def send_t_message():
    with app.app_context():
        messages = db.session.query(User, Info_meteo).join(Info_meteo).filter(User.id == Info_meteo.user_id).all()
    logging.error(messages)
    for user, info in messages:
        rain = False
        if info.rain == 1:
            rain = True
        snow = False
        if info.snow == 1:
            snow = True

        logging.error("SEND KAFKA NOTIFY")
        logging.error(info.city)
        logging.error(user.id)

        min_temperature = int(info.t_min) if info.t_min is not None else None
        max_temperature = int(info.t_max) if info.t_max is not None else None

        msg = {'City': info.city, 'Rain': rain, 'Snow': snow, 'min temperature': min_temperature,
               'max temperature': max_temperature}
        bot = telepot.Bot(token=telegram_token)
        bot.sendMessage(chat_id=user.telegram_chat_id, text=msg)


# await

def measure_metrics():
    logging.error("NOTIFY_METRICS")

    memory_percent = psutil.virtual_memory().percent
    memory_usage.set(memory_percent)

    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_usage.set(cpu_percent)

    disk_space = shutil.disk_usage('/')
    disk_space_used.set(disk_space.used)


schedule.every(1).minutes.do(measure_metrics)
schedule.every(30).seconds.do(consuma_da_kafka)
schedule.every(20).seconds.do(send_t_message)


# Funzione per eseguire il job in un thread separato
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Avvia il thread per eseguire il job in background
scheduler_thread = Thread(target=run_scheduler)
scheduler_thread.start()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()

    start_http_server(5003)

    # asyncio.run(consuma_da_kafka())
