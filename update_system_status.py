#!/usr/bin/env python3
import json
import time
import subprocess
import re
from pathlib import Path

BASE = Path('.')
out = BASE / 'system-status.json'

def get_cpu_usage():
    try:
        # Read /proc/stat
        with open('/proc/stat', 'r') as f:
            lines = f.readlines()
        cpu_line = [l for l in lines if l.startswith('cpu ')][0]
        parts = cpu_line.split()
        # user+nice+system+irq+softirq+steal
        active = sum(int(x) for x in parts[1:4] + parts[6:9])
        idle = int(parts[4]) + int(parts[5]) # idle + iowait
        return active, idle
    except:
        return 0, 0

def get_cpu_percent(sample_duration=0.5):
    a1, i1 = get_cpu_usage()
    time.sleep(sample_duration)
    a2, i2 = get_cpu_usage()
    total_delta = (a2 + i2) - (a1 + i1)
    active_delta = a2 - a1
    if total_delta > 0:
        return int((active_delta / total_delta) * 100)
    return 0

def get_disk_usage(path):
    try:
        res = subprocess.check_output(['df', '-h', path], text=True).splitlines()[1].split()
        # Filesystem Size Used Avail Use% Mounted on
        return {
            'size': res[1],
            'used': res[2],
            'avail': res[3],
            'usePercent': res[4].replace('%', '')
        }
    except:
        return {}

def get_folder_size(path):
    try:
        # du -sh
        res = subprocess.check_output(['du', '-sh', path], stderr=subprocess.DEVNULL, text=True).split()[0]
        return res
    except:
        return '0B'

# Paths to monitor
HOTSPOTS = {
    'tmp': '/tmp',
    'varLog': '/var/log',
    'nvm': '/home/gagekappes/.config/nvm',
    'npm': '/home/gagekappes/.npm'
}

data = {
    'ok': True,
    'cpu': get_cpu_percent(),
    'linuxDisk': get_disk_usage('/'),
    'shareDisk': get_disk_usage('/mnt/chromeos/MyFiles/Downloads/SHARE'),
    'hotspots': {k: get_folder_size(v) for k,v in HOTSPOTS.items()},
    'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z')
}

out.write_text(json.dumps(data, indent=2) + '\n')
print(f"System status updated. CPU: {data['cpu']}%")
