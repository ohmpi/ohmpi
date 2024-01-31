# run this script with "python create_dummy_modules.py" until you see no more
# import error from the terminal ("ok")
import os
import sys
import importlib
dumdir = 'rpi_dummy_modules/'
if os.path.exists(dumdir) is False:
    os.mkdir(dumdir)
sys.path.append(dumdir)
sys.path.append('.')
sys.path.append(os.path.abspath('..'))

def createModule(module_name):
    print('creating', module_name)
    dpath = os.path.join(dumdir, *module_name.split('.'))
    os.mkdir(dpath)
    with open(os.path.join(dpath, '__init__.py'), 'w') as f:
        f.write('# dummy module\n')

def createAttribute(attribute, module_name):
    print('adding attribute', attribute, 'to module', module_name)
    fpath = os.path.join(dumdir, *module_name.split('.'), '__init__.py')
    with open(fpath, 'a') as f:
        f.write(attribute + ' = None\n')

error = None
typ = 'mod'

# cannot do a for loop as the "environment" is not reloaded
try:
    importlib.import_module('ohmpi.ohmpi')
    print('============= ok, no more import error detected =========')
    exit(0)
except ImportError as e:
    error = e
    typ = 'mod'
except AttributeError as e:
    error = e
    typ = 'attr'
    
if error is not None:
    a = str(error).split("'")
    if typ == 'mod':
        if len(a) == 3:  # module not found error
            createModule(a[1])
        else:
            createAttribute(a[1], a[3])
    elif typ == 'attr':
        createAttribute(a[3], a[1])
exit(1)
