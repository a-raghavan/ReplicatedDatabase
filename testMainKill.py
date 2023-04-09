import os
import signal

# Get the list of subprocess PIDs from a file
with open('server_pids.txt', 'r') as f:
    pids = [int(line.strip()) for line in f.readlines()]

# Kill all subprocesses
for pid in pids:
    os.killpg(os.getpgid(pid), signal.SIGTERM)
