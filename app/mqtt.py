from app import app, mqtt
from time import time


# Incrição nos tópicos
@mqtt.on_connect()
def mqtt_connect(client, userdata, flags, rc):
    mqtt.subscribe(app.config['MQTT_IN_TOPIC'])


# Callback
@mqtt.on_message()
def mqtt_message(client, userdata, message):
    print("MQTT", message.topic, message.payload.decode())


def open_door_request():
    mqtt.publish(app.config['MQTT_OUT_TOPIC'], 'liberar,' + str(round(time())))
