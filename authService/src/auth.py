from threading import Thread
from flask import Flask, jsonify, request
from models import User, db
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Gauge
import os, logging, jwt, psutil, time, schedule, shutil

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
CORS(app)

invalid_tokens = []  # Lista per memorizzare i token invalidati

metrics = PrometheusMetrics(app)

# metriche prometheus
registered_users_metric = Counter('registered_users_total', 'Numero totale di utenti registrati')
logged_users_metric = Counter('logged_users_total', 'Numero totale di utenti loggati')
db_connections_total = Counter('db_connections_total', 'Numero totale di connessioni al DB')
memory_usage = Gauge('memory_usage_percent', 'Utilizzo della memoria in percentuale')
cpu_usage = Gauge('cpu_usage_percent', 'Utilizzo della CPU in percentuale')
disk_space_used = Gauge('disk_space_used', 'Spazio del disco usato dal servizio in bytes')


@app.route("/register", methods=['POST'])
def user_register():

    with app.app_context():
        db.create_all()
        db.session.commit()

    if request.method == 'POST':
        if request.form['username'] == '' or request.form['password'] == '' or request.form['telegramChatId'] == '':
            return jsonify({'state': 1})
        else:
            user = db.session.query(User).filter(User.username == request.form['username']).first()
            if not user:
                db_connections_total.inc()
                user = User(username=request.form['username'], password=request.form['password'],
                            telegram_chat_id=request.form['telegramChatId'])
                db.session.add(user)
                db.session.commit()

                registered_users_metric.inc()

                # Creazione del token con informazioni della sessione
                token = jwt.encode({'user_id': user.id, 't_chat_id': user.telegram_chat_id}, key=SECRET_KEY,
                                   algorithm='HS256')

                return jsonify({'state': 0, 'token': token})
            return jsonify({'state': 2})


@app.route("/login", methods=['POST'])
def user_login():

    with app.app_context():
        db.create_all()
        db.session.commit()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_connections_total.inc()
        user = db.session.query(User).filter(User.username == username, User.password == password).first()
        if user:
            if user.id in invalid_tokens:
                logging.error(invalid_tokens)
                invalid_tokens.remove(user.id)

            logged_users_metric.inc()

            logging.error(invalid_tokens)
            # Genera un nuovo token valido
            token = jwt.encode({'user_id': user.id, 't_chat_id': user.telegram_chat_id}, key=SECRET_KEY,
                               algorithm='HS256')
            return jsonify({'state': 0, 'message': 'Login effettuato con successo', 'token': token})
        else:
            return jsonify({'state': 1, 'message': 'Credenziali non valide'})


def verify_token(token):
    try:
        decoded_token = jwt.decode(token, key=SECRET_KEY, algorithms=['HS256'])
        user_id = decoded_token['user_id']
        return user_id
    except jwt.ExpiredSignatureError:
        # Il token è scaduto
        return None
    except jwt.InvalidTokenError:
        # Il token non è valido
        return None


@app.route("/logout", methods=['GET', 'POST'])
def user_logout():
    token = request.form.get('token')

    user_id = verify_token(token)

    if user_id is not None:
        invalid_tokens.append(user_id)
        logging.error(invalid_tokens)
        return jsonify({'state': 0, 'message': 'Logout effettuato con successo'})
    else:
        return jsonify({'state': 1, 'message': 'Token non valido'})


def measure_metrics():
    logging.error("AUTH_METRICS")

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

    app.run()
