"""Météo-France accumulated precipitation and paired gust components.

References: config/interval-fields.md. Statistics must follow per-member sums
and vector norms, never sum percentiles or take norms of ensemble averages.
"""
import numpy as np

INTERVAL_SIGNATURES={
 'rain_conv':(1,76,1,0),'rain_large':(1,77,1,0),
 'snow_conv':(1,55,1,0),'snow_large':(1,56,1,0),
 'gust_u':(2,23,103,10),'gust_v':(2,24,103,10),
}

def matching_interval(row,field,step):
    if step==0 or row['template']!=11:return False
    if field.startswith('gust_'):
        duration=1 if step<3 else 3
        return (row.get('statistical_process')==2 and row.get('range_unit')==1
                and row.get('range_length')==duration and row['lead']==step-duration)
    return (row.get('statistical_process')==1 and row.get('range_unit')==1
            and row.get('range_length')==step and row['lead']==0)

def validate_interval(handle,get,field,step):
    gust=field.startswith('gust_')
    duration=(1 if step<3 else 3) if gust else step
    expected={'productDefinitionTemplateNumber':11,'typeOfStatisticalProcessing':2 if gust else 1,
        'startStep':step-duration if gust else 0,'endStep':step,'indicatorOfUnitForTimeRange':1,
        'lengthOfTimeRange':duration,'stepType':'max' if gust else 'accum'}
    for key,value in expected.items():
        if get(handle,key)!=value:raise ValueError(f'Intervalle {field} incohérent: {key}')
    units=get(handle,'units')
    allowed=('m s**-1','m s-1') if gust else ('kg m**-2','kg m**-2 s**-1','mm')
    if units not in allowed:raise ValueError(f'Unité {field} inattendue: {units}')

def precipitation_total(components):
    if len(components)!=4:raise ValueError('Quatre composantes de précipitations requises')
    values=np.stack(components)
    if not np.isfinite(values).all() or values.min()<0:raise ValueError('Cumul négatif ou manquant')
    return values.sum(axis=0)

def gust_speed(u,v):
    if not np.isfinite(u).all() or not np.isfinite(v).all():raise ValueError('Rafale manquante')
    return np.hypot(u,v)*3.6
