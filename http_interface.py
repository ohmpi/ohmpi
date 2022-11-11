from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import json
import uuid
from config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG
from termcolor import colored
import pandas as pd
import shutil
import time
import numpy as np
from io import StringIO
import threading
import paho.mqtt.client as mqtt_client
import paho.mqtt.publish as publish

hostName = "0.0.0.0"  # for AP mode (not AP-STA)
serverPort = 8080

# https://gist.github.com/MichaelCurrie/19394abc19abd0de4473b595c0e37a3a

ctrl_broker = MQTT_CONTROL_CONFIG['hostname']
publisher_config = MQTT_CONTROL_CONFIG.copy()
publisher_config['topic'] = MQTT_CONTROL_CONFIG['ctrl_topic']
publisher_config.pop('ctrl_topic')

print(colored(f"Sending commands control topic {MQTT_CONTROL_CONFIG['ctrl_topic']} on {MQTT_CONTROL_CONFIG['hostname']} broker."))
cmd_id = None
received = False
rdic = {}


# set controller globally as __init__ seem to be called for each request and so we subscribe again each time (=overhead)
controller = mqtt_client.Client(f"ohmpi_{OHMPI_CONFIG['id']}_interface_http", clean_session=False)  # create new instance
print(colored(f"Connecting to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']} on {MQTT_CONTROL_CONFIG['hostname']} broker", 'blue'))
trials = 0
trials_max = 10
broker_connected = False
while trials < trials_max:
    try:
        controller.username_pw_set(MQTT_CONTROL_CONFIG['auth'].get('username'),
                                        MQTT_CONTROL_CONFIG['auth']['password'])
        controller.connect(MQTT_CONTROL_CONFIG['hostname'])
        trials = trials_max
        broker_connected = True
    except Exception as e:
        print(f'Unable to connect control broker: {e}')
        print('trying again to connect to control broker...')
        time.sleep(2)
        trials += 1
if broker_connected:
    print(f"Subscribing to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}")
    controller.subscribe(MQTT_CONTROL_CONFIG['ctrl_topic'], MQTT_CONTROL_CONFIG['qos'])
else:
    print(f"Unable to connect to control broker on {MQTT_CONTROL_CONFIG['hostname']}")
    controller = None


# start a listener for acknowledgement
def _control():
    def on_message(client, userdata, message):
        global cmd_id, rdic, received

        command = json.loads(message.payload.decode('utf-8'))
        #print('++++', cmd_id, received, command)
        if ('reply' in command.keys()) and (command['cmd_id'] == cmd_id):
            print(f'Acknowledgement reception of command {command} by OhmPi')
           # print('oooooooooook', command['reply'])
            received = True
            #rdic = command

    controller.on_message = on_message
    controller.loop_forever()
    
t = threading.Thread(target=_control)
t.start()


