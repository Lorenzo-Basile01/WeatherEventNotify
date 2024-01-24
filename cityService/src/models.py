from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    telegram_chat_id = db.Column(db.Text, nullable=False)

    info_meteo = relationship('Info_meteo', back_populates='user')


class Info_meteo(db.Model):
    __tablename__ = 'info_meteo'

    info_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city = db.Column(db.Text, nullable=False)
    t_max = db.Column(db.Integer, nullable=True)
    t_min = db.Column(db.Integer, nullable=True)
    rain = db.Column(db.Boolean, nullable=True)
    snow = db.Column(db.Boolean, nullable=True)

    user = relationship('User', back_populates='info_meteo')