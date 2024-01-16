from flask import Flask, render_template, flash, redirect, url_for
from forms import RegistrationForm, LoginForm
from models import User, db
from flask_login import login_user, current_user, LoginManager, logout_user
import os
SECRET_KEY = os.urandom(32)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@mysql:3306/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(int(user_id))
    return None

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        id_user = current_user.id
        url_redirezione = f'http://localhost:5013/cityevents/{id_user}'
        return redirect(url_redirezione)
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.data.get('username'), telegram_chat_id=form.data.get('tel_chat_id'), password=form.data.get('password'))
        db.session.add(user)  #Questa riga aggiunge il nuovo oggetto utente creato alla sessione SQLAlchemy.
        login_user(user)        #consente all'applicazione di tenere traccia dell'utente autenticato.
        db.session.commit()  #Questa riga conferma le modifiche apportate alla sessione del database, aggiungendo effettivamente il nuovo utente al database.
        flash(f'Account created for {form.username.data}!', 'success')
        id_user = current_user.id
        url_redirezione = f'http://localhost:5013/cityevents/{id_user}'
        return redirect(url_redirezione)
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
     if current_user.is_authenticated:
         id_user = current_user.id
         url_redirezione = f'http://localhost:5013/cityevents/{id_user}'
         return redirect(url_redirezione)
     form = LoginForm()
     if form.validate_on_submit():
        if db.session.query(User).filter(User.username == form.data.get('username'), User.password == form.data.get('password')).first():
             user = db.session.query(User).filter(User.username == form.data.get('username'), User.password == form.data.get('password')).first()
             login_user(user)
             flash('You have been logged in!', 'success')
             id_user = current_user.id
             url_redirezione = f'http://localhost:5013/cityevents/{id_user}'
             return redirect(url_redirezione)

        else:
             flash('Login Unsuccessful. Please check username and password', 'danger')
     return render_template('login.html', title='Login', form=form)

@app.route("/log_out", methods=['GET', 'POST'])
def log_out():
    logout_user()
    return redirect(url_for('login'))


@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5012)

