(() => {'use strict';
document.querySelectorAll('[data-pearp]').forEach(async (root,index) => {
 const $=s=>root.querySelector(s), base=root.dataset.source.replace(/\/$/,''),status=$('[data-status]');
 const load=async path=>{const response=await fetch(base+'/'+path,{cache:'no-cache'});if(!response.ok)throw Error('Données indisponibles (HTTP '+response.status+').');return response.json();};
 const add=(select,value,label)=>{const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);};
 const number=(v,unit)=>Number.isFinite(v)?new Intl.NumberFormat('fr-FR',{maximumFractionDigits:unit==='km/h'?0:1}).format(unit==='km/h'?Math.ceil(v/5)*5:v)+' '+unit:'—';
 try {
  const manifest=await load('index.json');
  if(manifest.members!==35||manifest.status!=='ok')throw Error('Publication PEARP incomplète.');
  status.textContent='Run '+new Date(manifest.run).toLocaleString('fr-FR',{timeZone:'Europe/Paris'})+' · 35 membres · '+manifest.commune_count+' communes';
  Object.entries(manifest.products).forEach(([key,spec])=>add($('[data-product]'),key,spec.label));
  manifest.steps.forEach(h=>add($('[data-step]'),h,'H+'+h));
  const refresh=()=>{const product=$('[data-product]').value,stat=$('[data-stat]').value,region=$('[data-region]').value,step=$('[data-step]').value;
   const img=$('[data-map]');img.hidden=false;img.src=base+'/maps/'+region+'-'+product+'-'+stat+'-'+step+'.svg';img.alt=manifest.products[product].label+' · '+$('[data-stat]').selectedOptions[0].textContent+' · H+'+step;
   img.onerror=()=>{img.hidden=true;$('[data-period]').textContent='Carte indisponible pour cette sélection.';};
   $('[data-period]').textContent='Validité : '+new Date(Date.parse(manifest.run)+Number(step)*3600000).toLocaleString('fr-FR',{timeZone:'Europe/Paris'});};
  ['region','product','stat','step'].forEach(key=>$('[data-'+key+']').addEventListener('change',refresh));
  $('[data-zoom]').addEventListener('input',event=>$('[data-map]').style.width=(Number(event.target.value)*100)+'%');refresh();
  const cities=await load('communes.json'), list=$('datalist');list.id='pearp-cities-'+index;$('[data-city]').setAttribute('list',list.id);
  const search=()=>{list.replaceChildren();const query=$('[data-city]').value.toLocaleLowerCase('fr');if(query.length<2)return;cities.filter(c=>(c[1]+' '+c[0]).toLocaleLowerCase('fr').includes(query)).slice(0,40).forEach(c=>add(list,c[1]+' ('+c[0]+')',c[1]+' ('+c[0]+')'));};
  $('[data-city]').addEventListener('input',search);
  $('[data-show]').addEventListener('click',async()=>{try{
   const query=$('[data-city]').value,c=cities.find(c=>query===c[0]||query===c[1]+' ('+c[0]+')');if(!c)throw Error('Choisissez une commune dans la liste.');
   $('[data-city-status]').textContent='Chargement…';const dep=await load('departements/'+c[2]+'.json');const commune=dep.communes.find(row=>row[0]===c[0]);if(!commune)throw Error('Commune absente de la publication.');
   $('[data-head]').replaceChildren();$('[data-body]').replaceChildren();const hr=document.createElement('tr');['Validité',...Object.values(manifest.products).map(p=>p.label)].forEach(label=>{const th=document.createElement('th');th.textContent=label;hr.append(th);});$('[data-head]').append(hr);
   dep.forecast.forEach(([date,rows])=>{const tr=document.createElement('tr'),td=document.createElement('td');td.textContent=new Date(date).toLocaleString('fr-FR',{timeZone:'Europe/Paris'});tr.append(td);Object.values(manifest.products).forEach(p=>{const cell=document.createElement('td');cell.textContent=number(rows[commune[6]][p.column],p.unit);tr.append(cell);});$('[data-body]').append(tr);});
   $('[data-city-status]').textContent=c[1]+' · maille la plus proche · moyenne des 35 membres';
  }catch(error){$('[data-city-status]').textContent=error.message;}});
 }catch(error){status.textContent=error.message+' Aucune valeur fictive affichée.';}
});})();
