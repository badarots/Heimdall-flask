import os

class BaseConfig(object):
    """Base configuration."""

    # main config
    SECRET_KEY = 'my_precious'
    SECURITY_PASSWORD_SALT = 'my_precious_two'
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    WTF_CSRF_ENABLED = True
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # mqtt settings
    MQTT_BROKER_URL = 'broker.mqttdashboard.com'
    MQTT_BROKER_PORT = 1883
    # MQTT_USERNAME = 'server'
    # MQTT_PASSWORD = '1234'
    MQTT_REFRESH_TIME = 1.0  # refresh time in seconds
    MQTT_TOPIC_IN = "testtopic/server"
    MQTT_TOPIC_OUT = "testtopic/fechadura"

    # mail settings
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    # gmail authentication
    MAIL_USERNAME = os.environ['APP_MAIL_USERNAME']
    MAIL_PASSWORD = os.environ['APP_MAIL_PASSWORD']

    # mail accounts
    MAIL_DEFAULT_SENDER = 'from@example.com'

class DebugConfig(BaseConfig):
    DEBUG = True
    