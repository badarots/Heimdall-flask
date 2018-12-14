from app import app, mqtt
from time import time

# bibliotecas para altenticação das mensagem
from hashlib import blake2s
from hmac import compare_digest
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
def sign(msg, b64=False):
    s = blake2s(msg.encode(), key=app.config['MQTT_KEY'].encode(), digest_size=16).digest()
    if b64:
        s = b64encode(s)
    return s


# Gera payload, concatenando a mensagem e a assinatura em um string em base64
def form_payload(msg):
    return msg + '$' + sign(msg, b64=True).decode()


# Checa se o payload é válido
def check_payload(payload):
    msg, test = payload.split('$')
    test = b64decode(test)
    valid = sign(app.config['MQTT_KEY'], msg)
    return compare_digest(test, valid)
