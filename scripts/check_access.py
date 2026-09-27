"""Read-only PEARP authentication and metadata probe; never log credentials."""
import os
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

BASE = 'https://public-api.meteofrance.fr/public/pearpege/1.0/wcs/'
key = os.environ.get('METEOFRANCE_PEARP_25_API_KEY', '').strip()
if not key:
    raise SystemExit('Secret METEOFRANCE_PEARP_25_API_KEY absent ou vide.')
out = Path('build/metadata')
out.mkdir(parents=True, exist_ok=True)

def request(member, operation, **params):
    service = f'MF-NWP-GLOBAL-PEARP{member:03d}-025-GLOBE-WCS'
    query = urllib.parse.urlencode(dict(service='WCS', version='2.0.1', **params))
    req = urllib.request.Request(f'{BASE}{service}/{operation}?{query}', headers={'apikey':key})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            content = response.read(12_000_001)
    except urllib.error.HTTPError as error:
        raise SystemExit(f'{operation} membre {member:03d}: HTTP {error.code}. Aucun secret affiché.') from None
    except urllib.error.URLError:
        raise SystemExit('Service Météo-France inaccessible.') from None
    if len(content)>12_000_000:
        raise SystemExit('Métadonnées anormalement volumineuses.')
    root=ET.fromstring(content)
    if root.tag.endswith('ExceptionReport'):
        raise SystemExit(f'Exception WCS dans {operation}; arrêt sans publication.')
    return root,content

for member in (0,1,34):
    root,content=request(member,'GetCapabilities',language='fre')
    ids=[node.text for node in root.iter() if node.tag.endswith('}CoverageId') and node.text]
    if not ids:
        raise SystemExit(f'Catalogue vide membre {member:03d}.')
    (out/f'capabilities-{member:03d}.xml').write_bytes(content)
    print(f'Membre {member:03d}: accès accepté, {len(ids)} couvertures.')
    if member==0:
        candidates=sorted(i for i in ids if i.startswith('TEMPERATURE__SPECIFIC_HEIGHT_LEVEL_ABOVE_GROUND___'))
        if not candidates:
            raise SystemExit('Température près du sol introuvable.')
        selected=candidates[-1]
        _,description=request(member,'DescribeCoverage',coverageid=selected)
        (out/'temperature-description.xml').write_bytes(description)
        print('Métadonnées température validées : '+selected)
print('Test accès PEARP réussi. Ceci ne constitue pas encore une production de cartes.')
