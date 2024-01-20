
from kafka import KafkaConsumer
from flask import Flask
from telegram import Bot
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter
import json, asyncio, time, os, logging

#
# SECRET_KEY = os.urandom(32)
#
# app = Flask(__name__)
# app.config['SECRET_KEY'] = SECRET_KEY

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
    asyncio.run(consuma_da_kafka())
