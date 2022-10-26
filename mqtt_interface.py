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
    socket.send(message.payload)

    #  Get the reply
    reply = socket.recv()

    print(f'Received reply {message.payload.decode("utf-8")}: {reply}')

mqtt_client = mqtt.Client(f'ohmpi_{OHMPI_CONFIG["id"]}_listener', clean_session=False)  # create new instance
print('connecting to broker')
trials = 0
trials_max = 10
broker_connected = False
while trials < trials_max:
    try:
        mqtt_client.username_pw_set(MQTT_CONTROL_CONFIG['auth'].get('username'),MQTT_CONTROL_CONFIG['auth']['password'])
        mqtt_client.connect(MQTT_CONTROL_CONFIG['hostname'])
        trials = trials_max
        broker_connected = True
    except:
        print('trying again...')
        time.sleep(2)
        trials+=1
if broker_connected:
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
else:
    print("Unable to connect to broker")
    exit(1)

