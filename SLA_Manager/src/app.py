import time
from datetime import datetime, timedelta
import logging
from threading import Thread
from flask_cors import CORS
import schedule
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
import prometheus_client
import requests
import os

app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql_SLA/slaDb'
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
    #violations = relationship('Violation', back_populates='sla')

#backref='sla', lazy=True
# Definizione del modello delle violazioni
class Violation(db.Model):
    __tablename__ = 'violations'
    id = db.Column(db.Integer, primary_key=True)
    sla_id = db.Column(db.Integer, db.ForeignKey('sla.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sla = relationship('SLA_table')#, back_populates='violations')

# Inizializzazione delle metriche di Prometheus
# sla_violations_counter = prometheus_client.Counter('sla_violations_total', 'Total number of SLA violations')


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


@app.route('/add_metric', methods=['POST'])
def add_metric():
    if request.method == 'POST':
        if db.session.query(SLA_table).filter(SLA_table.metric_name == request.form['metric_name']).first():
            return jsonify({'message': 1})
        else:
            sla = SLA_table(metric_name=request.form['metric_name'], desired_value=request.form['desired_value'])
            db.session.add(sla)
            db.session.commit()
            return jsonify({'message': 0})


@app.route('/remove_metric', methods=['POST'])
def remove_metric():
    sla = db.session.query(SLA_table).filter(SLA_table.metric_name == request.form['metric_name']).first()
    if sla:
        db.session.delete(sla)
        db.session.commit()
        return jsonify({'message': 0})
    else:
        return jsonify({'message': 1})


# API per la query dello stato del SLA
@app.route('/sla_current_state', methods=['POST'])
def get_sla_status():
    sla = SLA_table.query.filter_by(metric_name=request.form['metric_name']).first()
    if sla:
        data = prometheus_request(sla.metric_name)

        list_current_value = data['data']['result'][0]['value']
        current_value = float(list_current_value[1])

        logging.error(current_value)
        logging.error(sla.desired_value)

        violation = current_value > sla.desired_value
        return jsonify({
            'state': 0,
            'current_value': current_value,
            'desired_value': sla.desired_value,
            'violation': violation,
        })
    else:
        return jsonify({'state': 1})


@app.route('/sla_past_violations/', methods=['POST'])
def get_sla_past_violations():
    sla = SLA_table.query.filter_by(metric_name=request.form['metric_name']).first()
    if sla:

        # Calcolo del numero di violazioni nelle ultime 1, 3, 6 ore
        violations_count_last_hour = sla.violations.filter(
            Violation.timestamp >= datetime.utcnow() - timedelta(hours=1)).count()

        violations_count_last_3_hours = sla.violations.filter(
            Violation.timestamp >= datetime.utcnow() - timedelta(hours=3)).count()

        violations_count_last_6_hours = sla.violations.filter(
            Violation.timestamp >= datetime.utcnow() - timedelta(hours=6)).count()

        return jsonify({
            'state': 0,
            'desired_value': sla.desired_value,
            'violations_count_last_hour': violations_count_last_hour,
            'violations_count_last_3_hours': violations_count_last_3_hours,
            'violations_count_last_6_hours': violations_count_last_6_hours,
            # 'probability_of_violation':  # Calcolo della probabilità di violazione nei prossimi X minuti
        })
    else:
        return jsonify({'state': 1})


def prometheus_request(metric_name):
    url = "http://prometheus:9090/api/v1/query"
    params = {
        'query': metric_name,
        # 'time': 'timestamp', questo se mi interessano info su tempi non attuali
    }

    response = requests.post(url, params=params)
    logging.error(response.json())
    if response.status_code == 200:
        data = response.json()
        logging.error(data)
        return data


def monitor_system_metrics():
    logging.error("MONITORING")
    # Esempio di monitoraggio di una metrica (si prega di adattare alla tua logica effettiva)
    with app.app_context():
        sla_elements = db.session.query(SLA_table).all()
        for sla in sla_elements:
            metric_name = sla.metric_name
            data = prometheus_request(metric_name)

            list_current_value = data['data']['result'][0]['value']
            current_value = float(list_current_value[1])
            sla = SLA_table.query.filter_by(metric_name=metric_name).first()

            if sla:
                # Verifica se c'è una violazione
                if current_value > sla.desired_value:
                    # Registra la violazione nella tabella 'Violation'
                    violation = Violation(sla_id=sla.id, value=current_value, timestamp=datetime.utcnow())
                    db.session.add(violation)
                    db.session.commit()


# Configura l'intervallo di esecuzione della funzione (ogni mezz'ora)
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
    # Esegui questa funzione periodicamente o in risposta a eventi del sistema
    # per monitorare le metriche e rilevare eventuali violazioni
