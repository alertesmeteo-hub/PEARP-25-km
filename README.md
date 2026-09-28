# PEARP-25-km

Extension WordPress : `[pearp_meteo]`.

## Version 1.1.1

Le tableau communal est placé en haut du module. Le bouton « Me géolocaliser »
demande l'autorisation du navigateur sur HTTPS puis recherche localement la
commune la plus proche dans le catalogue embarqué. Aucun envoi des coordonnées
au module ni géocodage tiers. Une position à plus de 50 km du catalogue est
refusée avec maintien de la recherche manuelle. Tests interface : `node tests/test_module.cjs`.

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
- Précipitations totales depuis le run : quatre composantes (pluie et neige
  stratiformes/convectives), en mm d'équivalent eau. Pas un taux horaire.
- Rafales à 10 m : norme U/V sur les trois heures précédant l'échéance,
  convertie en km/h AVANT les statistiques d'ensemble. Pas un maximum depuis
  le run. H+0 indisponible. Conventions vérifiées : `config/interval-fields.md`.
- 384 cartes SVG : 7 paramètres, 4 statistiques, 2 domaines et 7 échéances,
  sauf les rafales à H+0. Marges blanches réduites.

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
