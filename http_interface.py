from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import json
import uuid
from config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG
from termcolor import colored
import pandas as pd
import shutil
import time
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
rdic = {}

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
        # set controller
        self.controller = mqtt_client.Client(f"ohmpi_{OHMPI_CONFIG['id']}_listener", clean_session=False)  # create new instance
        print(colored(f"Connecting to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']} on {MQTT_CONTROL_CONFIG['hostname']} broker", 'blue'))
        trials = 0
        trials_max = 10
        broker_connected = False
        while trials < trials_max:
            try:
                self.controller.username_pw_set(MQTT_CONTROL_CONFIG['auth'].get('username'),
                                                MQTT_CONTROL_CONFIG['auth']['password'])
                self.controller.connect(MQTT_CONTROL_CONFIG['hostname'])
                trials = trials_max
                broker_connected = True
            except Exception as e:
                print(f'Unable to connect control broker: {e}')
                print('trying again to connect to control broker...')
                time.sleep(2)
                trials += 1
        if broker_connected:
            print(f"Subscribing to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}")
            self.controller.subscribe(MQTT_CONTROL_CONFIG['ctrl_topic'], MQTT_CONTROL_CONFIG['qos'])
        else:
            print(f"Unable to connect to control broker on {MQTT_CONTROL_CONFIG['hostname']}")
            self.controller = None
        self.cmd_thread = threading.Thread(target=self._control)

    def _control(self):
        def on_message(client, userdata, message):
            global cmd_id, rdic

            command = message.payload.decode('utf-8')
            print(f'Received command {command}')
            # self.process_commands(command)
            if 'reply' in command.keys and command['cmd_id'] == cmd_id :
                rdic = command

        self.controller.on_message = on_message
        self.controller.loop_start()
        while True:
            time.sleep(.1)

    def do_POST(self):
        global cmd_id, rdic
        cmd_id = uuid.uuid4().hex
        # global socket

        # global ohmpiThread, status, run
        dic = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        rdic = {} # response dictionary
        if dic['cmd'] == 'run_sequence':
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'run_multiple_sequences'})
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'interrupt':
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'interrupt'})
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'getData':
            print(dic)
            # get all .csv file in data folder
            fnames = sorted([fname for fname in os.listdir('data/') if fname[-4:] == '.csv'])
            ddic = {}
            fdownloaded = True
            if dic['lastSurvey'] == '0':
                fdownloaded = False
            for fname in fnames:
                if (((fname != 'readme.txt')
                        and ('_rs' not in fname))
                    and ((fname.replace('.csv', '') == dic['lastSurvey'])
                         or (fdownloaded == False))):
                    fdownloaded = False
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
            # ohmpi.stop()
            if 'sequence' in dic['config'].keys() and dic['config']['sequence'] is not None:
                sequence = dic['config']['sequence']
                dic['config'].pop('sequence', None)
                payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'set_sequence', 'args': sequence})
                publish.single(payload=payload, **publisher_config)
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'update_settings', 'args': dic['config']})
            cdic = dic['config']
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'invert':
            pass
        elif dic['cmd'] == 'getResults':
            pass
        elif dic['cmd'] == 'rsCheck':
            # ohmpi.rs_check()
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'rs_check'})
            publish.single(payload=payload, **publisher_config)
            fnames = sorted([fname for fname in os.listdir('data/') if fname[-7:] == '_rs.csv'])
            df = pd.read_csv('data/' + fnames[-1])
            ddic = {
                'AB': (df['A'].astype('str') + '-' + df['B'].astype(str)).tolist(),
                'res': df['RS [kOhm]'].tolist()
            }
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
