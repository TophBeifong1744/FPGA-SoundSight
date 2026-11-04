"""Build the public board runtime using only this submission directory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    manifest = json.loads((ROOT/'build/file-map.json').read_text('utf-8'))
    spec=importlib.util.spec_from_file_location('ss_product_installer',ROOT/'build/tools/install_product.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    product_files=list(module.PAYLOAD)
    data = {}
    for row in manifest['files']:
        name = row['source_path']
        if (name.startswith(('software/', 'tools/', 'data/fixtures/')) or
                (name.startswith('soundsight') and name.endswith('.sh')) or name in product_files or
                (name.startswith('document/') and name.count('/')==1 and name.endswith('.md'))):
            if name.startswith(('software/stm32/', 'software/vitis/')):
                continue
            raw = (ROOT/row['restore_path']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != row['restore_sha256']:
                raise ValueError('Changed runtime input: '+name)
            # Linux scripts and source files use their restored names and bytes.
            if name.endswith(('.py','.sh','.c','.h','.md','.json','.txt')):
                raw=raw.replace(b'\r\n',b'\n')
            data[name]=raw
    for name in ('soundsight.bit','soundsight.hwh'):
        data[name]=(ROOT/'board/artifacts/screen_s2'/name).read_bytes()
    for name in data:
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or ':' in name:
            raise ValueError('Invalid runtime path: '+name)
        if name.endswith('speaker-template.json') or name.startswith(('logs/','speaker-profiles/','speaker-target-data/')) or '.local.' in name:
            raise ValueError('Private runtime input: '+name)
    data['SOURCE.json']=(json.dumps(dict(distribution='public_local_enrollment',
        revision='20261104', enrollment='Record and select a new local user',
        hardware='S2', input='submission file-map'),indent=2)+'\n').encode()
    missing=set(product_files)-set(data)
    if missing:raise ValueError('Missing product dependencies: '+str(sorted(missing)))
    info=dict(revision='S2_P1_CF1A_20261103',source_commit=manifest['baseline_commit'],
        distribution='public_local_enrollment',distribution_revision='20261104',
        private=False,private_assets=[],product_files=product_files,
        files={n:hashlib.sha256(raw).hexdigest() for n,raw in sorted(data.items())})
    items={'SoundSight_PYNQ_3D_Speaker/'+n:raw for n,raw in data.items()}
    items['manifest.json']=(json.dumps(info,indent=2)+'\n').encode()
    items['__main__.py']=data['tools/install_current_runtime.py']
    output=Path(output).resolve()
    if output.exists():raise ValueError('Choose a new output; existing archives are preserved')
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for name,raw in sorted(items.items()):
            entry=ZipInfo(name,(2026,11,4,0,0,0));entry.compress_type=ZIP_DEFLATED
            entry.create_system=3
            entry.external_attr=(0o100755 if name.endswith(('.sh','/pipeline_backend')) else 0o100644)<<16
            z.writestr(entry,raw)
    with ZipFile(output) as z:
        assert z.testzip() is None
    print('PUBLIC_RUNTIME_READY='+str(output)+' FILES='+str(len(items))+' HARDWARE_ACTIONS=0')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output)
