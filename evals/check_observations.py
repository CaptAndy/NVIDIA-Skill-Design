"""Final shipped facts-only helper check, distinct from full-Skill decision replay."""
import importlib.util,json,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=root/'evals/results/observations.json');p.add_argument('--case');a=p.parse_args()
if a.out.exists():raise SystemExit('Output exists; preserve it and select another path')
s=importlib.util.spec_from_file_location('client',root/'screen-assistance/scripts/invoke_model.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
cases=[('public-progress-region','用户想查申请到哪一步，目前这里有结果了吗？'),('pending','用户问是不是已经办好。'),('upload-error','用户问为何上传不了，文件大小没有显示。')]
if a.case:cases=[x for x in cases if x[0]==a.case]
rows=[]
for name,prompt in cases:
 row=c.invoke(c.build_request('spark',prompt,image=root/'evals/fixtures'/f'{name}.png'),timeout=240)
 row['case']=name;rows.append(row)
 a.out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(row,ensure_ascii=False),flush=True)
