import os
basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig(object):
    # Básico
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = True

    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # E-mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or "localhost"
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['badarots@gmail.com']

    # MQTT
    MQTT_BROKER_URL =  os.environ.get('MQTT_BROKER_URL') or 'broker.hivemq.com'  # use the free broker from HIVEMQ
    MQTT_BROKER_PORT = 1883  # default port for non-tls connection
    MQTT_USERNAME = ''  # set the username here if you need on for the broker
    MQTT_PASSWORD = ''  # set the password here if the broker demands on
    MQTT_KEEPALIVE = 5  # set the time interval for sending a ping to the seconds
    MQTT_TLS_ENABLED = False  # set TLS to disabled for testing purposes
    MQTT_IN_TOPIC = "testeio/server"
    MQTT_OUT_TOPIC = "testeio/porta"
    MQTT_KEY = "you-will-never-guess-again"
