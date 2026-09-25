"""Paired repeated Spark visual calls; run without concurrent inference jobs."""
import importlib.util,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('client',ROOT/'evals/frozen/invoke_model.py');client=importlib.util.module_from_spec(s);s.loader.exec_module(client)
prompt='用户只是想找到办件进度查询入口。只说明这张页面的标题，以及目前是否有该用户的办理结果。不要识别验证码，不要声称已经填写、查询或提交。用两句中文。'
out=ROOT/'evals/results/speed.json'
if out.exists():raise SystemExit('Output exists')
rows=[]
for repeat in range(3):
 for variant in (['full','region'] if repeat%2==0 else ['region','full']):
  image=ROOT/'evals/fixtures'/('public-progress.png' if variant=='full' else 'public-progress-region.png')
  row=client.invoke(client.build_request('spark',prompt,image=image),timeout=240)
  row.update(repeat=repeat+1,variant=variant,image_bytes=image.stat().st_size)
  rows.append(row);out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(row,ensure_ascii=False),flush=True)
