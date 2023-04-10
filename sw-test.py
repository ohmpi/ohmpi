from sw import OhmPi
k = OhmPi(mqtt=False, onpi=True)
k.read_values()
k._compute_tx_volt()
k.load_sequence('ABMN.txt')
k.run_sequence()
k.run_multiple_sequences(nb_meas=2, sequence_delay=10)
