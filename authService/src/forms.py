from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo


#WTForms è una libreria Python che semplifica molto lo sviluppo e la manutenzione di form
#per le applicazioni WEB. In sintesi: ci permette di progettare una form utilizzando una classe i
#cui attributi rappresentano i campi che l'utente ha a disposizione. Sono disponibili campi di diverse
# tipologie, che coprono la maggior parte delle esigenze di progettazione di form.
class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    tel_chat_id = StringField('Telegram chat id',
                              validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')