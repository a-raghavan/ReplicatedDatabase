import subprocess

import glob
import os
import shutil

import json

n = 5

sp_base = 50001
rp_base = 30001

addresses = []

files_to_delete = glob.glob('3000*')


for file in files_to_delete:
    if os.path.isfile(file):
        os.remove(file)
    else:
        shutil.rmtree(file)


# servers = [f"localhost:5000{i}" for i in range(1, n+1)]
# # print(servers)

# json_str = json.dumps(servers)

# formatted_str = json_str[1:-1]

print(formatted_str)


for i in range(n):
    rp = rp_base + i
    address = f"localhost:{rp}"
    addresses.append(address)

cmd = ['python3', 'server.py', '-n'] + addresses

# print(cmd)

ports = [(sp_base + i, rp_base + i) for i in range(n)]


sub_processes = []

for sp, rp in ports:
    proc = subprocess.Popen(cmd + ['-sp', str(sp), '-rp', str(rp)])
    sub_processes.append(proc)


with open('server_pids.txt', 'w') as f:
    for proc in sub_processes:
        f.write(str(proc.pid) + '\n')
