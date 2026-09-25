"""Explicitly preserve Step tokenizer regex; do not apply a Mistral conversion."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
config=json.loads((a.model/'config.json').read_text())
if config.get('model_type')!='step_robotics':raise SystemExit('Unverified model type; no workaround applied')
data=json.loads((a.model/'tokenizer_config.json').read_text())
data['fix_mistral_regex']=False
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('Preserved original tokenizer behavior; explicit non-Mistral flag')
