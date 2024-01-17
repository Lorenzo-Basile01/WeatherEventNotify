import json

from flask import Flask, render_template, redirect, flash
from models import User, Info_meteo, db
from forms import SubscriptionForm
from flask_login import login_user, current_user, LoginManager, logout_user
from flask import request, jsonify
from flask_cors import CORS
import os
import jwt
from datetime import datetime, timedelta
import logging

SECRET_KEY = os.environ.get('SECRET_KEY')

app = Flask(__name__)
# app.config['SECRET_KEY'] = SECRET_KEY

CORS(app)
CORS(app, origins="http://localhost:5002")

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql:3306/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# @app.route('/cityevents/<id_user>', methods=['GET', 'POST'])
# def home(id_user):
#     form = SubscriptionForm()
#     if form.is_submitted():
#         for city_form in form.cities:
#             info_meteo = Info_meteo(user_id=id_user, city=city_form.city_name.data, t_max=city_form.max_temp.data, t_min=city_form.min_temp.data, rain=city_form.rain.data, snow=city_form.snow.data)
#             db.session.add(info_meteo)
#             db.session.commit()
#             flash('city event succesfully submitted', 'success')
#     return render_template('city.html', form=form)
#
#
# @app.route('/logout', methods=['GET', 'POST'])
# def logout():
#     url_redirezione = f'http://localhost:5012/login'
#     return redirect(url_redirezione)

@app.route('/cityevents', methods=['POST'])
def home():
    if request.method == 'POST':
        if request.form['rain'] == 1:
            rain = True
        else:
            rain = False

        if request.form['snow'] == 1:
            snow = True
        else:
            snow = False
        logging.error(request)
        logging.error(request.data)
        token = request.args.get('token')
        logging.error(token)
        decoded_token = jwt.decode(token, key=SECRET_KEY, algorithms=['HS256'])



        info_meteo = Info_meteo(user_id=decoded_token['user_id'], city=request.form['city_name'],
                                t_max=request.form['max_temp'], t_min=request.form['min_temp'], rain=rain,
                                snow=snow)
        db.session.add(info_meteo)
        db.session.commit()
        return jsonify({'state': 0, 'message': 'City event inviato con successo'})


@app.route("/log_out", methods=['GET', 'POST'])
def log_out():
    logout_user()
    return jsonify({'state': 0})


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002)
