"""Build verified instantaneous PEARP ensemble products from public GRIBs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import re
import requests
import numpy as np
from eccodes import codes_new_from_message,codes_get,codes_get_values,codes_release
from public_source import CATALOG,inventory,read_range,complete_catalog
from ensemble import statistics
from render_maps import PRODUCTS,REGIONS,render
from interval_fields import INTERVAL_SIGNATURES,matching_interval,validate_interval,precipitation_total,gust_speed,gust_duration

STEPS=list(range(103))
MAP_STEPS=[0,24,48,72,84,96,102]
SIGNATURES={
 'temperature':(0,0,103,2),'u':(2,2,103,10),'v':(2,3,103,10),
 'nuages':(6,1,1,0),'humidity':(1,1,103,2),'pressure':(3,1,101,0),
}
LON=np.arange(-26,46.01,.25);LAT=np.arange(29,73.01,.25)
IX=np.rint((LON%360)/.25).astype(int);IY=np.rint((90-LAT)/.25).astype(int)

def select_resources(resources):
    runs={}
    for resource in resources:
        match=re.search(r'_(\d{12})_(\d+):00\.grib$',resource['title'])
        if match:runs.setdefault(match[1][:10],{})[int(match[2])]=resource
    complete=[run for run,items in runs.items() if all(h in items for h in STEPS)]
    if not complete:raise ValueError('Aucun run public cohérent sur toutes les échéances requises')
    run=max(complete)
    return run,{h:runs[run][h] for h in STEPS}

def extract_step(run,step,resource):
    cache=Path('build/cache')/f'{run}-{step}-v3.json';cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.exists():
        index=json.loads(cache.read_text())
        if index['resource']['url']!=resource['url'] or index['resource']['filesize']!=resource['filesize']:
            raise ValueError('Source modifiée depuis indexation')
    else:
        index=inventory(resource);cache.write_text(json.dumps(index))
    if not index['complete']:raise ValueError('Inventaire incomplet')
    chosen=[]
    gust_window=gust_duration(index['messages'],step) if step else None
    signatures={**SIGNATURES,**(INTERVAL_SIGNATURES if step else {})}
    for row in index['messages']:
        if row['discipline']!=0 or row['level_scale']!=0:continue
        for field,signature in signatures.items():
            if tuple(row[k] for k in ('category','parameter','level_type','level_value'))==signature:
                if field in INTERVAL_SIGNATURES:
                    if not matching_interval(row,field,step,gust_window):continue
                elif row['template']!=1 or row['lead']!=step:continue
                if row['run']!=run or row['time_unit']!=1 or row.get('ensemble_size')!=35:
                    raise ValueError('Métadonnées incohérentes')
                chosen.append((field,row))
    for field in list(signatures):
        selected=[r['member'] for f,r in chosen if f==field]
        # Au-delà de H+48 Météo-France publie des fichiers réduits (vent 10 m et pression seulement) :
        # un champ totalement absent est ignoré, un champ partiel reste une erreur.
        if not selected and step>48:
            signatures.pop(field);continue
        if sorted(selected)!=list(range(35)):raise ValueError(f'{field}: 35 membres uniques requis à H+{step}')
    members={field:{} for field in signatures}
    session=requests.Session()
    for field,row in chosen:
        if row['length']>5_000_000:raise ValueError('Champ anormalement volumineux')
        data=read_range(session,resource['url'],row['offset'],row['length'],resource['filesize'])
        if data[-4:]!=b'7777':raise ValueError('GRIB tronqué')
        handle=codes_new_from_message(data)
        try:
            expected={'Ni':1440,'Nj':721,'latitudeOfFirstGridPointInDegrees':90,
                'longitudeOfFirstGridPointInDegrees':0,'iDirectionIncrementInDegrees':.25,
                'jDirectionIncrementInDegrees':.25,'jScansPositively':0,'iScansNegatively':0,
                'jPointsAreConsecutive':0,'alternativeRowScanning':0,
                'perturbationNumber':row['member'],'endStep':step}
            if field in INTERVAL_SIGNATURES:validate_interval(handle,codes_get,field,step,gust_window)
            else:expected['startStep']=step
            for key,value in expected.items():
                if codes_get(handle,key)!=value:raise ValueError(f'Grille ou échéance invalide: {key}')
            if codes_get(handle,'numberOfMissing')!=0:raise ValueError('Champ avec points manquants')
            values=codes_get_values(handle).reshape(721,1440)[np.ix_(IY,IX)]
            units=codes_get(handle,'units')
            if field=='temperature':
                if units!='K':raise ValueError('Unité température inattendue')
                values=values-273.15
            elif field in ('u','v'):
                if units not in ('m s**-1','m s-1'):raise ValueError('Unité vent inattendue')
            elif field=='pressure':
                if units!='Pa':raise ValueError('Unité pression inattendue')
                values=values/100
            elif field in ('nuages','humidity'):
                # WMO GRIB2 0/6/1 and 0/1/1 are percentages. ecCodes may not
                # assign a short name for the Météo-France cloud field.
                if units not in ('%','unknown'):raise ValueError('Unité pourcentage inattendue')
                if values.min()<0 or values.max()>150:raise ValueError('Pourcentage invalide')
            members[field][row['member']]=values.astype(np.float32)
        finally:codes_release(handle)
    if 'u' in members and 'v' in members:
        members['vent']={i:np.hypot(members['u'][i],members['v'][i])*3.6 for i in range(35)}
    if step:
        if all(key in members for key in ('rain_conv','rain_large','snow_conv','snow_large')):
            members['precipitation']={i:precipitation_total([members[key][i] for key in ('rain_conv','rain_large','snow_conv','snow_large')]) for i in range(35)}
        if 'gust_u' in members and 'gust_v' in members:
            members['rafales']={i:gust_speed(members['gust_u'][i],members['gust_v'][i]) for i in range(35)}
    else:members['precipitation']={i:np.zeros_like(members['temperature'][i]) for i in range(35)}
    result={product:statistics(members[product]) for product in PRODUCTS if product in members}
    print(f'H+{step}: {len(result)} produits, 35 membres validés',flush=True)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='build/data');args=parser.parse_args()
    response=requests.get(CATALOG,timeout=30);response.raise_for_status()
    catalog=response.json()['resources']
    try:run,resources=select_resources(catalog)
    except ValueError:
        print('Catalogue en transition : vérification des fichiers dans le stockage officiel.',flush=True)
        run,resources=select_resources(complete_catalog(catalog))
    print('Run sélectionné: '+run,flush=True)
    run_dt=datetime.strptime(run,'%Y%m%d%H').replace(tzinfo=timezone.utc)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures={h:executor.submit(extract_step,run,h,resources[h]) for h in STEPS}
        results={h:futures[h].result() for h in STEPS}
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    for step in MAP_STEPS:
        result=results[step]
        for product,stats in result.items():
            for stat,values in stats.items():
                for region in REGIONS:
                    render(LON,LAT,values,product,stat,region,run_dt,step,output/'maps'/f'{region}-{product}-{stat}-{step}.svg')
    communes=json.loads(Path('config/communes-france.json').read_text(encoding='utf-8'))['communes']
    departments={}
    for c in communes:
        if c[2] in ('2A','2B') or (c[2].isdigit() and 1<=int(c[2])<=95 and c[2]!='20'):
            departments.setdefault(c[2],[]).append(c)
    if len(departments)!=96 or sum(map(len,departments.values()))<34000:raise ValueError('Catalogue France incomplet')
    reference_schema=json.loads(Path('config/reference-schema.json').read_text())
    # le schéma de référence est un dictionnaire (points, communes, values) : seules les colonnes de valeurs PEARP sont conservées
    schema_values=[reference_schema['values'][index] for index in (0,1,3,4,6,7,12)]
    schema={**reference_schema,'values':schema_values}
    (output/'departements').mkdir(exist_ok=True)
    city_list=[]
    for dep,cities in departments.items():
        points=[];rows=[];lookup={}
        for c in cities:
            iy=int(np.argmin(abs(LAT-c[5])));ix=int(np.argmin(abs(LON-c[6])))
            if (iy,ix) not in lookup:
                lookup[iy,ix]=len(points);points.append([int(IY[iy]*1440+IX[ix]),float(LAT[iy]),float(LON[ix]),None])
            rows.append([c[0],c[1],c[3],c[4],c[5],c[6],lookup[iy,ix]])
            city_list.append([c[0],c[1],dep])
        forecasts={}
        for stat in ('mean','median','p10','p90'):
            forecast=[]
            for step in STEPS:
                values=[]
                for iy,ix in lookup:
                    row=[None]*len(schema_values)
                    for product,spec in PRODUCTS.items():
                        if product in results[step]:row[spec['column']]=round(float(results[step][product][stat][iy,ix]),2)
                    values.append(row)
                forecast.append([(run_dt+timedelta(hours=step)).isoformat(),values])
            forecasts[stat]=forecast
        payload={'schema_version':5,'columns':schema,'department':dep,'points':points,'communes':rows,'forecast':forecasts['mean'],'forecast_statistics':{key:value for key,value in forecasts.items() if key!='mean'},'statistic':'mean','members':35}
        (output/'departements'/f'{dep}.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (output/'communes.json').write_text(json.dumps(city_list,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    manifest={'status':'ok','version':'1.3.0','members':35,'run':run_dt.isoformat(),'steps':STEPS,'map_steps':MAP_STEPS,'products':PRODUCTS,'commune_count':len(city_list),
        'generated_at':datetime.now(timezone.utc).isoformat(),'maps':sum(len(results[step]) for step in MAP_STEPS)*4*2,
        'limitations':'Tableau horaire H+0 à H+102, sans interpolation. Cartes aux 7 échéances principales. Précipitations totales depuis le run, pluie et neige en équivalent eau. Rafales maximales sur une heure à H+1 et H+2, puis sur les trois heures précédentes, indisponibles à H+0.'}
    (output/'index.json').write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False),flush=True)

if __name__=='__main__':main()

