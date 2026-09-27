"""Strict ensemble statistics: no probabilities from incomplete ensembles."""
import numpy as np

def statistics(members):
    if set(members)!=set(range(35)):
        raise ValueError('Les 35 membres 000 à 034 sont obligatoires')
    values=np.stack([members[i] for i in range(35)])
    if not np.isfinite(values).all():raise ValueError('Ensemble incomplet ou valeurs manquantes')
    return {'mean':values.mean(axis=0),'p10':np.quantile(values,.1,axis=0),
            'median':np.median(values,axis=0),'p90':np.quantile(values,.9,axis=0)}

def probability(members,threshold):
    statistics(members)
    return (np.stack([members[i] for i in range(35)])>=threshold).mean(axis=0)*100
