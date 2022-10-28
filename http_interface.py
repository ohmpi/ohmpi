from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import json
import uuid
from config import CONTROL_CONFIG
from termcolor import colored
import threading
import pandas as pd
import shutil
import zmq # to write on TCP

hostName = "0.0.0.0"  # for AP mode (not AP-STA)
serverPort = 8080

# https://gist.github.com/MichaelCurrie/19394abc19abd0de4473b595c0e37a3a

tcp_port = CONTROL_CONFIG['tcp_port']
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f'tcp://localhost:{CONTROL_CONFIG["tcp_port"]}')
print(colored(f'Sending commands and listening on tcp port {tcp_port}.'))



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

    def do_POST(self):
        cmd_id = uuid.uuid4().hex
        global socket

        # global ohmpiThread, status, run
        dic = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        rdic = {} # response dictionary
        if dic['cmd'] == 'run_sequence':
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'run_sequence'})
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'interrupt':
            # ohmpi.stop()
            payload = json.dumps({'cmd_id': cmd_id, 'cmd': 'interrupt'})
            publish.single(payload=payload, **publisher_config)
        elif dic['cmd'] == 'getData':
            # get all .csv file in data folder
            fnames = [fname for fname in os.listdir('data/') if fname[-4:] == '.csv']
            ddic = {}
            for fname in fnames:
                if (fname.replace('.csv', '') not in dic['surveyNames']
                        and fname != 'readme.txt'
                        and '_rs' not in fname):
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
            socket.send_string(json.dumps({
                'cmd_id': cmd_id,
                'cmd': 'update_settings',
                'args': dic['config']
            }))
            cdic = dic['config']
            
            """
            ohmpi.pardict['nb_electrodes'] = int(cdic['nbElectrodes'])
            ohmpi.pardict['injection_duration'] = float(cdic['injectionDuration'])
            ohmpi.pardict['nbr_meas'] = int(cdic['nbMeasurements'])
            ohmpi.pardict['nb_stack'] = int(cdic['nbStack'])
            ohmpi.pardict['sequence_delay'] = int(cdic['sequenceDelay'])
            if cdic['sequence'] != '':
                with open('sequence.txt', 'w') as f:
                    f.write(cdic['sequence'])
                ohmpi.read_quad('sequence.txt')
                print('new sequence set.')
            print('setConfig', ohmpi.pardict)
            """
        elif dic['cmd'] == 'invert':
            pass
        elif dic['cmd'] == 'getResults':
            pass
        elif dic['cmd'] == 'rsCheck':
            # ohmpi.rs_check()
            socket.send_string(json.dumps({
                'cmd_id': cmd_id,
                'cmd': 'rs_check'
            }))
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
            os.system('reboot')
        else:
            # command not found
            rdic['response'] = 'command not found'

        # rdic['status'] = ohmpi.status
        rdic['status'] = 'unknown'  # socket_out.
        # wait for reply

        message = socket.recv()
        print('+++////', message)
        rdic['data'] = message.decode('utf-8')
        """
        while False:
            message = socket.recv()
            print(f'Received command: {message}')
            e = None
            try:
                decoded_message = json.loads(message.decode('utf-8'))
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
