# ohmpi integration test
# to get coverage use
# pip install coverage
# coverage run --source=ohmpi .dev/test_all.py
# coverage report --include=ohmpi/ohmpi.py,ohmpi/hardware_system.py
# coverage html
import time
import os

t0 = time.time()
from ohmpi.ohmpi import OhmPi
k = OhmPi()
print('---------- test ----------')
k.test(remote=True)
#k.test_mux(activation_time=0.1)) # already tested in k.test() > k._test_mux_ABMN()
print('---------- sequence generation ----------')
k.create_sequence(16, params=[('dpdp', 1, 8)])
k.interrupt()
k.create_sequence(16, params=[('schlum', 1, 8)])
k.create_sequence(16, params=[('multigrad', 1, 8, 2)])
k.load_sequence(os.path.join(os.path.dirname(__file__), '../sequences/ABMN.txt'))
k.create_sequence(16, params=[('wenner', 2)])
k.remove_data()
print('---------- rs_check ----------')
k._process_commands('{"cmd_id": "102392038", "cmd": "rs_check", "kwargs": {}}')
#k.rs_check()
#print('---------- async sequence ----------')
#k.run_sequence_async()
#time.sleep(3)
#k.interrupt()
#print('interrupting!!')
print('---------- vmax ----------')
vmax = k.run_measurement([1, 4, 2, 3], nb_stack=2, injection_duration=0.2, duty_cycle=0.5, strategy='vmax')
print('---------- vmin ----------')
vmin = k.run_measurement([1, 4, 2, 3], nb_stack=1, injection_duration=0.2, duty_cycle=0.3, strategy='vmin', vmn_req=0.02)
print('---------- safe ----------')
safe = k.run_measurement([1, 4, 2, 3], nb_stack=1, injection_duration=0.2, duty_cycle=0.7, strategy='safe', vab_req=40)
print('---------- fixed ----------')
fixed = k.run_measurement([1, 4, 2, 3], nb_stack=2, injection_duration=0.2, duty_cycle=1, strategy='fixed', vab_req=7.3)
print('---------- flex ----------')
flex = k.run_measurement([1, 4, 2, 3], nb_stack=2, injection_duration=0.2, duty_cycle=1, strategy='flex', pab_req=0.3)
dic = {
    'vmin': vmin,
    'vmax': vmax,
    'safe': safe,
    'fixed': fixed,
    'flex': flex
}
for key in dic:
    q = dic[key]
    print('{:8s} >>> vab: {:10.2f} V, vmn: {:10.2f} mV, r: {:10.2f} Ohm'.format(
        key, q['vab_[V]'], q['vmn_[mV]'], q['r_[Ohm]']))
#k.plot_last_fw()
print('---------- multiple sequences ----------')
k.run_multiple_sequences(sequence_delay=60, nb_meas=2)
time.sleep(20)
k.interrupt()
print('---------- inversion ----------')
k.remove_data()
k.create_sequence(8, params=[('wenner', 3)])
k.run_sequence(vab_req=5., duty_cycle=1, injection_duration=0.1, strategy='fixed', fw_in_zip=True)
datadir = os.path.join(os.path.dirname(__file__), '../data/')
fnames = sorted([f for f in os.listdir(datadir) if f[-4:] == '.csv'])
survey_names = [os.path.join(datadir, fnames[-1])]
k.get_data(survey_names=survey_names, full=True)
print(fnames[-1])
k.run_inversion(survey_names=survey_names)
print('---------- data download ----------')
k.download_data(ftype='ohmpi')
k.download_data(ftype='ohmpi', start_date='2022-01-01', end_date='2030-01-01')
k.download_data(ftype='pygimli')
k.download_data(ftype='protocol')
print('---------- find optimal vab ----------')
k.create_sequence(8, params=[('wenner', 3)])
k.find_optimal_vab_for_sequence(n_samples=3)

print('TOTAL time running: {:.1f}s'.format(time.time() - t0))
