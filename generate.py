#!/usr/bin/env python3
"""Render a synthetic public tracker or a protected private report."""
import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlparse

CSS='''
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#0c1020;color:#edf1fb}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% -10%,#483462 0,transparent 35%),radial-gradient(circle at 95% 0,#1f4757 0,transparent 30%),#0c1020}.wrap{max-width:1240px;margin:auto;padding:38px 22px 80px}.eyebrow{font-size:.76rem;font-weight:800;letter-spacing:.17em;text-transform:uppercase;color:#f6b86f}h1{font-size:clamp(2.2rem,5vw,4.2rem);letter-spacing:-.055em;margin:12px 0 8px}p{color:#aab5ce;line-height:1.55}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:29px 0 34px}.stat{border:1px solid #3d3b59;background:#1a1c36;border-radius:17px;padding:18px}.stat strong{display:block;font-size:1.8rem}.stat span{font-size:.82rem;color:#aab5ce}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-bottom:15px}input{background:#1a1c36;border:1px solid #555274;color:#fff;padding:12px 15px;border-radius:11px;font:inherit}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.card{border:1px solid #484562;background:linear-gradient(145deg,#252441,#171b32);border-radius:20px;padding:21px;min-width:0}.head{display:flex;justify-content:space-between;gap:12px;align-items:start}.title{font-size:1.15rem;font-weight:750;margin:0;color:#fff}.badge{font-size:.73rem;font-weight:750;border-radius:30px;background:#504064;padding:7px 10px;white-space:nowrap}.complete{background:#245247;color:#9be9ce}.active{background:#534425;color:#ffe0a3}.bar{height:7px;background:#3a3c5b;border-radius:8px;margin:20px 0}.bar span{display:block;height:100%;background:linear-gradient(90deg,#f6b86f,#d292ef);border-radius:8px}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}.metric{padding:10px;background:#17192f;border-radius:11px}.metric strong{display:block;font-size:1.06rem}.metric small{color:#9eabc5}.section{margin-top:18px;border-top:1px solid #43445e;padding-top:14px}.label{font-size:.72rem;color:#9eabc5;text-transform:uppercase;letter-spacing:.13em;font-weight:800}.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.chip{font-size:.75rem;background:#343954;border-radius:20px;padding:6px 9px}.source{font-size:.75rem;color:#9eabc5;margin-top:8px;overflow-wrap:anywhere}.source a{color:#b9b8ff}.note{border-left:3px solid #f6b86f;padding-left:15px;margin-top:30px;font-size:.83rem}.empty{display:none}@media(max-width:730px){.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.toolbar{display:block}.toolbar input{width:100%;margin-top:7px}.metrics{grid-template-columns:repeat(2,1fr)}}
'''
def esc(v): return html.escape(str(v if v is not None else 'unknown'))
def total_known(items,key):
    vals=[i.get(key) for i in items]
    return str(sum(vals)) if vals and all(isinstance(v,(int,float)) for v in vals) else 'unknown'
def reactions(task):
    seen=set();out=[]
    for r in task.get('reactions',[]):
        key=(r.get('channel_id'),r.get('message_ts'),r.get('user_id'),r.get('emoji'))
        if key in seen: continue
        seen.add(key);out.append(r)
    return out

def approval_for(task, rs, owner_user_id):
    for r in rs:
        if owner_user_id and r.get('user_id') == owner_user_id and r.get('emoji') in ('+1', 'thumbsup', '👍'):
            return 'approved · owner 👍 · ' + str(r.get('message_ts') or 'timestamp unknown')
    return 'unverified'

