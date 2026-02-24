#!/usr/bin/env python3
import json, subprocess, time
from pathlib import Path

BASE = Path('/mnt/chromeos/MyFiles/Downloads/SHARE/core/mission-control')
out = BASE / 'system-status.json'


def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def parse_df(path):
    line = sh(f"df -h {path} | tail -n 1")
    parts = line.split()
    return {
        'filesystem': parts[0],
        'size': parts[1],
        'used': parts[2],
        'avail': parts[3],
        'usePercent': int(parts[4].rstrip('%')),
        'mount': parts[5],
    }


def size(path):
    try:
        return sh(f"du -sh {path} 2>/dev/null | awk '{{print $1}}'")
    except Exception:
        return 'n/a'

try:
    data = {
        'ok': True,
        'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'linuxDisk': parse_df('/'),
        'shareDisk': parse_df('/mnt/chromeos/MyFiles/Downloads/SHARE'),
        'hotspots': {
            'tmp': size('/tmp'),
            'varLog': size('/var/log'),
            'nvm': size('/home/gagekappes/.config/nvm'),
            'npm': size('/home/gagekappes/.npm'),
            'cache': size('/home/gagekappes/.cache'),
            'tmpGhAudit': size('/tmp/gh-audit'),
        }
    }
except Exception as e:
    data = {'ok': False, 'error': str(e), 'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z')}

out.write_text(json.dumps(data, indent=2) + '\n')
print(out)
