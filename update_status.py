#!/usr/bin/env python3
import json, re, subprocess, time
from pathlib import Path

BASE = Path('.')
out = BASE / 'status.json'
history_file = BASE / 'usage-history.jsonl'


def parse_tokens(s: str):
    m = re.search(r'agent:main:main[\s\S]*?(\d+(?:\.\d+)?)k\/(\d+(?:\.\d+)?)k \((\d+)%\)', s)
    if not m:
        return None
    used_k = float(m.group(1))
    max_k = float(m.group(2))
    pct = int(m.group(3))
    return int(used_k * 1000), int(max_k * 1000), pct


def parse_model(s: str):
    # Strip ANSI codes first if possible, or make regex robust
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean = ansi_escape.sub('', s)
    m = re.search(r'Model:\s+([^\s]+)', clean)
    return m.group(1) if m else None

def parse_provider(model: str):
    if not model: return 'Unknown'
    if 'google' in model.lower(): return 'Google'
    if 'gemini' in model.lower(): return 'Google'
    if 'gpt' in model.lower() or 'openai' in model.lower(): return 'OpenAI'
    if 'claude' in model.lower() or 'anthropic' in model.lower(): return 'Anthropic'
    return 'Custom'

def parse_usage_left(s: str):
    m = re.search(r'Usage:[\s\S]*?(\d+)%\s+left[\s\S]*?Day\s+(\d+)%\s+left', s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


prev = {}
if out.exists():
    try:
        prev = json.loads(out.read_text())
    except Exception:
        prev = {}

try:
    text = subprocess.check_output(['openclaw', 'status'], text=True, stderr=subprocess.STDOUT, timeout=40)
    parsed = parse_tokens(text)
    if not parsed:
        raise RuntimeError('Could not parse session token usage from openclaw status output')
    used, max_tokens, pct = parsed
    usage = parse_usage_left(text)
    session_left_pct, day_left_pct = usage if usage else (None, None)

    model = parse_model(text)
    provider = parse_provider(model)

    if session_left_pct is None:
        session_left_pct = prev.get('sessionLeftPercent')
    if day_left_pct is None:
        day_left_pct = prev.get('dayLeftPercent')
    if model is None:
        model = prev.get('model')
    if provider == 'Unknown':
        provider = prev.get('provider')

    data = {
        'ok': True,
        'used': used,
        'max': max_tokens,
        'percent': pct,
        'sessionLeftPercent': session_left_pct,
        'dayLeftPercent': day_left_pct,
        'model': model,
        'provider': provider,
        'auth': 'Verified',
        'source': 'openclaw status',
        'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z')
    }
except Exception as e:
    # Keep last known-good values on transient failures so dashboard stays usable.
    data = {
        'ok': bool(prev.get('used') is not None and prev.get('max') is not None and prev.get('percent') is not None),
        'used': prev.get('used'),
        'max': prev.get('max'),
        'percent': prev.get('percent'),
        'sessionLeftPercent': prev.get('sessionLeftPercent'),
        'dayLeftPercent': prev.get('dayLeftPercent'),
        'model': prev.get('model'),
        'provider': prev.get('provider'),
        'auth': 'Unknown',
        'source': 'openclaw status (stale fallback)',
        'error': str(e),
        'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z')
    }

out.write_text(json.dumps(data, indent=2) + '\n')

# Append history only when numeric data exists.
if all(data.get(k) is not None for k in ('used', 'max', 'percent')):
    entry = {
        'ts': int(time.time()),
        'used': data.get('used'),
        'max': data.get('max'),
        'percent': data.get('percent'),
        'sessionLeftPercent': data.get('sessionLeftPercent'),
        'dayLeftPercent': data.get('dayLeftPercent'),
    }
    with history_file.open('a') as f:
        f.write(json.dumps(entry) + '\n')

# Keep file size bounded
try:
    lines = history_file.read_text().splitlines()
    if len(lines) > 13000:
        history_file.write_text('\n'.join(lines[-13000:]) + '\n')
except Exception:
    pass

print(out)
