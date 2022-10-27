import json

import paho.mqtt.client as mqtt_client
import paho.mqtt.publish as publish
from config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG
import time
import uuid

client = mqtt_client.Client(f'ohmpi_{OHMPI_CONFIG["id"]}_controller', clean_session=False)  # create new instance
print('connecting controller to broker')
client.connect(MQTT_CONTROL_CONFIG['hostname'])
client.loop_start()
publisher_config = MQTT_CONTROL_CONFIG.copy()
publisher_config['topic'] = MQTT_CONTROL_CONFIG['ctrl_topic']
publisher_config.pop('ctrl_topic')
settings = {
            'injection_duration': 0.2,
            'nbr_meas': 1,
            'sequence_delay': 1,
            'nb_stack': 1,
            'export_path': 'data/measurement.csv'
        }

cmd_id = uuid.uuid4().hex
payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'update_settings', 'args': settings})
print(f'Update settings setup message: {payload} to {publisher_config["topic"]} with config {publisher_config}')
publish.single(payload=payload, **publisher_config)

sequence = [[1, 2, 3, 4]]
cmd_id = uuid.uuid4().hex
payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'set_sequence', 'args': sequence})
print(f'Set sequence message: {payload} to {publisher_config["topic"]} with config {publisher_config}')
publish.single(payload=payload, **publisher_config)
cmd_id = uuid.uuid4().hex
payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'rs_check'})
print(f'Run rs_check: {payload} to {publisher_config["topic"]} with config {publisher_config}')
publish.single(payload=payload, **publisher_config)

for i in range(4):
    cmd_id = uuid.uuid4().hex
    payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'start'})
    print(f'Publishing message {i}: {payload} to {publisher_config["topic"]} with config {publisher_config}')
    publish.single(payload=payload, **publisher_config)
    time.sleep(1)
client.loop_stop()
