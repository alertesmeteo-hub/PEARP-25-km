"""Selective GRIB2 inventory from the official public PEARP bucket."""
import argparse
import json
import struct
import time
from pathlib import Path
import requests
from urllib3.exceptions import ProtocolError
import xml.etree.ElementTree as ET
import re

CATALOG='https://www.data.gouv.fr/api/1/datasets/pe-arpege-glob025/'
HOST='https://meteofrance-pe.s3.rbx.io.cloud.ovh.net/'

def complete_catalog(resources):
    """Read bounded official bucket listings for runs already in the catalog.

    data.gouv replaces resources individually, temporarily mixing two runs.
    Immutable files for the previous run remain in the public bucket.
    """
    runs=sorted({m[1] for resource in resources if (m:=re.search(r'/(\d{12})/',resource['url']))},reverse=True)[:2]
    session=requests.Session();result=[]
    ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    for run in runs:
        prefix=f'prod/data/arpege/glob025/{run}/'
        response=session.get(HOST,params={'prefix':prefix,'max-keys':150},timeout=30)
        response.raise_for_status();root=ET.fromstring(response.content)
        if root.findtext('s:IsTruncated',namespaces=ns)!='false':raise ValueError('Bucket listing truncated')
        for item in root.findall('s:Contents',ns):
            key=item.findtext('s:Key',namespaces=ns)
            if not key.startswith(prefix) or not key.endswith('.grib'):continue
            result.append({'title':key.rsplit('/',1)[1],'url':HOST+key,'filesize':int(item.findtext('s:Size',namespaces=ns))})
    return result

def read_range(session,url,start,count,total):
    if not url.startswith(HOST):raise ValueError('Untrusted GRIB host')
    end=min(start+count,total)-1
    for attempt in range(4):
        try:
            with session.get(url,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(15,60)) as r:
                if r.status_code in (429,500,502,503,504):
                    if attempt==3:raise ValueError(f'Public source unavailable: HTTP {r.status_code}')
                    time.sleep(15*(attempt+1));continue
                if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{total}':
                    raise ValueError(f'Invalid range response: HTTP {r.status_code}')
                data=r.raw.read(end-start+2)
            if len(data)!=end-start+1:raise ProtocolError('Truncated range')
            return data
        except (requests.RequestException,OSError,ProtocolError) as error:
            if attempt==3:raise ValueError('Public source unavailable after four attempts') from error
            print(f'Connexion source interrompue, reprise dans {15*(attempt+1)} s.',flush=True)
            time.sleep(15*(attempt+1))
    raise ValueError('Public source unavailable')

def metadata(header):
    if len(header)<16 or header[:4]!=b'GRIB' or header[7]!=2:raise ValueError('Invalid GRIB2')
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
            if template==11:
                if len(s)<61 or s[44]!=1:raise ValueError('Unsupported statistical time ranges')
                result.update(statistical_process=s[49],range_unit=s[51],range_length=int.from_bytes(s[52:56],'big'))
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
