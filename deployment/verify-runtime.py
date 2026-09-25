import json,subprocess,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def docker(*args):return subprocess.check_output(['docker',*args],text=True)
started=time.monotonic();healthy=False
for attempt in range(72):
 try:
  with urllib.request.urlopen('http://127.0.0.1:18000/health',timeout=3) as r:healthy=r.status==200
 except Exception:pass
 if healthy:break
 time.sleep(5)
state=json.loads(docker('inspect','screen-assistance-vlm'))[0]
result={'healthy':healthy,'wait_seconds':round(time.monotonic()-started,2),'image':state['Image'],'container_started_at':state['State']['StartedAt'],'port_bindings':state['HostConfig']['PortBindings'],'config_label':state['Config']['Labels'].get('org.screen-assistance.config')}
log=subprocess.run(['docker','logs','screen-assistance-vlm'],capture_output=True,text=True)
text=log.stdout+log.stderr
result['incorrect_regex_warning_present']='incorrect regex pattern' in text
result['warning_lines']=[x for x in text.splitlines() if 'WARNING' in x or '[transformers]' in x][-15:]
if healthy:
 with urllib.request.urlopen('http://127.0.0.1:18000/v1/models',timeout=5) as r:result['model_ids']=[x['id'] for x in json.load(r)['data']]
result['passed']=healthy and result['image']=='sha256:9b2b3cb4d201e48efac830e8b1fd4d5f057be394def6f11cce50f3691d2f8e6a' and result['port_bindings']=={'8000/tcp':[{'HostIp':'127.0.0.1','HostPort':'18000'}]} and not result['incorrect_regex_warning_present'] and 'screen-assistance-vlm' in result.get('model_ids',[]) and bool(result['config_label'])
(root/'evals/results/restart-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False),flush=True)
raise SystemExit(0 if result['passed'] else 1)
