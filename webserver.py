from http.server import SimpleHTTPRequestHandler, HTTPServer
import time
import os
import json
from ohmpi import OhmPi
import threading
import pandas as pd
import shutil

#hostName = "raspberrypi.local" # works for AP-STA
#hostName = "192.168.50.1"  # fixed IP in AP-STA mode
hostName = "0.0.0.0"  # for AP mode (not AP-STA)
serverPort = 8080

# https://gist.github.com/MichaelCurrie/19394abc19abd0de4473b595c0e37a3a

with open('ohmpi_param.json') as json_file:
    pardict = json.load(json_file)

ohmpi = OhmPi(pardict, sequence='dd.txt')
#ohmpi = OhmPi(pardict, sequence='dd16s0no8.txt')


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
        global ohmpiThread, status, run
        dic = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        rdic = {}
        if dic['command'] == 'start':
            ohmpi.measure()
        elif dic['command'] == 'stop':
            ohmpi.stop()
        elif dic['command'] == 'getData':
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
        elif dic['command'] == 'removeData':
            shutil.rmtree('data')
            os.mkdir('data')
        elif dic['command'] == 'setConfig':
            ohmpi.stop()
            cdic = dic['config']
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
        elif dic['command'] == 'invert':
            pass
        elif dic['command'] == 'getResults':
            pass
        elif dic['command'] == 'rsCheck':
            ohmpi.rs_check()
            fnames = sorted([fname for fname in os.listdir('data/') if fname[-7:] == '_rs.csv'])
            df = pd.read_csv('data/' + fnames[-1])
            ddic = {
                'AB': (df['A'].astype('str') + '-' + df['B'].astype(str)).tolist(),
                'res': df['RS [kOhm]'].tolist()
            }
            rdic['data'] = ddic
        elif dic['command'] == 'download':
            shutil.make_archive('data', 'zip', 'data')
        elif dic['command'] == 'shutdown':
            print('shutting down...')
            os.system('shutdown now -h')
        elif dic['command'] == 'restart':
            print('shutting down...')
            os.system('reboot')
        else:
            # command not found
            rdic['response'] = 'command not found'
        
        rdic['status'] = ohmpi.status
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
