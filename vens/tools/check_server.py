#!/usr/bin/env python3
import time, json
import yaml, requests
from pathlib import Path

cfg=Path(r"C:\Users\Baxter\.continue\config.yaml")
try:
    data=yaml.safe_load(cfg.read_text(encoding='utf-8'))
    active=data.get('active_profile')
    profile=data.get('profiles',{}).get(active,{})
    model=profile.get('model','')
    api_base=profile.get('apiBase', 'http://127.0.0.1:8080')
    api_key=profile.get('apiKey','')
except Exception as e:
    print('failed to read config.yaml',e)
    api_base='http://127.0.0.1:8080'
    model=''
    api_key=''
print('api_base=',api_base)
print('active_profile=',active,'model=',model)

s=requests.Session()
if api_key:
    s.headers.update({'Authorization': f'Bearer {api_key}'})

print('\n== GET /v1/models ==')
try:
    t0=time.time(); r=s.get(api_base+'/v1/models', timeout=30); dt=time.time()-t0
    print('status', r.status_code, 'time_s', round(dt,3))
    try:
        print(r.json())
    except Exception:
        print(r.text[:1000])
except Exception as e:
    print('GET error', e)

print('\n== POST /v1/chat/completions (empty model) ==')
try:
    payload={'model':'','messages':[{'role':'user','content':'ping'}]}
    t0=time.time(); r=s.post(api_base+'/v1/chat/completions', json=payload, timeout=120); dt=time.time()-t0
    print('status', r.status_code, 'time_s', round(dt,3))
    try:
        print(json.dumps(r.json(), indent=2)[:1000])
    except Exception:
        print(r.text[:1000])
except Exception as e:
    print('POST empty-model error', e)

if model:
    print(f"\n== POST /v1/chat/completions (model={model}) ==")
    try:
        payload={'model':model,'messages':[{'role':'user','content':'ping'}]}
        t0=time.time(); r=s.post(api_base+'/v1/chat/completions', json=payload, timeout=300); dt=time.time()-t0
        print('status', r.status_code, 'time_s', round(dt,3))
        try:
            print(json.dumps(r.json(), indent=2)[:2000])
        except Exception:
            print(r.text[:1000])
    except Exception as e:
        print('POST specific-model error', e)
