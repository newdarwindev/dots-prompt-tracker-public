#!/usr/bin/env python3
"""Render the allowlisted public aggregate pipeline projection."""
import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

STAGE_KEYS=('export','dataset','consumer','optimizer')
STAGE_FIELDS={
 'export':{'key','state','channels','records','positive_labels','negative_labels'},
 'dataset':{'key','state','version','notebook_tests'},
 'consumer':{'key','state','tests'},
 'optimizer':{'key','state','train','validation','test','ready_for_optimizer','reason'},
}
TOP_FIELDS={'schema_version','classification','source','cutoff_utc','refresh_mode','stages','real_model_calls','training_runs','deployments'}
STATE={'export':'complete','dataset':'verified','consumer':'validated','optimizer':'blocked'}

def validate(data):
    if set(data)!=TOP_FIELDS or data['schema_version']!=1 or data['classification']!='public_aggregate': raise ValueError('projection schema mismatch')
    if data['source']!='verified private aggregate snapshot' or data['refresh_mode']!='manual': raise ValueError('provenance or refresh mismatch')
    cutoff=datetime.fromisoformat(data['cutoff_utc'].replace('Z','+00:00'))
    if cutoff.tzinfo is None: raise ValueError('naive cutoff')
    stages=data['stages']
    if not isinstance(stages,list) or tuple(s.get('key') for s in stages)!=STAGE_KEYS: raise ValueError('stage keys/order mismatch')
    for s in stages:
        k=s['key']
        if set(s)!=STAGE_FIELDS[k] or s['state']!=STATE[k]: raise ValueError('stage field/state mismatch')
        for field,val in s.items():
            if field in ('key','state','reason'): continue
            if field=='ready_for_optimizer':
                if val is not False: raise ValueError('optimizer readiness mismatch')
            elif type(val) is not int or val<0: raise ValueError('invalid count')
    if stages[3]['reason']!='missing source context': raise ValueError('reason mismatch')
    for k in ('real_model_calls','training_runs','deployments'):
        if type(data[k]) is not int or data[k]!=0: raise ValueError('unsupported activity claim')
    return cutoff

CSS='''
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#0b1020;color:#edf3fb}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 78% -12%,#31406a,transparent 35%),radial-gradient(circle at 10% 10%,#24224d,transparent 32%),#0b1020}.wrap{max-width:1120px;margin:auto;padding:42px 22px 78px}.eyebrow{color:#a6e1d0;text-transform:uppercase;letter-spacing:.17em;font-size:.74rem;font-weight:800}h1{font-size:clamp(2.3rem,5vw,4.3rem);letter-spacing:-.06em;margin:11px 0}h2{font-size:1.2rem;margin:0 0 11px}p{color:#b3c1d4;line-height:1.55}.sub{max-width:740px}.meta{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 32px}.pill{border:1px solid #45516d;background:#1b2941;border-radius:50px;padding:9px 13px;color:#d8e7f1;font-size:.8rem}.hero{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:31px}.stat{border:1px solid #374760;border-radius:17px;background:#19243a;padding:18px}.stat strong{display:block;font-size:1.8rem}.stat span{color:#9fb0c6;font-size:.82rem}.section-title{margin:36px 0 15px;color:#9be5d2;font-size:.76rem;text-transform:uppercase;letter-spacing:.17em}.flow{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{background:linear-gradient(145deg,#202d46,#151f35);border:1px solid #3b4d67;border-radius:19px;padding:22px}.number{color:#8da7c3;font-size:.78rem;font-weight:800;letter-spacing:.15em}.state{display:inline-block;background:#1d4d46;color:#9cead0;border-radius:30px;padding:7px 11px;font-size:.76rem;font-weight:800;margin:7px 0 14px}.detail{display:flex;gap:8px;flex-wrap:wrap}.detail span{background:#111a2d;border-radius:9px;padding:10px 12px;color:#d3dfed;font-size:.87rem}.blocked{margin-top:16px;border-color:#745340;background:linear-gradient(130deg,#32273a,#1b2235)}.blocked .state{background:#5a392a;color:#ffd2ab}.blocked strong{color:#ffcd9f}.foot{border-left:3px solid #a6e1d0;padding-left:16px;margin-top:36px}.muted{color:#8ca0b7;font-size:.82rem}@media(max-width:760px){.hero{grid-template-columns:repeat(2,1fr)}.flow{grid-template-columns:1fr}.wrap{padding:28px 19px 60px}}
'''

def build(data):
    validate(data)
    e,d,c,o=data['stages']
    cutoff=html.escape(data['cutoff_utc'])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Workflow refinery status</title><style>{CSS}</style><main class="wrap"><div class="eyebrow">New Darwin · workflow refinery</div><h1>From export to evidence</h1><p class="sub">A bounded operational snapshot of the public-facing pipeline. Validation is complete through the consumer; optimization is waiting on missing source context.</p><div class="meta"><span class="pill">Verified cutoff · {cutoff}</span><span class="pill" id="freshness">Manual snapshot</span><span class="pill">Aggregate counts only</span></div><section class="hero"><div class="stat"><strong>{e['channels']}</strong><span>Channels exported</span></div><div class="stat"><strong>{e['records']}</strong><span>Records exported</span></div><div class="stat"><strong>{d['notebook_tests']}</strong><span>Notebook tests passed</span></div><div class="stat"><strong>{c['tests']}</strong><span>Consumer tests passed</span></div></section><div class="section-title">Implemented and verified</div><section class="flow"><article class="card"><div class="number">01 / EXPORT</div><span class="state">Complete</span><h2>Source export</h2><p>Bounded source snapshot captured at the cutoff.</p><div class="detail"><span>{e['channels']} channels</span><span>{e['records']} records</span><span>{e['positive_labels']} positive labels</span><span>{e['negative_labels']} negative labels</span></div></article><article class="card"><div class="number">02 / DATASET</div><span class="state">Verified</span><h2>Dataset conversion</h2><p>Version {d['version']} conversion checks passed.</p><div class="detail"><span>{d['notebook_tests']} notebook tests</span></div></article><article class="card"><div class="number">03 / CONSUMER</div><span class="state">Validated</span><h2>Refinery consumer</h2><p>Offline validation passed, without paid model execution.</p><div class="detail"><span>{c['tests']} tests</span></div></article></section><div class="section-title">Blocked next stage</div><article class="card blocked"><div class="number">04 / OPTIMIZER</div><span class="state">Blocked</span><h2>Training inputs are not ready</h2><p>Missing source context keeps the train / validation / test split at <strong>{o['train']} / {o['validation']} / {o['test']}</strong>. Ready for optimizer: <strong>no</strong>.</p><div class="detail"><span>{data['real_model_calls']} real model calls</span><span>{data['training_runs']} training runs</span><span>{data['deployments']} deployments</span></div></article><div class="foot"><p>Source: verified private aggregate snapshot at {cutoff}. This public projection contains sanitized labels and counts only. Refresh is manual; the page does not read private accounts or synchronize automatically.</p><p class="muted">These counts describe this pipeline, not Codex session usage, model spend, task approval or all-channel coverage.</p></div></main><script>const cut=new Date('{cutoff}').getTime(),hours=(Date.now()-cut)/36e5;document.querySelector('#freshness').textContent=hours>24?'Snapshot stale · manual refresh needed':'Manual snapshot · within 24h of cutoff';</script></html>'''

def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(build(json.loads(a.input.read_text())))
if __name__=='__main__':main()
