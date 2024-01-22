from flask import Flask, jsonify, request
from models import User, db
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter
import os
import logging
import jwt

SECRET_KEY = os.environ.get('SECRET_KEY')

app = Flask(__name__)

metrics = PrometheusMetrics(app)
# La linea di codice metrics = PrometheusMetrics(app) è parte dell'utilizzo della libreria prometheus-flask-exporter
# in un'app Flask. Questo codice inizializza un oggetto PrometheusMetrics associato all'istanza dell'applicazione
# Flask (app). L'oggetto metrics fornisce una serie di funzionalità per la raccolta e l'esposizione di metriche per la tua applicazione.

# metriche prometheus
registered_users_metric = Counter(
    'registered_users_total', 'Numero totale di utenti registrati'
)
# metriche prometheus
logged_users_metric = Counter(
    'logged_users_total', 'Numero totale di utenti loggati'
)

# Metriche per il conteggio delle connessioni al database
db_connections_total = Counter('db_connections_total', 'Total number of database connections')

CORS(app)

app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql_auth/authDb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

invalid_tokens = []  # Lista per memorizzare i token invalidati


@app.route("/register", methods=['POST'])
def user_register():
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

                # incremento metrica register counter
                registered_users_metric.inc()

                # Creazione del token con informazioni della sessione
                token = jwt.encode({'user_id': user.id, 't_chat_id': user.telegram_chat_id}, key=SECRET_KEY,
                                   algorithm='HS256')

                return jsonify({'state': 0, 'token': token})
            return jsonify({'state': 2})


@app.route("/login", methods=['POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']  # Utilizza l'operatore di accesso diretto []
        password = request.form['password']

        db_connections_total.inc()
        user = db.session.query(User).filter(User.username == username, User.password == password).first()
        if user:
            if user.id in invalid_tokens:
                logging.error(invalid_tokens)
                invalid_tokens.remove(user.id)

            # incremento metrica login counter
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

    # Verifica e decodifica il token
    user_id = verify_token(token)

    if user_id is not None:
        # Aggiungi il token alla lista di token invalidati
        invalid_tokens.append(user_id)
        logging.error(invalid_tokens)
        return jsonify({'state': 0, 'message': 'Logout effettuato con successo'})
    else:
        return jsonify({'state': 1, 'message': 'Token non valido'})


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == '__main__':
    app.run()
