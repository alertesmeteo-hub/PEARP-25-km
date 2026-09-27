"""Bounded public GRIB2 range probe; downloads no complete global fields."""
import json
import argparse
import struct
import urllib.request

def part(url, start, length):
    req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{start+length-1}'})
    with urllib.request.urlopen(req,timeout=30) as response:
        if response.status!=206:
            raise RuntimeError('Server does not honor byte ranges; download stopped')
        data=response.read(length+1)
    if len(data)!=length:
        raise RuntimeError('Unexpected partial response size')
    return data

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--decode-first',type=int,default=0,choices=range(13))
    args=parser.parse_args()
    with urllib.request.urlopen('https://www.data.gouv.fr/api/1/datasets/pe-arpege-glob025/',timeout=30) as response:
        catalog=json.load(response)
    resource=catalog['resources'][0]
    url=resource['url']
    if not url.startswith('https://meteofrance-pe.s3.rbx.io.cloud.ovh.net/'):
        raise RuntimeError('Unexpected source host')
    offset=0
    report=[]
    downloaded=0
    for _ in range(12):
        header=part(url,offset,16)
        if header[:4]!=b'GRIB' or header[7]!=2:
            raise RuntimeError('Invalid GRIB2 boundary')
        length=struct.unpack('>Q',header[8:16])[0]
        if length<20 or offset+length>resource['filesize']:
            raise RuntimeError('Invalid GRIB2 length')
        if part(url,offset+length-4,4)!=b'7777':
            raise RuntimeError('Invalid GRIB2 end marker')
        downloaded+=20
        entry={'offset':offset,'length':length}
        if len(report)<args.decode_first:
            if length>5_000_000:
                raise RuntimeError('Probe field exceeds 5 MB budget')
            from eccodes import codes_new_from_message,codes_get,codes_release,codes_get_values
            import numpy as np
            message=part(url,offset,length)
            downloaded+=length
            handle=codes_new_from_message(message)
            try:
                for name in ('shortName','name','units','typeOfLevel','level','dataDate','dataTime',
                             'stepRange','perturbationNumber','numberOfForecastsInEnsemble',
                             'Ni','Nj','iDirectionIncrementInDegrees','jDirectionIncrementInDegrees'):
                    try:entry[name]=codes_get(handle,name)
                    except Exception:entry[name]=None
                values=codes_get_values(handle)
                entry['decoded_values']=len(values)
                entry['finite_values']=int(np.isfinite(values).sum())
            finally:codes_release(handle)
        report.append(entry)
        offset+=length
    print(json.dumps({'resource':resource['title'],'file_bytes':resource['filesize'],
        'validated_messages':len(report),'downloaded_bytes':downloaded,
        'scanned_bytes':offset,'messages':report},indent=2))

if __name__=='__main__':main()
