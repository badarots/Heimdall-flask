from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_mqtt import Mqtt
from config import BaseConfig


app = Flask(__name__)
app.config.from_object(BaseConfig)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'

mail = Mail(app)

mqtt = Mqtt(app)

from app import routes, models, erros
