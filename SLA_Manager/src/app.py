import time, requests, os
from datetime import datetime, timedelta
import logging
from threading import Thread
from flask_cors import CORS
import schedule
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

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
db = SQLAlchemy()
db.init_app(app)
CORS(app)


# Definizione del modello del SLA
class SLA_table(db.Model):
    __tablename__ = 'sla'

    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(50), nullable=False)
    desired_value = db.Column(db.Float, nullable=False)
    job_name = db.Column(db.String(50), nullable=False)


# Definizione del modello delle violazioni
class Violation(db.Model):
    __tablename__ = 'violations'
    id = db.Column(db.Integer, primary_key=True)
    sla_id = db.Column(db.Integer, db.ForeignKey('sla.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sla = relationship('SLA_table')


# metodo che permette di aggiungere una metrica nel db
@app.route('/add_metric', methods=['POST'])
def add_metric():
    with app.app_context():
        db.create_all()
        db.session.commit()

    if request.method == 'POST':
        if db.session.query(SLA_table).filter((SLA_table.metric_name == request.form['metric_name'])
                                              & (SLA_table.job_name == request.form['job_name'])).first():
            return jsonify({'message': 1})
        else:
            sla = SLA_table(metric_name=request.form['metric_name'],
                            job_name=request.form['job_name'],
                            desired_value=request.form['desired_value'])
            db.session.add(sla)
            db.session.commit()
            return jsonify({'message': 0})


# metodo che permette di rimuovere una metrica dal db
@app.route('/remove_metric', methods=['POST'])
def remove_metric():
    with app.app_context():
        db.create_all()
        db.session.commit()
    sla = db.session.query(SLA_table).filter((SLA_table.metric_name == request.form['metric_name'])
                                             & (SLA_table.job_name == request.form['job_name'])).first()

    violations = Violation.query.filter_by(sla_id=sla.id).all()

    if sla:
        for violation in violations:
            db.session.delete(violation)
        db.session.delete(sla)
        db.session.commit()
        return jsonify({'message': 0})
    else:
        return jsonify({'message': 1})


# API per la query dello stato del SLA
@app.route('/sla_current_state', methods=['POST'])
def get_sla_status():
    with app.app_context():
        db.create_all()
        db.session.commit()
    sla = SLA_table.query.filter((SLA_table.metric_name == request.form['metric_name'])
                                 & (SLA_table.job_name == request.form['job_name'])).first()

    if not sla:
        return jsonify({'state': 1})

    data = prometheus_request(sla.metric_name)
    results = data['data']['result']

    for result in results:
        if result['metric']['job'] == sla.job_name:
            current_value = float(result['value'][1])
            violation = current_value > sla.desired_value
            return jsonify({
                'state': 0,
                'current_value': current_value,
                'desired_value': sla.desired_value,
                'violation': violation,
            })

    return jsonify({'state': 2})


# metodo utilizzato per il calcolo delle violazioni nelle ultime 1, 3, 6 ore
@app.route('/sla_past_violations', methods=['POST'])
def get_sla_past_violations():
    with app.app_context():
        db.create_all()
        db.session.commit()
    sla = SLA_table.query.filter((SLA_table.metric_name == request.form['metric_name'])
                                 & (SLA_table.job_name == request.form['job_name'])).first()

    if not sla:
        return jsonify({'state': 1})

    logging.error(datetime.utcnow())

    logging.error(timedelta(minutes=1))

    # Calcolo del numero di violazioni nelle ultime 1, 3 e 6 ore
    violations_count_last_hour = Violation.query.filter(
        (Violation.sla_id == sla.id) &
        (Violation.timestamp >= datetime.utcnow() - timedelta(minutes=60))
    ).count()

    violations_count_last_3_hours = Violation.query.filter(
        (Violation.sla_id == sla.id) &
        (Violation.timestamp >= datetime.utcnow() - timedelta(minutes=180))
    ).count()

    violations_count_last_6_hours = Violation.query.filter(
        (Violation.sla_id == sla.id) &
        (Violation.timestamp >= datetime.utcnow() - timedelta(minutes=360))
    ).count()

    return jsonify({
        'state': 0,
        'desired_value': sla.desired_value,
        'violations_count_last_hour': violations_count_last_hour,
        'violations_count_last_3_hours': violations_count_last_3_hours,
        'violations_count_last_6_hours': violations_count_last_6_hours,

    })


def prometheus_request(metric_name):
    url = "http://prometheus:9090/api/v1/query"
    params = {
        'query': metric_name,
    }

    response = requests.post(url, params=params)
    logging.error(response.json())
    if response.status_code == 200:
        data = response.json()
        logging.error(data)
        return data


# metodo eseguito periodicamente per monitorare le possibili violazioni nel tempo
def monitor_system_metrics():
    with app.app_context():
        db.create_all()
        db.session.commit()
    logging.error("MONITORING")

    with app.app_context():
        sla_elements = db.session.query(SLA_table).all()
        for sla in sla_elements:
            data = prometheus_request(sla.metric_name)
            results = data['data']['result']

            for result in results:
                if result['metric']['job'] == sla.job_name:
                    current_value = float(result['value'][1])
                    if current_value > sla.desired_value:
                        # Registra la violazione nella tabella 'Violation'
                        violation = Violation(sla_id=sla.id, value=current_value, timestamp=datetime.utcnow())
                        db.session.add(violation)
                        db.session.commit()


@app.route('/sla_probability_violations', methods=['POST'])
def get_sla_probability_violations():
    metric_name = request.form['metric_name']
    job_name = request.form['job_name']
    minutes = request.form['minutes']
    desired_value = float(request.form['desired_value'])

    response = requests.get('http://prometheus:9090/api/v1/query_range',
                            params={'query': metric_name, 'start': time.time() - 21600, 'end': time.time(),
                                    'step': "2m"})

    results = response.json()['data']['result']

    current_values = None

    for result in results:
        if result['metric']['job'] == job_name:
            current_values = result['values']

    logging.error(current_values)

    # Crea un DataFrame
    df = pd.DataFrame(current_values, columns=['time', 'value'])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.set_index('time')

    logging.error(df)

    model = ARIMA(df, order=(1, 1, 1))
    results = model.fit()
    steps = int(minutes) / 2

    # Predizione della probabilità futura
    forecast = results.get_forecast(steps=int(steps))
    conf_int = forecast.conf_int()

    umax = conf_int['upper value'].max()
    lmax = conf_int['lower value'].max()
    umin = conf_int['upper value'].min()
    lmin = conf_int['lower value'].min()
    distanzasup = umax - lmax
    distanzainf = umin - lmin
    psup = 0

    if umax > desired_value:
        psup += (umax - desired_value) / distanzasup
    if lmax < desired_value:
        psup += (desired_value - lmax) / distanzasup

    pinf = 0
    if umin > desired_value:
        psup += (umin - desired_value) / distanzainf
    if lmin < desired_value:
        psup += (desired_value - lmin) / distanzainf

    probability_value = min(max(psup, pinf), 1)

    return jsonify({
        'state': 0,
        'prevision': probability_value,
    })


# Configura dell'intervallo di esecuzione della funzione (ogni mezz'ora)
schedule.every(1).minutes.do(monitor_system_metrics)


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
