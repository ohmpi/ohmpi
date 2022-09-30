import paho.mqtt.client as mqtt
from config import MQTT_CONTROL_CONFIG, CONTROL_CONFIG, OHMPI_CONFIG
import time
from queue import Queue
import zmq

ctrl_queue = Queue()


def on_message(client, userdata, message):
    global socket

    # Send the command
    print(f'Sending command {message.payload.decode("utf-8")}')
    socket.send_string(message.payload.decode("utf-8"))

    #  Get the reply.
    reply = socket.recv()
    print(f'Received reply {message.payload.decode("utf-8")}: {reply}')


mqtt_client = mqtt.Client(f'ohmpi_{OHMPI_CONFIG["id"]}_listener', clean_session=False)  # create new instance
print('connecting to broker')
mqtt_client.connect(MQTT_CONTROL_CONFIG['hostname'])
print('Subscribing to topic', MQTT_CONTROL_CONFIG['ctrl_topic'])
mqtt_client.subscribe(MQTT_CONTROL_CONFIG['ctrl_topic'], MQTT_CONTROL_CONFIG['qos'])
mqtt_client.on_message = on_message
mqtt_client.loop_start()
context = zmq.Context()

#  Socket to talk to server
print("Connecting to ohmpi control server")
socket = context.socket(zmq.REQ)
socket.connect(f'tcp://localhost:{CONTROL_CONFIG["tcp_port"]}')

while True:
    time.sleep(.1)
