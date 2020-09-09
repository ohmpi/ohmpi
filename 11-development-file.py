import json

with open('ohmpi_param.json') as json_file:
    pardict = json.load(json_file)

print(pardict.get("nb_electrodes"))