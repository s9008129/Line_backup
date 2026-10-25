"""Actual dynamic inventory, stable sampling and independent full-pixel decoder."""
import os
from pathlib import Path
import stat
import subprocess
import time
from collections import Counter
from line_backup_acceptance.common import utc_now
from line_backup_acceptance.project_binding import ProjectReader,strict_json,sha
from .schema import require

PARTIAL=('.part','.partial','.tmp','.temp','.download','.crdownload','.incomplete','.filepart')

def inventory(root,destination):
    require(destination.startswith(root+'/backups/'),'DESTINATION_CONTAINMENT')
    reader=ProjectReader(root);relative=destination[len(root)+1:]
    parent=None
    try:
        parent=reader.open(relative,directory=True);before=ProjectReader.ident(os.fstat(parent))
        names=sorted(os.listdir(parent));rows=[]
        for name in names:
            st=os.stat(name,dir_fd=parent,follow_symlinks=False)
            require(stat.S_ISREG(st.st_mode) and not name.startswith('.'),'INVALID_DOWNLOAD_ENTRY')
            require(st.st_size>0 and not name.lower().endswith(PARTIAL),'DOWNLOAD_NOT_CLEAN_YET')
            raw,ident=reader.read(relative+'/'+name,'DOWNLOAD_READ_ERROR')
            if raw.startswith(b'\xff\xd8'):mime='image/jpeg'
            elif raw.startswith(b'\x89PNG\r\n\x1a\n'):mime='image/png'
            else:require(False,'UNSUPPORTED_DOWNLOAD_TYPE')
            rows.append(dict(relative_path=name,size=len(raw),mtime_ns=ident[4],mime=mime,sha256=sha(raw),
                status='OK',type='regular',failure_class=None))
        require(names==sorted(os.listdir(parent)) and before==ProjectReader.ident(os.fstat(parent)),'DOWNLOAD_CHANGED')
        reader.fresh_root()
        return rows
    finally:
        if parent is not None:os.close(parent)
        reader.close()

def verify(root,destination,expected,cfg,decoder,decoder_sha,*,clock=time.monotonic,sleep=time.sleep,after_decode=None):
    binary=ProjectReader(str(Path(decoder).parent))
    try:raw,_=binary.read(Path(decoder).name)
    finally:binary.close()
    require(sha(raw)==decoder_sha,'DECODER_DRIFT')
    start=clock();samples=[];previous=None;consecutive=0
    while True:
        try:rows=inventory(root,destination)
        except Exception as exc:
            from line_backup_acceptance.common import AcceptanceError
            if not isinstance(exc,AcceptanceError) or exc.code not in ('DOWNLOAD_CHANGED','DOWNLOAD_READ_ERROR','DOWNLOAD_NOT_CLEAN_YET'):
                raise
            require(clock()-start<cfg['max_wait_seconds'],'DOWNLOAD_TIMEOUT')
            previous=None;consecutive=0;sleep(cfg['poll_interval_seconds']);continue
        instant=clock()
        consecutive=consecutive+1 if rows==previous else 1
        samples.append(dict(monotonic=instant,count=len(rows),inventory=rows))
        if len(rows)==expected and consecutive>=cfg['stable_samples']:break
        require(len(rows)<=expected,'EXTRA_DOWNLOAD_FILES')
        require(instant-start<cfg['max_wait_seconds'],'DOWNLOAD_TIMEOUT')
        previous=rows;sleep(cfg['poll_interval_seconds'])
    require(all(samples[i]['monotonic']-samples[i-1]['monotonic']>=cfg['poll_interval_seconds'] for i in range(1,len(samples))),
        'STABILITY_INTERVAL')
    command=subprocess.run([decoder,destination,str(expected)],capture_output=True,timeout=120)
    require(command.returncode==0,'PIXEL_DECODE_FAILED')
    result=strict_json(command.stdout,'INVALID_DECODER_OUTPUT')
    require(result.get('verdict')=='PASS' and result.get('readOnly') is True and result.get('destination')==destination
        and result.get('expected')==expected and result.get('actualEntries')==expected,'DECODER_BINDING')
    decoded=result.get('entries');require(isinstance(decoded,list) and len(decoded)==expected,'DECODER_BINDING')
    by_name={r['relative_path']:r for r in rows}
    require(len({r['name'] for r in decoded})==expected,'DECODER_BINDING')
    for item in decoded:
        require(item['name'] in by_name and item.get('decoded') is True
            and item.get('sha256')==by_name[item['name']]['sha256'],'DECODER_CONTENT_MISMATCH')
    if after_decode is not None:after_decode()
    require(inventory(root,destination)==rows,'DOWNLOAD_CHANGED_AFTER_DECODE')
    extensions=dict(Counter(Path(r['relative_path']).suffix.lower() for r in rows))
    verification=dict(observed_at=utc_now(),outcome='PASS',regular_files=expected,image_files=expected,subdirectories=[],
        total_bytes=sum(r['size'] for r in rows),extensions=extensions,metadata_files=[],zero_byte_files=[],
        partial_temp_files=[],unrecognized_files=[],other_entries=[],stable_samples=consecutive,inventory=rows,
        evidence='actual full RGB decode; stable interval/count; exact post-decode inventory')
    return verification,dict(samples=samples,decoder=result,decoder_stdout_sha256=sha(command.stdout),
        decoder_stderr_sha256=sha(command.stderr),decoder_sha256=decoder_sha,elapsed_seconds=clock()-start)
