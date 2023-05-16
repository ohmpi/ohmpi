import subprocess
import os

uml_diagrams = []
s = None
os.chdir('..')
with open('./uml_diagrams/uml_diagrams.txt', 'r') as f:
    while not (s == ''):
        s = f.readline().strip('\n')
        if not (s == '' or s == ' '):
            uml_diagrams.append(s)
print(uml_diagrams)

if len(uml_diagrams) > 0:
    print('Updating UML diagrams...')
    for d in uml_diagrams:
        cmd = f'pyreverse {d} -p ./uml_diagrams/uml_{d}'
        print(cmd)
        out = subprocess.check_output(cmd, shell=True)
        print(out.decode('ascii'))

os.chdir('./uml_diagrams')

if len(uml_diagrams) > 0:
    print('Converting dot files...')
    for d in sorted(uml_diagrams):
        if os.path.exists(f'./classes_uml_{d}.dot'):
            cmd = f'dot -Tpng classes_uml_{d}.dot -O classes_uml_{d}.png'
            print(cmd)
            out = subprocess.check_output(cmd, shell=True)
            print(out.decode('ascii'))

    for d in sorted(uml_diagrams):
        if os.path.exists(f'./packages_uml_{d}.dot'):
            cmd = f'mvdot -Tpng packages_uml_{d}.dot -O packages_uml_{d}.png'
            print(cmd)
            out = subprocess.check_output(cmd, shell=True)
            print(out.decode('ascii'))


else:
    print('No files to update! Please add packages or modules in the '
          '"uml_diagrams.txt" file.')

