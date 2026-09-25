"""Read configuration and run synthetic probes in the project container."""
import json, subprocess, urllib.request

def inspect(kind,name):
    return json.loads(subprocess.check_output(['docker',kind,'inspect',name],text=True))[0]

state=inspect('container','screen-assistance-vlm')
host=state['HostConfig']
networks=state['NetworkSettings']['Networks']
network_details={name:inspect('network',name) for name in networks}
probe=r'''
import os,socket,json,pathlib
result={'uid':os.getuid()}
result['proc_security']={line.split(':')[0]:line.split(':')[1].strip() for line in pathlib.Path('/proc/self/status').read_text().splitlines() if line.startswith(('CapEff:','NoNewPrivs:'))}
sock=socket.socket();sock.settimeout(3)
try:sock.connect(('1.1.1.1',443));result['external_tcp_blocked']=False
except OSError as e:result['external_tcp_blocked']=True;result['external_error']=type(e).__name__
finally:sock.close()
result['default_route_absent']=not any(line.split()[1]=='00000000' for line in pathlib.Path('/proc/net/route').read_text().splitlines()[1:])
print(json.dumps(result))
'''
runtime=json.loads(subprocess.check_output(['docker','exec','screen-assistance-vlm','python3','-c',probe],text=True))
relay=inspect('container','screen-assistance-relay')
target=networks['screen-assistance-isolated-v3']['IPAddress']
relay_ok=bool(relay['State']['Running'] and relay['HostConfig']['NetworkMode']=='host'
    and relay['HostConfig']['ReadonlyRootfs'] and relay['HostConfig']['CapDrop']==['ALL']
    and relay['Config']['Cmd']==['/relay.py','--target',target]
    and relay['Config']['User']==state['Config']['User']
    and any(x.startswith('no-new-privileges') for x in relay['HostConfig']['SecurityOpt']))
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
with opener.open('http://127.0.0.1:18000/health',timeout=5) as response:health=response.status
result={'health':health,'image':state['Image'],'running':state['State']['Running'],'user':state['Config']['User'],
        'read_only_root':host['ReadonlyRootfs'],'cap_drop':host['CapDrop'],'security_opt':host['SecurityOpt'],
        'port_bindings':host['PortBindings'],'networks':{n:{'internal':v['Internal'],'members':len(v['Containers'])} for n,v in network_details.items()},
        'mounts':[{'destination':m['Destination'],'rw':m['RW']} for m in state['Mounts']], 'runtime':runtime,'relay_fixed_target_verified':relay_ok}
result['passed']=bool(health==200 and result['running'] and result['read_only_root'] and host['CapDrop']==['ALL']
    and any(x.startswith('no-new-privileges') for x in host['SecurityOpt']) and runtime['uid']!=0
    and runtime['proc_security']=={'CapEff':'0000000000000000','NoNewPrivs':'1'}
    and runtime['external_tcp_blocked'] and runtime['default_route_absent'] and len(network_details)==1
    and all(n['Internal'] for n in network_details.values())
    and host['PortBindings']=={'8000/tcp':[{'HostIp':'127.0.0.1','HostPort':'18000'}]} and relay_ok)
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