def build(data,audience):
    if audience=='public' and data.get('classification')!='synthetic': raise ValueError('public output requires synthetic input')
    seen=set();cards=[];complete=0;known_sessions=0;reaction_count=0
    for task in data['tasks']:
        key=task['source_id']
        if key in seen: continue
        seen.add(key)
        sessions=task.get('sessions',[])
        rs=reactions(task)
        reaction_count+=len(rs)
        status=task.get('status') or 'unknown'
        if status.lower()=='complete': complete+=1
        if sessions: known_sessions+=len(sessions)
        progress=task.get('progress_percent')
        if not isinstance(progress,(int,float)) or not 0<=progress<=100: progress=0
        computers=sorted({s.get('computer') for s in sessions if s.get('computer')})
        computer_text=', '.join(computers) if computers and len(computers)==len(sessions) else 'unknown' if not computers else ', '.join(computers)+' · some unknown'
        elapsed=task.get('elapsed_minutes')
        elapsed_text=f'{elapsed} min window' if isinstance(elapsed,(int,float)) else 'unknown'
        rx=''.join(f'<span class="chip">{esc(r.get("emoji"))} · {esc(r.get("user_label") or "actor unknown")} · {esc(r.get("message_ts"))}</span>' for r in rs) or '<span class="chip">none observed</span>'
        source=task.get('source_url')
        p=urlparse(source or '')
        source_html=f'<a href="{html.escape(source,quote=True)}">Source ↗</a>' if p.scheme=='https' and p.hostname else 'Source unavailable'
        metrics=[('Sessions',str(len(sessions)) if task.get('session_coverage')=='complete' else str(len(sessions))+' known / total unknown'),('Computers',computer_text),('Files touched (session sum)',total_known(sessions,'files_changed')),('Lines + / −',total_known(sessions,'additions')+' / '+total_known(sessions,'deletions')),('Tokens',total_known(sessions,'tokens')),('Messages',total_known(sessions,'messages')),('Elapsed',elapsed_text),('Model cost','unknown' if task.get('model_cost') is None else str(task['model_cost'])),('Approval',approval_for(task,rs,data.get('owner_user_id')))]
        met=''.join(f'<div class="metric"><strong>{esc(v)}</strong><small>{esc(k)}</small></div>' for k,v in metrics)
        cards.append(f'<article class="card" data-name="{esc(task["prompt"].lower())}"><div class="head"><h2 class="title">{esc(task["prompt"])}</h2><span class="badge {"complete" if status.lower()=="complete" else "active"}">{esc(status)}</span></div><div class="bar" aria-label="{progress}% progress"><span style="width:{progress}%"></span></div><div class="metrics">{met}</div><div class="section"><div class="label">Related thread reactions · {len(rs)}</div><div class="chips">{rx}</div><div class="source">{source_html} · Observed {esc(task.get("observed_at"))}</div></div></article>')
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Prompt workboard</title><style>{CSS}</style><main class="wrap"><div class="eyebrow">New Darwin · work intelligence</div><h1>Prompt workboard</h1><p>Progress, session evidence and reaction provenance in one place.</p><section class="stats"><div class="stat"><strong>{len(cards)}</strong><span>Tracked prompts</span></div><div class="stat"><strong>{complete}</strong><span>Complete</span></div><div class="stat"><strong>{known_sessions}</strong><span>Known sessions</span></div><div class="stat"><strong>{reaction_count}</strong><span>Distinct reactions</span></div></section><div class="toolbar"><div class="eyebrow">Task ledger</div><input id="q" type="search" placeholder="Filter prompts" aria-label="Filter prompts"></div><section class="grid">{''.join(cards)}</section><p class="empty" id="empty">No matching prompts.</p><p class="note">{('Synthetic demo: all prompts and reactions are fictional. ' if audience=='public' else 'Private report: verify source access before sharing. ')}Unknown is not zero. Elapsed windows include waiting and are not active compute or token spend. Reactions identify actors and sources; bot reactions do not grant approval.</p></main><script>const q=document.querySelector('#q'),cards=[...document.querySelectorAll('.card')],empty=document.querySelector('#empty');q.addEventListener('input',()=>{{let n=0;for(const c of cards){{const show=c.dataset.name.includes(q.value.toLowerCase());c.hidden=!show;if(show)n++}}empty.style.display=n?'none':'block'}});</script></html>'''
def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);p.add_argument('--audience',choices=['public','private'],required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(build(json.loads(a.input.read_text()),a.audience))
if __name__=='__main__':main()
