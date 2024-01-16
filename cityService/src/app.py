from flask import Flask, render_template, redirect, flash
from models import User, Info_meteo, db
from forms import SubscriptionForm
import os

SECRET_KEY = os.urandom(32)
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql:3306/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/cityevents/<id_user>', methods=['GET', 'POST'])
def home(id_user):
    form = SubscriptionForm()
    if form.is_submitted():
        for city_form in form.cities:
            info_meteo = Info_meteo(user_id=id_user, city=city_form.city_name.data, t_max=city_form.max_temp.data, t_min=city_form.min_temp.data, rain=city_form.rain.data, snow=city_form.snow.data)
            db.session.add(info_meteo)
            db.session.commit()
            flash('city event succesfully submitted', 'success')
    return render_template('city.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    url_redirezione = f'http://localhost:5012/login'
    return redirect(url_redirezione)


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5013)
