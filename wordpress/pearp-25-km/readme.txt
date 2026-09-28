=== PEARP 25 km — Alertes Météo ===
Stable tag: 1.1.2
Requires PHP: 7.4
License: GPLv2 or later

Installation : importer le ZIP dans Extensions > Ajouter, activer, puis utiliser [pearp_meteo].

1.1.2 : tableau communal en haut, recherche par nom ou code INSEE et bouton Me géolocaliser.
Géolocalisation à la demande sur HTTPS, avec autorisation du navigateur. Coordonnées traitées localement, sans transmission au module météo. Zone : métropole et Corse ; refus au-delà de 50 km de la commune la plus proche. Aucun service de géocodage externe.

Paramètres : précipitations totales, rafales sur 3 h, température à 2 m, vent à 10 m, humidité relative, pression mer, nébulosité totale.
Cartes France/Europe : moyenne, médiane, percentiles 10 et 90 sur les 35 membres.
Tableaux des communes de France métropolitaine et Corse : moyenne d'ensemble.
Échéances H+0, 24, 48, 72, 84, 96, 102. Aucune interpolation horaire.
Vent affiché au palier supérieur de 5 km/h. Champs sources non arrondis avant les statistiques.
Précipitations cumulées depuis le run, pluie et neige en équivalent eau (mm).
Rafales maximales sur les 3 heures précédant l'échéance, pas depuis le run.
Pas de rafales à H+0 : valeur absente et carte non proposée.
Les statistiques sont calculées après combinaison des composantes, membre par membre.
Les cartes SVG restent vectorielles au zoom. La grille diffusée est de 0,25°.
Données Météo-France sous Licence Ouverte Etalab ; contours Natural Earth, domaine public.
Aucun secret requis ou embarqué dans WordPress. Les fichiers publics sont traités par GitHub Actions.
