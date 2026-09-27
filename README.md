# PEARP-25-km

Extension WordPress : `[pearp_meteo]`.

## Version initiale 1.0.0

Les données sont issues des fichiers GRIB2 publics officiels Météo-France :
https://www.data.gouv.fr/datasets/pe-arpege-glob025

Le traitement indexe les messages par requêtes HTTP Range, puis télécharge les
champs utiles. Il vérifie le run, l'échéance, la grille 0,25°, les unités et la
présence des 35 membres avant de calculer les statistiques. Il ne dépend pas de
l'API WCS limitée ni du secret configuré pour les tests d'accès.

- Cartes SVG France et Europe : température à 2 m, vent à 10 m, humidité à 2 m,
  pression mer et nébulosité totale.
- Moyenne, médiane, percentiles 10 et 90 calculés sur les 35 membres.
- Échéances H+0, 24, 48, 72, 84, 96 et 102 ; pas d'interpolation horaire.
- Tableaux communaux métropole et Corse : moyenne d'ensemble, format
  départemental v3 à 33 colonnes, colonnes non produites laissées à null.
- Vent : moyenne des vitesses scalaires de chaque membre, pas norme du vent
  vectoriel moyen ; affichage arrondi au palier supérieur de 5 km/h.
- Précipitations et rafales non incluses dans cette version : leurs conventions
  GRIB nécessitent une validation supplémentaire.

Les statistiques ne sont ni un scénario individuel ni des observations.
Le percentile n'est pas une garantie de réalisation. « 25 km » est un nom de
module ; la grille diffusée est de 0,25° (distance zonale variable avec latitude).

## Production et installation

Le workflow `build-pearp.yml` produit et valide toutes les cartes avant de publier
sur `data`. Il tourne sur déclenchement manuel et à 05:40, 11:40, 17:40, 23:40 UTC.
Une erreur conserve la dernière publication. Le workflow de test WCS est distinct.
Le dépôt doit être public pour que WordPress lise la branche data sans secret.

Importer le ZIP de l'extension (dossier wordpress/pearp-25-km) dans WordPress,
activer, puis placer `[pearp_meteo]` dans la page. Aucune clé n'est dans le ZIP.

Tests : `python -m unittest discover -s tests`.
Source : Météo-France, Licence Ouverte Etalab. Contours : Natural Earth, domaine public.
Module WordPress PEARP : prevision ensemble Meteo-France sur grille 0.25 degre