class MyServer(SimpleHTTPRequestHandler):
    # because we use SimpleHTTPRequestHandler, we do not need to implement
    # the do_GET() method (if we use the BaseHTTPRequestHandler, we would need to)

    # def do_GET(self):
    #     # normal get for wepages (not so secure!)
    #     print(self.command)
    #     print(self.headers)
    #     print(self.request)
    #     self.send_response(200)
    #     self.send_header("Content-type", "text/html")
    #     self.end_headers()
    #     with open(os.path.join('.', self.path[1:]), 'r') as f:
    #         self.wfile.write(bytes(f.read(), "utf-8"))

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        # global controller, once  # using global variable otherwise, we subscribe to client for EACH request
        # if once:
        #     self.controller = controller
        #     self.cmd_thread = threading.Thread(target=self._control)
        #     self.cmd_thread.start()
        #     once = False


    # we would like to listen to the ackn topic to check our message has been wel received
    # by the OhmPi, however, this won't work as it seems an instance of MyServer is created
    # each time (actually it's not a server but a requestHandler)
    # def _control(self):
    #     def on_message(client, userdata, message):
    #         global cmd_id, rdic

    #         command = json.loads(message.payload.decode('utf-8'))
    #         print(f'Acknowledgement reception of command {command} by OhmPi')
    #         if 'reply' in command.keys() and command['cmd_id'] == cmd_id :
    #             print('oooooooooook', command['reply'])
    #             #rdic = command

    #     self.controller.on_message = on_message
    #     print('starting loop')
    #     self.controller.loop_forever()
    #     print('forever')

    def do_POST(self):
        global cmd_id, rdic, received
        received = False
        cmd_id = uuid.uuid4().hex
        dic = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        rdic = {} # response dictionary
        if dic['cmd'] == 'run_multiple_sequences':
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'run_multiple_sequences'})
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'interrupt':
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'interrupt'})
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'getData':
            # get all .csv file in data folder
            fnames = [fname for fname in os.listdir('data/') if fname[-4:] == '.csv']
            ddic = {}
            for fname in fnames:
                if ((fname != 'readme.txt')
                    and ('_rs' not in fname)
                    and (fname.replace('.csv', '') not in dic['surveyNames'])):
                    df = pd.read_csv('data/' + fname)
                    ddic[fname.replace('.csv', '')] = {
                        'a': df['A'].tolist(),
                        'b': df['B'].tolist(),
                        'm': df['M'].tolist(),
                        'n': df['N'].tolist(),
                        'rho': df['R [ohm]'].tolist(),
                    }
            rdic['data'] = ddic
        elif dic['cmd'] == 'removeData':
            shutil.rmtree('data')
            os.mkdir('data')
        elif dic['cmd'] == 'update_settings':
            if 'sequence' in dic['settings'].keys() and dic['settings']['sequence'] is not None:
                sequence = dic['settings'].pop('sequence', None)
                sequence = np.loadtxt(StringIO(sequence)).astype(int).tolist()  # list of list
                # we pass the sequence as a list of list as this object is easier to parse for the json.loads()
                # of ohmpi._process_commands()
                payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'set_sequence', 'kwargs': {'sequence': sequence}})
                print('payload ===', payload)
                publish.single(payload=payload, **publisher_config)
            payload = json.dumps({'cmd_id': cmd_id + '_settings', 'cmd': 'update_settings', 'kwargs': {'settings': dic['settings']}})
            cdic = dic['settings']
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'invert':
            pass
        elif dic['cmd'] == 'getResults':
            pass
        elif dic['cmd'] == 'rsCheck':
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'rs_check'})
            publish.single(payload=payload, **publisher_config)

        elif dic['cmd'] == 'getRsCheck':
            fnames = sorted([fname for fname in os.listdir('data/') if fname[-7:] == '_rs.csv'])
            if len(fnames) > 0:
                df = pd.read_csv('data/' + fnames[-1])
                ddic = {
                    'AB': (df['A'].astype('str') + '-' + df['B'].astype(str)).tolist(),
                    'res': df['RS [kOhm]'].tolist()
                }
            else:
                ddic = {}
            rdic['data'] = ddic
        elif dic['cmd'] == 'download':
            shutil.make_archive('data', 'zip', 'data')
        elif dic['cmd'] == 'shutdown':
            print('shutting down...')
            os.system('shutdown now -h')
        elif dic['cmd'] == 'restart':
            print('shutting down...')
            os.system('reboot')  # NOTE: on machine running the interface?  or on rpi?
        else:
            # command not found
            rdic['response'] = 'command not found'

        # rdic['status'] = ohmpi.status
        rdic['status'] = 'unknown'  # socket_out.
        # wait for reply

        #message = socket.recv()
        #print('+++////', message)
        # rdic['data'] = message.decode('utf-8')
        """
        while False:
            message = socket.recv()
            print(f'Received command: {message}')
            e = None
            try:
                decoded_message = json.loads(message))
                cmd = decoded_message.pop('cmd', None)
                args = decoded_message.pop('args', None)
                status = False
                e = None
                if cmd is not None and cmd_id is decoded_message.pop('cmd_id', None):
                    print('reply=', decoded_message)
            except Exception as e:
                print(f'Unable to decode command {message}: {e}')
            """
        self.send_response(200)
        self.send_header('Content-Type', 'text/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(rdic), 'utf8'))


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
