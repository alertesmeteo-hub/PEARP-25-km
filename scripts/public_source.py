"""Selective GRIB2 inventory from the official public PEARP bucket."""
import argparse
import json
import struct
import time
from pathlib import Path
import requests

CATALOG='https://www.data.gouv.fr/api/1/datasets/pe-arpege-glob025/'
HOST='https://meteofrance-pe.s3.rbx.io.cloud.ovh.net/'

def read_range(session,url,start,count,total):
    if not url.startswith(HOST):raise ValueError('Untrusted GRIB host')
    end=min(start+count,total)-1
    for attempt in range(3):
        with session.get(url,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(15,60)) as r:
            if r.status_code in (429,500,502,503,504) and attempt<2:
                time.sleep(5*(attempt+1));continue
            if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{total}':
                raise ValueError(f'Invalid range response: HTTP {r.status_code}')
            data=r.raw.read(end-start+2)
        if len(data)!=end-start+1:raise ValueError('Truncated range')
        return data
    raise ValueError('Public source unavailable')

def metadata(header):
    if header[:4]!=b'GRIB' or header[7]!=2:raise ValueError('Invalid GRIB2')
    result={'length':int.from_bytes(header[8:16],'big'),'discipline':header[6]}
    pos=16
    while pos+5<=len(header):
        size=int.from_bytes(header[pos:pos+4],'big');section=header[pos+4]
        if size<5:raise ValueError('Invalid section')
        if pos+size>len(header):break
        s=header[pos:pos+size]
        if section==1:
            result['run']=f'{int.from_bytes(s[12:14],"big"):04d}{s[14]:02d}{s[15]:02d}{s[16]:02d}'
        if section==4:
            template=int.from_bytes(s[7:9],'big')
            result.update(template=template,category=s[9],parameter=s[10],
                time_unit=s[17],lead=int.from_bytes(s[18:22],'big'),
                level_type=s[22],level_scale=s[23],level_value=int.from_bytes(s[24:28],'big'))
            if template in (1,11):result.update(member=s[35],ensemble_size=s[36])
            return result
        pos+=size
    raise ValueError('Product metadata not found in prefix')

def inventory(resource,limit=10000):
    session=requests.Session();offset=0;rows=[];total=resource['filesize']
    while offset<total and len(rows)<limit:
        prefix=read_range(session,resource['url'],offset,1024,total)
        entry=metadata(prefix);entry['offset']=offset
        if entry['length']<20 or offset+entry['length']>total:raise ValueError('Invalid message length')
        rows.append(entry);offset+=entry['length']
        if len(rows)%100==0:print(f'Inventaire : {len(rows)} messages, {offset/total:.0%} du fichier indexé',flush=True)
    return {'resource':resource,'complete':offset==total,'messages':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=100)
    p.add_argument('--step',type=int,default=0)
    p.add_argument('--output',default='build/inventory.json');args=p.parse_args()
    session=requests.Session();r=session.get(CATALOG,timeout=30);r.raise_for_status()
    resource=next(x for x in r.json()['resources'] if x['title'].endswith(f'_{args.step:02d}:00.grib'))
    result=inventory(resource,args.limit)
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result),encoding='utf-8')
    print(json.dumps({'complete':result['complete'],'messages':len(result['messages']),
        'members':sorted(set(x.get('member',-1) for x in result['messages']))}))
