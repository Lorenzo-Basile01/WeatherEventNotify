from threading import Thread
from kafka import KafkaConsumer
from prometheus_client import Gauge, start_http_server
from telegram import Bot
import json, asyncio, time, os, logging, shutil, psutil, schedule

telegram_token = '6731451948:AAHNHAVNRG2EI89uGxPE7b0g11v3FZTpadk'


memory_usage = Gauge('memory_usage_percent', 'Utilizzo della memoria in percentuale')
cpu_usage = Gauge('cpu_usage_percent', 'Utilizzo della CPU in percentuale')
disk_space_used = Gauge('disk_space_used', 'Disk space used by the application in bytes')

async def consuma_da_kafka():
    TOPIC_NAME = 'weatherNotification'
    time.sleep(30)
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


def measure_metrics():

    logging.error("NOTIFY_METRICS")

    memory_percent = psutil.virtual_memory().percent
    memory_usage.set(memory_percent)

    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_usage.set(cpu_percent)

    disk_space = shutil.disk_usage('/')
    disk_space_used.set(disk_space.used)


schedule.every(1).minutes.do(measure_metrics)


# Funzione per eseguire il job in un thread separato
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Avvia il thread per eseguire il job in background
scheduler_thread = Thread(target=run_scheduler)
scheduler_thread.start()


if __name__ == '__main__':

    start_http_server(5003)

    asyncio.run(consuma_da_kafka())


