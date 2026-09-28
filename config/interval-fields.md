# Conventions des champs PEARP cumulés

Vérifiées le 28 septembre 2026 sur PEARP GLOB025, run 00 UTC, H+24, membre 000.

Sources primaires :
- https://www.data.gouv.fr/datasets/definition-des-gribs-de-meteo-france
- https://static.data.gouv.fr/resources/definition-des-gribs-de-meteo-france/20260130-133354/eccodes-definition-path.tar.gz
- https://donneespubliques.meteofrance.fr/client/document/description_parametres_modeles_181.pdf

Dans grib2/localConcepts/lfpw/faFieldName.def, les paramètres 0/1/76 et 0/1/77
sont les flux de pluie convective et grande échelle intégrés depuis le run.
Les valeurs du template 4.11, processus statistique 1 (accumulation), de H+0
à H+n sont déjà intégrées. Le libellé générique ecCodes « kg m**-2 s**-1 »
est celui du paramètre de taux avant intégration : ne pas remultiplier par
la durée. Les composantes neige 0/1/55 et 0/1/56 sont en équivalent eau.
La précipitation totale est leur somme, en kg/m² = mm d'équivalent eau.
Le produit est explicitement « précipitations totales », pas pluie liquide seule.
À H+0 le cumul depuis le départ vaut zéro par définition.

Les paramètres 0/2/23 et 0/2/24 sont les composantes U/V de rafale à 10 m.
La documentation Météo-France définit FF_RAF = sqrt(U_RAF²+V_RAF²).
On sélectionne uniquement les paires à processus statistique 2 (maximum)
portant sur les trois heures précédant l'échéance. Le fichier H+24 contient
aussi des champs sur une heure, explicitement exclus de cette sélection.
Les deux composantes ont la même période et le même membre. Conversion en
km/h par multiplication par 3,6. H+0 n'a pas de rafale sur trois heures : null,
pas de carte ni de zéro artificiel. Ce n'est pas le maximum depuis le run.

Les statistiques d'ensemble sont calculées APRÈS la somme des précipitations
ou le module de la rafale, indépendamment pour chacun des 35 membres.
