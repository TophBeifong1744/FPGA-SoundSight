"""Check the public runtime ZIP and install transaction with hardware disabled."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();out=a.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('Use a new empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    archive=ROOT/'board/artifacts/soundsight_pynq_3d_speaker.zip'
    installer=module('public_installer',ROOT/'build/tools/install_current_runtime.py')
    manifest,data=installer.load_package(archive)
    assert manifest['distribution']=='public_local_enrollment'
    assert not manifest['private'] and manifest['private_assets']==[]
    assert not any(n.endswith('speaker-template.json') or n.startswith(('speaker-profiles/','logs/')) for n in data)
    target=out/'runtime'
    first=installer.install(archive,target,'offline-boot-1')
    assert first['hardware_actions']==0 and first['reboot_required']
    second=installer.install(archive,target,'offline-boot-2')
    assert second['changed_files']==0 and not second['reboot_required']
    sys.path.insert(0,str(target/'software/ps'))
    from speaker_settings import verify_assets
    from speaker_targets import list_targets
    from speaker_permission import load_settings
    from speaker_models import verify_candidates
    core=target/'software/ps/speaker_core'
    assert verify_assets(core,use_selected=False) is None
    assert list_targets(target)=={'active_target':None,'targets':[]}
    assert load_settings(target)['threshold'] is None
    verify_candidates(core)
    try:verify_assets(core)
    except ValueError as e:assert 'NO_ACTIVE_TARGET' in str(e)
    else:raise AssertionError('Empty installation activated a target')
    # ELF32 little-endian ARM. No ARM binary is executed on the test host.
    elf={}
    for name in ('pipeline_backend','lib/libonnxruntime.so.1.17.3'):
        raw=(core/name).read_bytes()
        assert raw[:6]==b'\x7fELF\x01\x01' and int.from_bytes(raw[18:20],'little')==40
        elf[name]='ELF32_ARM'
    logs=target/'logs';logs.mkdir(exist_ok=True)
    (logs/'keep.json').write_bytes(b'local log')
    (target/'settings.local.json').write_bytes(b'{"local":true}')
    installer.install(archive,target,'offline-boot-2')
    assert (logs/'keep.json').read_bytes()==b'local log'
    assert (target/'settings.local.json').read_bytes()==b'{"local":true}'
    assets=core/'live-assets.json';original=assets.read_bytes()
    assets.write_text('{"sha256":{}}',encoding='utf-8')
    try:installer.install(archive,target,'offline-boot-2')
    except ValueError as e:assert 'USE_NEW_DESTINATION' in str(e)
    else:raise AssertionError('Legacy assets overwritten')
    assert assets.read_text('utf-8')=='{"sha256":{}}'
    assets.write_bytes(original)
    # Simulate systemd only, using a temporary unit file.
    calls=[]
    def ctl(*args):
        calls.append(args)
        value={'is-active':'inactive','show':'loaded','is-enabled':'disabled'}.get(args[0],'')
        return SimpleNamespace(returncode=0,stdout=value,stderr='')
    product=module('public_product_installer',ROOT/'build/tools/install_product.py')
    pr=product.install(ROOT/'board/artifacts/soundsight_screen_product_p1.zip',target,
        out/'soundsight-product.service',ctl=ctl,unit_root=Path('/opt/fpga_soundsight'))
    assert not pr['service_started'] and pr['hardware_actions']==0
    assert not any(x[0] in ('start','restart','stop') for x in calls)
    for n,sha in manifest['files'].items():
        assert hashlib.sha256((target/n).read_bytes()).hexdigest()==sha,n
    rebuilt=out/'runtime-rebuilt.zip'
    run=subprocess.run([sys.executable,'-B',str(ROOT/'build/package_runtime.py'),'--output',str(rebuilt)],
        cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    assert run.returncode==0,run.stdout+run.stderr
    assert rebuilt.read_bytes()==archive.read_bytes()
    result=dict(scope='OFFLINE_PUBLIC_RUNTIME',payload_files=len(data),
        private_profiles=0,fresh_install='PASS',repeat_install='PASS',
        public_assets_verified='PASS',empty_start_and_no_permission='PASS',
        local_settings_and_logs_preserved='PASS',legacy_baseline_preserved='PASS',
        product_service_install='PASS_WITH_FAKE_SYSTEMD',
        standalone_rebuild='BYTE_IDENTICAL',binaries=elf,
        hardware_actions=0,arm_inference='NOT_RUN')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
