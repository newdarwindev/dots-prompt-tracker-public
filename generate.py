#!/usr/bin/env python3
"""Build a synthetic public prompt tracker or access-controlled private report."""
import argparse
import html
import json
from pathlib import Path


def build(data, audience):
    if audience == 'public' and data.get('classification') != 'synthetic':
        raise ValueError('public output requires synthetic input')
    seen = set()
    rows = []
    for task in data['tasks']:
        key = task['source_id']
        if key in seen:
            continue
        seen.add(key)
        prompt = html.escape(task['prompt'])
        status = html.escape(task.get('status') or 'unknown')
        approval = html.escape(task.get('approval') or 'unverified')
        elapsed = task.get('elapsed_minutes')
        elapsed_text = 'unknown' if elapsed is None else f'{int(elapsed)} min observed window'
        rows.append(f'<tr><td>{prompt}</td><td>{status}</td><td>{approval}</td><td>{elapsed_text}</td><td>unknown</td></tr>')
    return '<!doctype html><meta charset="utf-8"><title>Prompt progress</title><h1>Prompt progress</h1><p>Elapsed window includes waiting and is not active compute. Token and monetary cost are unknown unless separately measured.</p><table><thead><tr><th>Prompt</th><th>Progress</th><th>Approval</th><th>Elapsed</th><th>Model cost</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--audience', choices=['public', 'private'], required=True)
    a = p.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(build(json.loads(a.input.read_text()), a.audience))

if __name__ == '__main__':
    main()
