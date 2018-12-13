from app import app, mqtt
from time import time

# bibliotecas para altenticação das mensagem
from hashlib import sha256
import hmac
from base64 import b64encode, b64decode


# Incrição nos tópicos
@mqtt.on_connect()
def mqtt_connect(client, userdata, flags, rc):
    mqtt.subscribe(app.config['MQTT_IN_TOPIC'])


# Callback
@mqtt.on_message()
def mqtt_message(client, userdata, message):
    check = check_payload(message.payload.decode())
    msg = 'MQTT CHECK' if check else 'MQTT FAILURE'
    print(msg, message.topic, message.payload.decode())


def open_door_request():
    msg = 'liberar:{}'.format(round(time()))
    payload = form_payload(msg)
    mqtt.publish(app.config['MQTT_OUT_TOPIC'], payload)


# Gera assinatura
def sign(msg, digest=sha256, encode=True):
    sign = hmac.digest(app.config['MQTT_KEY'].encode(), msg.encode(), sha256)
    if encode:
        sign = b64encode(sign)
    return sign


# Gera payload, concatenando a mensagem e a assinatura em um string em base64
def form_payload(msg, digest=sha256):
    s = sign(app.config['MQTT_KEY'], msg)
    return msg + '$' + s.decode()


# Checa se o payload é válido
def check_payload(payload, digest=sha256):
    msg, s = payload.split('$')
    s = b64decode(s)
    check = sign(app.config['MQTT_KEY'], msg, encode=False)
    return hmac.compare_digest(s, check)
