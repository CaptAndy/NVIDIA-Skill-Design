"""Build a new runtime directory from verified downloads; never replace a model."""
import argparse
import json
import shutil
from pathlib import Path
from manifest import inventory, digest

def prepare(source, destination, lock):
    source=source.resolve(); destination=destination.absolute()
    if destination.exists() or destination.is_symlink():raise ValueError('Destination must be new')
    if destination.resolve().is_relative_to(source):raise ValueError('Destination must be outside source')
    rows=json.loads(lock.read_text(encoding='utf-8'))['files']
    expected={r['path'] for r in rows}
    if len(expected)!=len(rows):raise ValueError('Duplicate manifest path')
    actual={p.relative_to(source).as_posix() for p in inventory(source)}
    # Only known inert downloader bookkeeping may be omitted, never arbitrary hidden code.
    metadata={'.mv', '.msc', 'figures/.gitkeep'}
    if expected-actual or actual-expected-metadata:raise ValueError('Unexpected download file set')
    for row in rows:
        rel=Path(row['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Invalid manifest path')
        p=source/rel
        if p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:raise ValueError('Content mismatch')
    destination.mkdir(parents=True,exist_ok=False)
    for row in rows:
        p=destination/row['path'];p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/row['path'],p)
        if p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:raise ValueError('Copied content mismatch; do not use destination')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('source','destination','lock'):parser.add_argument(name,type=Path)
    args=parser.parse_args();prepare(args.source,args.destination,args.lock)
