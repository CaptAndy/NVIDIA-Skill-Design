"""Create/check a full content lock of model files; no unsafe pickle loading."""
import argparse,hashlib,json
from pathlib import Path

def inventory(base):
 base=base.resolve()
 if not base.is_dir():raise SystemExit('Model directory missing')
 files=[]
 for x in sorted(base.rglob('*')):
  if x.is_symlink():raise SystemExit('Symlinks are not allowed: '+str(x.relative_to(base)))
  if x.is_file():files.append(x)
  elif not x.is_dir():raise SystemExit('Special files are not allowed')
 return files
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['create','verify']);p.add_argument('directory',type=Path);p.add_argument('manifest',type=Path);a=p.parse_args()
 if a.mode=='create':
  base=a.directory.resolve()
  files=[{'path':x.relative_to(base).as_posix(),'bytes':x.stat().st_size,'sha256':digest(x)} for x in inventory(base)]
  a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps({'source':'stepfun-ai/Step3-VL-10B','source_revision':'master (original download); content-pinned by SHA256 below','files':files},indent=2),encoding='utf-8');print('locked',len(files),'files')
 else:
  obj=json.loads(a.manifest.read_text(encoding='utf-8'));base=a.directory.resolve()
  expected={row['path'] for row in obj['files']}
  if len(expected)!=len(obj['files']):raise SystemExit('Duplicate manifest path')
  actual={x.relative_to(base).as_posix() for x in inventory(base)}
  if actual!=expected:raise SystemExit('Model file set differs from content lock')
  for row in obj['files']:
   target=(base/row['path']).resolve()
   if not target.is_relative_to(base):raise SystemExit('Invalid path')
   if not target.is_file() or target.stat().st_size!=row['bytes'] or digest(target)!=row['sha256']:raise SystemExit('Mismatch: '+row['path'])
  print('All',len(obj['files']),'files match')
if __name__=='__main__':main()
