<?php
/**
 * Plugin Name: Alertes Météo — PEARP 25 km
 * Description: Cartes et tableaux de la prévision d'ensemble PEARP, grille 0,25°.
 * Version: 1.1.0
 * Author: Alertes Météo
 * License: GPL-2.0-or-later
 */
if (!defined('ABSPATH')) { exit; }
add_shortcode('pearp_meteo', function () {
    wp_enqueue_style('pearp-meteo', plugins_url('assets/module.css', __FILE__), array(), '1.1.0');
    wp_enqueue_script('pearp-meteo', plugins_url('assets/module.js', __FILE__), array(), '1.1.0', true);
    $source = apply_filters('pearp_meteo_data_url', 'https://raw.githubusercontent.com/alertesmeteo-hub/PEARP-25-km/data');
    ob_start(); ?>
    <section class="pearp" data-pearp data-source="<?php echo esc_url($source); ?>">
      <h2>PEARP · grille 0,25°</h2>
      <p>Prévision d’ensemble Météo-France · 35 membres. Les percentiles décrivent la dispersion des scénarios, pas une garantie d’évolution.</p>
      <p data-status role="status">Chargement des données…</p>
      <div class="pearp-controls">
        <label>Domaine <select data-region><option value="france">France</option><option value="europe">Europe</option></select></label>
        <label>Carte <select data-product></select></label>
        <label>Statistique <select data-stat><option value="mean">Moyenne des 35 membres</option><option value="p10">Percentile 10</option><option value="median">Médiane</option><option value="p90">Percentile 90</option></select></label>
        <label>Échéance <select data-step></select></label>
        <label>Zoom <input data-zoom type="range" min="1" max="4" value="1" step="0.25"></label>
      </div>
      <p data-period></p>
      <div class="pearp-map"><img data-map alt="Carte PEARP" hidden></div>
      <h3>Tableau communal · moyenne des 35 membres</h3>
      <label>Commune <input data-city list="pearp-cities" placeholder="Nom ou code INSEE" autocomplete="off"></label>
      <datalist id="pearp-cities"></datalist><button type="button" data-show>Afficher</button>
      <p data-city-status role="status"></p>
      <div class="pearp-table"><table><thead data-head></thead><tbody data-body></tbody></table></div>
      <p class="pearp-note">Précipitations totales depuis le run : pluie et neige en équivalent eau (mm). Rafales maximales sur les 3 heures précédant chaque échéance, pas depuis le run ; indisponibles à H+0. Échéances H+0, 24, 48, 72, 84, 96 et 102 : aucune interpolation horaire. La moyenne des rafales des 35 membres n’est pas leur maximum absolu.</p>
      <footer><span class="pearp-logo">www.alertes-meteo.com</span><p>Source : Météo-France · Licence Ouverte Etalab. Module PEARP v1.1.0.</p></footer>
    </section>
    <?php return ob_get_clean();
});
