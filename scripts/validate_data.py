import json
from pathlib import Path
root=Path('build/data')
manifest=json.loads((root/'index.json').read_text(encoding='utf-8'))
assert manifest['members']==35 and manifest['commune_count']>=34000
assert manifest['steps']==list(range(103))
assert manifest['map_steps']==[0,24,48,72,84,96,102]
assert len(list((root/'maps').glob('*.svg')))==manifest['maps']
for path in (root/'maps').glob('*.svg'):
    assert '<image' not in path.read_text(encoding='utf-8'),'Image bitmap dans une carte vectorielle'
departments=list((root/'departements').glob('*.json'))
assert len(departments)==96
count=0
for path in departments:
    data=json.loads(path.read_text(encoding='utf-8'));count+=len(data['communes']);assert data['schema_version']==5
    assert len(data['forecast'])==len(manifest['steps'])
    assert set(data['forecast_statistics'])=={'median','p10','p90'}
    assert all(len(items)==len(manifest['steps']) for items in data['forecast_statistics'].values())
    for city in data['communes']:assert 0<=city[6]<len(data['points'])
    for step,(date,rows) in zip(manifest['steps'],data['forecast']):
        assert len(rows)==len(data['points'])
        # Au-delà de H+48, Météo-France ne publie entre deux échéances tri-horaires que le vent 10 m et la
        # pression : les autres produits y sont absents pour tous les points (None), jamais partiellement.
        reduced=step>48 and step%3!=0
        for row in rows:
            assert len(row)==len(data['columns'])==7
            for product_name,product in manifest['products'].items():
                value=row[product['column']]
                if product_name=='rafales' and step==0:assert value is None
                elif product_name in ('vent','pressure'):assert isinstance(value,(int,float))
                elif reduced:assert value is None,f'{product_name} inattendu à H+{step}'
                else:assert isinstance(value,(int,float)),f'{product_name} manquant à H+{step}'
assert count==manifest['commune_count']
print(f'Publication validée : {count} communes, 96 départements, {manifest["maps"]} cartes vectorielles.')
