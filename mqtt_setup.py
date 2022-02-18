from settings import MQTT_CONFIG
import paho.mqtt.client as mqtt


def on_message(client, userdata, message):
    m = str(message.payload.decode("utf-8"))
    print(f'message received {m}')
    print(f'topic: {message.topic}')
    print(f'qos: {message.qos}')
    print(f'retain flag: {message.retain}')
    client.publish(MQTT_CONFIG['measurements_topic'], f'{m} 45 ohm.m')


def mqtt_client_setup():
    client = mqtt.Client(MQTT_CONFIG['client_id'], protocol=4)  # create new client instance
    client.connect(MQTT_CONFIG['mqtt_broker'])
    client.on_message = on_message
    return client, MQTT_CONFIG['measurements_topic']
