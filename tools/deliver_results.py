"""Publish one result batch into dated Codex/project/experiment directories.

Example: python3 tools/deliver_results.py --title final-refinement \
  --source outputs/stage1_final_refinement --report docs/stage1_final_refinement.md
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
from zoneinfo import ZoneInfo

WORKSPACE=Path(__file__).resolve().parents[1]
DEFAULT_ROOT=Path('/Users/ququ/Documents/Codex')
PROJECT=WORKSPACE.name


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def next_number(root):
    values=[]
    for folder in root.glob(f'????-??-??/{PROJECT}/experiment_*'):
        match=re.match(r'experiment_(\d+)_',folder.name)
        if match:values.append(int(match.group(1)))
    return max(values,default=0)+1


def publish(source,title,report=None,extras=None,date=None,root=DEFAULT_ROOT):
    source=Path(source).resolve();root=Path(root).resolve()
    if not source.is_dir():raise ValueError(f'Missing result directory: {source}')
    date=date or datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d')
    datetime.strptime(date,'%Y-%m-%d')
    slug=re.sub(r'[^a-zA-Z0-9_-]+','-',title).strip('-').lower()
    if not slug:raise ValueError('Provide a useful delivery title')
    parent=root/date/PROJECT;parent.mkdir(parents=True,exist_ok=True)
    # mkdir(exist_ok=False) prevents collision/overwrite even with concurrent publishers.
    number=next_number(root)
    while True:
        destination=parent/f'experiment_{number:03d}_{slug}'
        try:destination.mkdir();break
        except FileExistsError:number+=1
    mappings={'results':source}
    for name,path in (extras or {}).items():
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',name) or name in ('results','assets'):
            raise ValueError(f'Invalid supplemental folder name: {name}')
        mappings[name]=Path(path).resolve()
    files=[]
    for name,original in mappings.items():
        if not original.is_dir():raise ValueError(f'Missing supplement: {original}')
        shutil.copytree(original,destination/name)
        for src in sorted(original.rglob('*')):
            if src.is_file():
                target=destination/name/src.relative_to(original)
                digest=sha(src)
                if sha(target)!=digest:raise RuntimeError(f'Copy checksum mismatch: {target}')
                files.append({'path':str(target.relative_to(destination)),'sha256':digest,'source':str(src)})
    # Reproduction metadata references repository-relative font/atlas assets.
    if (WORKSPACE/'assets').is_dir():
        shutil.copytree(WORKSPACE/'assets',destination/'assets')
        for asset in sorted((destination/'assets').rglob('*')):
            if asset.is_file():files.append({'path':str(asset.relative_to(destination)),'sha256':sha(asset),'source':str(WORKSPACE/asset.relative_to(destination))})
    if report:
        report=Path(report).resolve();body=report.read_text()
        for name,original in mappings.items():
            body=body.replace(f'../outputs/{original.name}/',f'{name}/')
            body=body.replace(f'../{original.relative_to(WORKSPACE)}/',f'{name}/') if original.is_relative_to(WORKSPACE) else body
            body=body.replace(str(original)+'/',name+'/')
        # Preserve direct access to the source workspace for commands/source references.
        (destination/'report.md').write_text(body)
        if '](shader.md)' in body and (report.parent/'shader.md').exists():shutil.copy2(report.parent/'shader.md',destination/'shader.md')
    provenance={'experiment':number,'title':title,'date':date,'timezone':'America/Chicago',
                'published_at':datetime.now(ZoneInfo('America/Chicago')).isoformat(),
                'source_workspace':str(WORKSPACE),'source_results':{k:str(v) for k,v in mappings.items()},
                'source_report':str(report) if report else None,
                'copy_verification':'All copied result and asset bytes matched their source SHA-256.',
                'historical_source_code':('Frozen reproduction snapshot included under results/reproduction; see its README for scope.'
                    if (source/'reproduction'/'README.md').exists() else
                    'Not snapshotted; historical renderer hashes remain in result metadata. Current workspace code is not claimed to be the historical version.')}
    (destination/'provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n')
    previews=[]
    for candidate in ['inspection_contact_sheet.png','previews/contact_sheet.png','validation/contact_sheet.png','B_single_digit_front.png','A_three_visible_pins.png']:
        if (destination/'results'/candidate).exists():previews.append(f'- [Preview: {Path(candidate).name}](results/{candidate})')
    summary=f'# Experiment {number:03d} — {title}\n\nDate: {date} (America/Chicago)\n\nSource workspace: `{WORKSPACE}`\n\n'
    summary+='This directory contains one independent delivery. Earlier deliveries and source artifacts are preserved.\n\n'
    summary+='\n'.join(previews)+'\n\n'
    if report:summary+='- [Report and artifact links](report.md)\n'
    summary+='- [Results](results/)\n'
    for name in mappings:
        if name!='results':summary+=f'- [Supplement: {name}]({name}/)\n'
    summary+='- [Provenance and verification](provenance.json)\n- [SHA-256 manifest](manifest.sha256.json)\n'
    (destination/'README.md').write_text(summary)
    # Include generated delivery documents in the delivery's own manifest too.
    seen={f['path'] for f in files}
    for path in sorted(destination.rglob('*')):
        relative=str(path.relative_to(destination))
        if path.is_file() and relative not in seen:files.append({'path':relative,'sha256':sha(path),'source':'generated delivery document'})
    (destination/'manifest.sha256.json').write_text(json.dumps({'files':files},indent=2,ensure_ascii=False)+'\n')
    for entry in files:
        if sha(destination/entry['path'])!=entry['sha256']:raise RuntimeError('Final delivery checksum failed')
    index=parent/'README.md'
    entries=sorted(p.name for p in parent.glob('experiment_*') if p.is_dir())
    index.write_text(f'# {date} — {PROJECT}\n\nEach experiment is an independent delivery.\n\n'+''.join(f'- [{name}]({name}/README.md)\n' for name in entries))
    return destination


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--title',required=True)
    parser.add_argument('--report',type=Path);parser.add_argument('--date',help='Delivery date, defaults to current America/Chicago date')
    parser.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--extra',action='append',default=[],metavar='NAME=SOURCE')
    args=parser.parse_args();extras=dict(value.split('=',1) for value in args.extra)
    print(publish(args.source,args.title,args.report,extras,args.date,args.root))


if __name__=='__main__':main()
