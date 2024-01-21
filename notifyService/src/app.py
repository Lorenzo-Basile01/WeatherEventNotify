from kafka import KafkaConsumer
from flask import Flask
from telegram import Bot
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge, start_http_server
import json, asyncio, time, os, logging, psutil, random

#
# SECRET_KEY = os.urandom(32)
#
# app = Flask(__name__)
# app.config['SECRET_KEY'] = SECRET_KEY
metrics = PrometheusMetrics()

# Crea i Gauge per l'utilizzo della memoria, CPU e il tempo di risposta
memory_usage = Gauge('memory_usage_percent', 'Utilizzo della memoria in percentuale')
cpu_usage = Gauge('cpu_usage_percent', 'Utilizzo della CPU in percentuale')
api_response_time = Gauge('api_response_time_seconds', 'Tempo di risposta dell\'API in secondi')


def measure_metrics():
    # Misura l'utilizzo della memoria
    memory_percent = psutil.virtual_memory().percent
    memory_usage.set(memory_percent)

    # Misura l'utilizzo della CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_usage.set(cpu_percent)

    # Simula un tempo di risposta casuale tra 0.1 e 1.0 secondi
    simulated_response_time = random.uniform(0.1, 1.0)
    api_response_time.set(simulated_response_time)


telegram_token = '6731451948:AAHNHAVNRG2EI89uGxPE7b0g11v3FZTpadk'


async def consuma_da_kafka():
    TOPIC_NAME = 'weatherNotification'
    time.sleep(10)
    consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers='kafka:9095')

    while True:
        for key, value in consumer.poll(1.0).items():
            for record in value:
                # record.value contiene il messaggio come bytes
                json_message = record.value.decode('utf-8')
                dictionary_message = json.loads(json_message)
                logging.error(dictionary_message)
                await send_t_message(dictionary_message)


async def send_t_message(message):
    bot = Bot(token=telegram_token)
    await bot.send_message(chat_id=message['t_chat_id'], text=message)


if __name__ == '__main__':
    start_http_server(5003)

    asyncio.run(consuma_da_kafka())
