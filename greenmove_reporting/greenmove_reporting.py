#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Greenmove - Rapport d'Analyse des Déplacements
Génère un rapport complet avec graphiques et statistiques
"""

import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# Seuils par défaut pour l'intensité carbone (g CO₂/km)
# Peuvent être surchargés via config.py
try:
    from config import SEUILS_INTENSITE_CARBONE
    OBJECTIF_RECOMMANDE = SEUILS_INTENSITE_CARBONE.get('objectif_recommande', 15)
    SEUIL_EXCELLENT = SEUILS_INTENSITE_CARBONE.get('excellent', 15)
    SEUIL_BON = SEUILS_INTENSITE_CARBONE.get('bon', 50)
    SEUIL_MOYEN = SEUILS_INTENSITE_CARBONE.get('moyen', 100)
except ImportError:
    # Valeurs par défaut si config.py n'existe pas
    OBJECTIF_RECOMMANDE = 15
    SEUIL_EXCELLENT = 15
    SEUIL_BON = 50
    SEUIL_MOYEN = 100

# Configuration de style pour les graphiques
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

class GreenmoveAnalytics:
    """Classe pour l'analyse des données Greenmove"""
    
    def __init__(self, host, database, user, password, port=5432):
        """Initialise la connexion à la base de données"""
        self.conn_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
        self.df = None
        self.stats_globales = {}
        self.output_format = 'pdf'  # Format par défaut
        
    def set_output_format(self, format='pdf'):
        """Définit le format de sortie : 'pdf' ou 'html'"""
        if format.lower() not in ['pdf', 'html']:
            raise ValueError("Format doit être 'pdf' ou 'html'")
        self.output_format = format.lower()
        print(f"✓ Format de sortie défini : {self.output_format.upper()}")
        
    def connect_and_load_data(self):
        """Charge les données depuis PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.conn_params)
            query = """
                SELECT 
                    utilisateur,
                    "startTime" as start_time,
                    mode_transport,
                    distance,
                    duration_in_minutes,
                    emission_co2
                FROM tripanalyse.usagestat
                ORDER BY "startTime"
            """
            self.df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Conversion des types
            self.df['start_time'] = pd.to_datetime(self.df['start_time'])
            self.df['distance'] = pd.to_numeric(self.df['distance'], errors='coerce')
            self.df['duration_in_minutes'] = pd.to_numeric(self.df['duration_in_minutes'], errors='coerce')
            self.df['emission_co2'] = pd.to_numeric(self.df['emission_co2'], errors='coerce')
            
            print(f"✓ Données chargées : {len(self.df)} trajets")
            return True
        except Exception as e:
            print(f"✗ Erreur de connexion : {e}")
            return False
    
    def calculer_statistiques_globales(self):
        """Calcule les statistiques globales"""
        self.stats_globales = {
            'nombre_utilisateurs': self.df['utilisateur'].nunique(),
            'nombre_trajets': len(self.df),
            'distance_totale': self.df['distance'].sum(),
            'distance_moyenne': self.df['distance'].mean(),
            'duree_totale': self.df['duration_in_minutes'].sum(),
            'duree_moyenne': self.df['duration_in_minutes'].mean(),
            'emission_totale': self.df['emission_co2'].sum(),
            'emission_moyenne': self.df['emission_co2'].mean(),
            'periode_debut': self.df['start_time'].min(),
            'periode_fin': self.df['start_time'].max()
        }
        
        # Statistiques par mode de transport
        self.stats_par_mode = self.df.groupby('mode_transport').agg({
            'utilisateur': 'count',
            'distance': ['sum', 'mean'],
            'duration_in_minutes': ['sum', 'mean'],
            'emission_co2': ['sum', 'mean']
        }).round(2)
        
        return self.stats_globales
    
    def generer_rapport_pdf(self, filename='rapport_greenmove.pdf', format='pdf'):
        """Génère le rapport complet en PDF ou HTML"""
        # Si format HTML, rediriger vers la méthode HTML
        if format == 'html':
            filename = filename.replace('.pdf', '.html')
            return self.generer_rapport_html(filename)
        
        # Sinon, générer le PDF
        with PdfPages(filename) as pdf:
            # Page 1: Vue d'ensemble
            self._page_vue_ensemble(pdf)
            
            # Page 2: Analyse par mode de transport
            self._page_analyse_modes(pdf)
            
            # Page 3: Distribution des distances
            self._page_distribution_distances(pdf)
            
            # Page 4: Analyse temporelle
            self._page_analyse_temporelle(pdf)
            
            # Page 5: Émissions CO2
            self._page_emissions_co2(pdf)
            
            # Page 6: Top utilisateurs
            self._page_top_utilisateurs(pdf)
            
            # Métadonnées du PDF
            d = pdf.infodict()
            d['Title'] = 'Rapport Greenmove - Analyse des Déplacements'
            d['Author'] = 'Greenmove Analytics'
            d['Subject'] = 'Analyse de mobilité'
            d['CreationDate'] = datetime.now()
        
        print(f"✓ Rapport PDF généré : {filename}")
    
    def generer_rapport_html(self, filename='rapport_greenmove_global.html'):
        """Génère le rapport complet en HTML avec graphiques interactifs"""
        import base64
        from io import BytesIO
        
        # Créer le HTML
        html_content = self._generer_html_rapport_global()
        
        # Sauvegarder
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Rapport HTML généré : {filename}")
    
    def _generer_html_rapport_global(self):
        """Génère le contenu HTML pour le rapport global"""
        from io import BytesIO
        import base64
        
        stats = self.stats_globales
        
        # Template HTML de base
        html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Greenmove - Rapport d'Analyse des Déplacements</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        h1 {{
            text-align: center;
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            font-size: 1.2em;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 10px;
            color: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 1em;
            opacity: 0.9;
        }}
        .section {{
            margin: 40px 0;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        .metric-good {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .metric-medium {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .metric-warning {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 GREENMOVE</h1>
        <div class="subtitle">Rapport d'Analyse des Déplacements</div>
        <div class="subtitle" style="font-size: 0.9em;">
            Période: {stats['periode_debut'].strftime('%d/%m/%Y')} - {stats['periode_fin'].strftime('%d/%m/%Y')}
        </div>
        
        <!-- KPIs Principaux -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">👥 Utilisateurs Actifs</div>
                <div class="stat-value">{stats['nombre_utilisateurs']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">🚶 Trajets Totaux</div>
                <div class="stat-value">{stats['nombre_trajets']:,}</div>
            </div>
            <div class="stat-card metric-good">
                <div class="stat-label">🛣️ Distance Totale</div>
                <div class="stat-value">{stats['distance_totale']:,.0f} km</div>
            </div>
            <div class="stat-card metric-warning">
                <div class="stat-label">🌱 Émissions CO₂</div>
                <div class="stat-value">{stats['emission_totale']:.1f} kg</div>
            </div>
        </div>
        
        <!-- Statistiques Détaillées -->
        <div class="section">
            <h2>📊 Statistiques Détaillées</h2>
            <table>
                <tr>
                    <th>Indicateur</th>
                    <th>Valeur</th>
                </tr>
                <tr>
                    <td>Distance moyenne par trajet</td>
                    <td><strong>{stats['distance_moyenne']:.2f} km</strong></td>
                </tr>
                <tr>
                    <td>Durée totale</td>
                    <td><strong>{stats['duree_totale']:,.0f} minutes ({stats['duree_totale']/60:.0f} heures)</strong></td>
                </tr>
                <tr>
                    <td>Durée moyenne par trajet</td>
                    <td><strong>{stats['duree_moyenne']:.1f} minutes</strong></td>
                </tr>
                <tr>
                    <td>Émissions moyennes par trajet</td>
                    <td><strong>{stats['emission_moyenne']*1000:.1f} g CO₂</strong></td>
                </tr>
                <tr>
                    <td>Intensité carbone globale</td>
                    <td><strong>{(stats['emission_totale']*1000)/stats['distance_totale']:.1f} g CO₂/km</strong></td>
                </tr>
            </table>
        </div>
"""
        
        # Ajouter les graphiques
        html += self._generer_graphiques_html()
        
        # Analyse par mode de transport
        html += self._generer_analyse_modes_html()
        
        # Footer
        html += f"""
        <div class="footer">
            <p>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
            <p>Greenmove Analytics - Analyse de Mobilité</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generer_graphiques_html(self):
        """Génère les graphiques en base64 pour HTML"""
        from io import BytesIO
        import base64
        
        html = '<div class="section"><h2>📈 Visualisations</h2>'
        
        # Graphique 1: Répartition modale
        fig, ax = plt.subplots(figsize=(10, 6))
        mode_counts = self.df['mode_transport'].value_counts()
        colors = plt.cm.Set3(range(len(mode_counts)))
        ax.pie(mode_counts.values, labels=mode_counts.index, autopct='%1.1f%%',
              colors=colors, startangle=90)
        ax.set_title('Répartition des Trajets par Mode de Transport', fontsize=14, fontweight='bold')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        html += f'<div class="chart-container"><img src="data:image/png;base64,{image_base64}" /></div>'
        
        # Graphique 2: Distance par mode
        fig, ax = plt.subplots(figsize=(10, 6))
        distance_par_mode = self.df.groupby('mode_transport')['distance'].sum().sort_values(ascending=False)
        distance_par_mode.plot(kind='bar', ax=ax, color='steelblue')
        ax.set_ylabel('Distance (km)', fontsize=12)
        ax.set_title('Distance Totale par Mode de Transport', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        html += f'<div class="chart-container"><img src="data:image/png;base64,{image_base64}" /></div>'
        
        # Graphique 3: Émissions CO2 par mode
        fig, ax = plt.subplots(figsize=(10, 6))
        co2_par_mode = self.df.groupby('mode_transport')['emission_co2'].sum().sort_values(ascending=False)
        co2_par_mode.plot(kind='bar', ax=ax, color='coral')
        ax.set_ylabel('Émissions CO₂ (g)', fontsize=12)
        ax.set_title('Émissions CO₂ Totales par Mode de Transport', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        html += f'<div class="chart-container"><img src="data:image/png;base64,{image_base64}" /></div>'
        
        html += '</div>'
        return html
    
    def _generer_analyse_modes_html(self):
        """Génère l'analyse par mode en HTML"""
        html = '<div class="section"><h2>🚗 Analyse par Mode de Transport</h2>'
        
        mode_stats = self.df.groupby('mode_transport').agg({
            'utilisateur': 'count',
            'distance': ['sum', 'mean'],
            'duration_in_minutes': 'mean',
            'emission_co2': ['sum', 'mean']
        }).round(2)
        
        html += '<table><tr><th>Mode</th><th>Trajets</th><th>Distance Totale</th><th>Distance Moy.</th>'
        html += '<th>Durée Moy.</th><th>CO₂ Total</th><th>CO₂ Moy.</th><th>Intensité</th></tr>'
        
        for mode in mode_stats.index:
            nb = mode_stats.loc[mode, ('utilisateur', 'count')]
            dist_tot = mode_stats.loc[mode, ('distance', 'sum')]
            dist_moy = mode_stats.loc[mode, ('distance', 'mean')]
            duree = mode_stats.loc[mode, ('duration_in_minutes', 'mean')]
            co2_tot = mode_stats.loc[mode, ('emission_co2', 'sum')]  # en kg
            co2_moy = mode_stats.loc[mode, ('emission_co2', 'mean')]  # en kg
            intensite = (co2_tot * 1000) / dist_tot if dist_tot > 0 else 0  # g/km
            
            html += f'<tr><td><strong>{mode}</strong></td>'
            html += f'<td>{nb:.0f}</td>'
            html += f'<td>{dist_tot:.1f} km</td>'
            html += f'<td>{dist_moy:.2f} km</td>'
            html += f'<td>{duree:.1f} min</td>'
            html += f'<td>{co2_tot:.2f} kg</td>'
            html += f'<td>{co2_moy*1000:.1f} g</td>'
            html += f'<td>{intensite:.1f} g/km</td></tr>'
        
        html += '</table></div>'
        return html
    
    def _page_vue_ensemble(self, pdf):
        """Page 1: Vue d'ensemble"""
        fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
        fig.suptitle('GREENMOVE - Rapport d\'Analyse des Déplacements', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        # Informations générales
        ax1 = plt.subplot(3, 2, 1)
        ax1.axis('off')
        stats = self.stats_globales
        texte_stats = f"""
STATISTIQUES GÉNÉRALES

Période d'analyse :
  Du {stats['periode_debut'].strftime('%d/%m/%Y')}
  Au {stats['periode_fin'].strftime('%d/%m/%Y')}

Utilisateurs actifs : {stats['nombre_utilisateurs']:,}
Nombre de trajets : {stats['nombre_trajets']:,}

Distance totale : {stats['distance_totale']:,.1f} km
Distance moyenne : {stats['distance_moyenne']:.2f} km

Durée totale : {stats['duree_totale']:,.0f} min ({stats['duree_totale']/60:.0f} heures)
Durée moyenne : {stats['duree_moyenne']:.1f} min

Émissions CO₂ totales : {stats['emission_totale']:.2f} kg ({stats['emission_totale']*1000:,.0f} g)
Émissions moyennes : {stats['emission_moyenne']*1000:.1f} g/trajet
        """
        ax1.text(0.05, 0.95, texte_stats, transform=ax1.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Répartition des modes de transport (camembert)
        ax2 = plt.subplot(3, 2, 2)
        mode_counts = self.df['mode_transport'].value_counts()
        colors = plt.cm.Set3(range(len(mode_counts)))
        ax2.pie(mode_counts.values, labels=mode_counts.index, autopct='%1.1f%%',
                colors=colors, startangle=90)
        ax2.set_title('Répartition des Trajets par Mode de Transport', fontweight='bold')
        
        # Nombre de trajets par mode (barres horizontales)
        ax3 = plt.subplot(3, 2, 3)
        mode_counts.plot(kind='barh', ax=ax3, color='steelblue')
        ax3.set_xlabel('Nombre de trajets')
        ax3.set_title('Nombre de Trajets par Mode de Transport', fontweight='bold')
        ax3.grid(axis='x', alpha=0.3)
        
        # Distance totale par mode
        ax4 = plt.subplot(3, 2, 4)
        distance_par_mode = self.df.groupby('mode_transport')['distance'].sum().sort_values(ascending=False)
        distance_par_mode.plot(kind='bar', ax=ax4, color='coral')
        ax4.set_ylabel('Distance (km)')
        ax4.set_title('Distance Totale par Mode de Transport', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(axis='y', alpha=0.3)
        
        # Émissions CO2 par mode
        ax5 = plt.subplot(3, 2, 5)
        co2_par_mode = self.df.groupby('mode_transport')['emission_co2'].sum().sort_values(ascending=False)
        co2_par_mode.plot(kind='bar', ax=ax5, color='lightcoral')
        ax5.set_ylabel('Émissions CO₂ (g)')
        ax5.set_title('Émissions CO₂ Totales par Mode de Transport', fontweight='bold')
        ax5.tick_params(axis='x', rotation=45)
        ax5.grid(axis='y', alpha=0.3)
        
        # Durée moyenne par mode
        ax6 = plt.subplot(3, 2, 6)
        duree_par_mode = self.df.groupby('mode_transport')['duration_in_minutes'].mean().sort_values(ascending=False)
        duree_par_mode.plot(kind='barh', ax=ax6, color='lightgreen')
        ax6.set_xlabel('Durée moyenne (minutes)')
        ax6.set_title('Durée Moyenne par Mode de Transport', fontweight='bold')
        ax6.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_analyse_modes(self, pdf):
        """Page 2: Analyse détaillée par mode de transport"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('Analyse Détaillée par Mode de Transport', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # Distance moyenne vs Émissions moyennes
        ax1 = plt.subplot(2, 2, 1)
        stats_mode = self.df.groupby('mode_transport').agg({
            'distance': 'mean',
            'emission_co2': 'mean'
        }).round(2)
        ax1.scatter(stats_mode['distance'], stats_mode['emission_co2'], 
                   s=200, alpha=0.6, c=range(len(stats_mode)), cmap='viridis')
        for idx, mode in enumerate(stats_mode.index):
            ax1.annotate(mode, (stats_mode.iloc[idx]['distance'], 
                               stats_mode.iloc[idx]['emission_co2']),
                        fontsize=9, ha='center')
        ax1.set_xlabel('Distance moyenne (km)')
        ax1.set_ylabel('Émissions CO₂ moyennes (g)')
        ax1.set_title('Distance vs Émissions par Mode', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Intensité carbone (g CO2/km)
        ax2 = plt.subplot(2, 2, 2)
        intensite_carbone = ((self.df.groupby('mode_transport')['emission_co2'].sum() * 1000) / 
                            self.df.groupby('mode_transport')['distance'].sum()).sort_values(ascending=False)
        intensite_carbone.plot(kind='bar', ax=ax2, color='orangered')
        ax2.set_ylabel('g CO₂ / km')
        ax2.set_title('Intensité Carbone par Mode de Transport', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(axis='y', alpha=0.3)
        
        # Vitesse moyenne par mode (km/h)
        ax3 = plt.subplot(2, 2, 3)
        self.df['vitesse_kmh'] = (self.df['distance'] / self.df['duration_in_minutes']) * 60
        vitesse_par_mode = self.df.groupby('mode_transport')['vitesse_kmh'].mean().sort_values(ascending=False)
        vitesse_par_mode.plot(kind='barh', ax=ax3, color='skyblue')
        ax3.set_xlabel('Vitesse moyenne (km/h)')
        ax3.set_title('Vitesse Moyenne par Mode de Transport', fontweight='bold')
        ax3.grid(axis='x', alpha=0.3)
        
        # Part modale en distance
        ax4 = plt.subplot(2, 2, 4)
        distance_totale_mode = self.df.groupby('mode_transport')['distance'].sum()
        colors = plt.cm.Pastel1(range(len(distance_totale_mode)))
        wedges, texts, autotexts = ax4.pie(distance_totale_mode.values, 
                                            labels=distance_totale_mode.index,
                                            autopct='%1.1f%%',
                                            colors=colors, startangle=90)
        ax4.set_title('Part Modale en Distance', fontweight='bold')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_distribution_distances(self, pdf):
        """Page 3: Distribution des distances"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('Distribution des Distances', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # Histogramme global
        ax1 = plt.subplot(2, 2, 1)
        self.df['distance'].hist(bins=50, ax=ax1, color='steelblue', edgecolor='black', alpha=0.7)
        ax1.set_xlabel('Distance (km)')
        ax1.set_ylabel('Nombre de trajets')
        ax1.set_title('Distribution Globale des Distances', fontweight='bold')
        ax1.axvline(self.df['distance'].median(), color='red', linestyle='--', 
                   label=f'Médiane: {self.df["distance"].median():.2f} km')
        ax1.axvline(self.df['distance'].mean(), color='orange', linestyle='--', 
                   label=f'Moyenne: {self.df["distance"].mean():.2f} km')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Boîtes à moustaches par mode
        ax2 = plt.subplot(2, 2, 2)
        self.df.boxplot(column='distance', by='mode_transport', ax=ax2)
        ax2.set_xlabel('Mode de transport')
        ax2.set_ylabel('Distance (km)')
        ax2.set_title('Distribution des Distances par Mode', fontweight='bold')
        plt.suptitle('')  # Enlever le titre automatique
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(axis='y', alpha=0.3)
        
        # Distribution par catégories de distance
        ax3 = plt.subplot(2, 2, 3)
        bins_distance = [0, 1, 5, 10, 20, 50, 100, float('inf')]
        labels_distance = ['<1km', '1-5km', '5-10km', '10-20km', '20-50km', '50-100km', '>100km']
        self.df['categorie_distance'] = pd.cut(self.df['distance'], bins=bins_distance, labels=labels_distance)
        cat_counts = self.df['categorie_distance'].value_counts().sort_index()
        cat_counts.plot(kind='bar', ax=ax3, color='mediumseagreen')
        ax3.set_xlabel('Catégorie de distance')
        ax3.set_ylabel('Nombre de trajets')
        ax3.set_title('Répartition par Catégorie de Distance', fontweight='bold')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(axis='y', alpha=0.3)
        
        # Cumulative distribution
        ax4 = plt.subplot(2, 2, 4)
        distances_sorted = np.sort(self.df['distance'].dropna())
        cumulative = np.arange(1, len(distances_sorted) + 1) / len(distances_sorted) * 100
        ax4.plot(distances_sorted, cumulative, linewidth=2, color='darkblue')
        ax4.set_xlabel('Distance (km)')
        ax4.set_ylabel('Pourcentage cumulé (%)')
        ax4.set_title('Distribution Cumulative des Distances', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.axhline(50, color='red', linestyle='--', alpha=0.5, label='50%')
        ax4.axhline(90, color='orange', linestyle='--', alpha=0.5, label='90%')
        ax4.legend()
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_analyse_temporelle(self, pdf):
        """Page 4: Analyse temporelle"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('Analyse Temporelle des Déplacements', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # Trajets par jour
        ax1 = plt.subplot(3, 1, 1)
        self.df['date'] = self.df['start_time'].dt.date
        trajets_par_jour = self.df.groupby('date').size()
        trajets_par_jour.plot(ax=ax1, color='steelblue', linewidth=1.5)
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Nombre de trajets')
        ax1.set_title('Évolution du Nombre de Trajets par Jour', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Trajets par jour de la semaine
        ax2 = plt.subplot(3, 2, 3)
        self.df['jour_semaine'] = self.df['start_time'].dt.day_name()
        jours_ordre = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        jours_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        trajets_par_jour_sem = self.df['jour_semaine'].value_counts().reindex(jours_ordre)
        trajets_par_jour_sem.index = jours_fr
        trajets_par_jour_sem.plot(kind='bar', ax=ax2, color='coral')
        ax2.set_xlabel('Jour de la semaine')
        ax2.set_ylabel('Nombre de trajets')
        ax2.set_title('Trajets par Jour de la Semaine', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(axis='y', alpha=0.3)
        
        # Trajets par heure
        ax3 = plt.subplot(3, 2, 4)
        self.df['heure'] = self.df['start_time'].dt.hour
        trajets_par_heure = self.df['heure'].value_counts().sort_index()
        trajets_par_heure.plot(kind='bar', ax=ax3, color='lightgreen')
        ax3.set_xlabel('Heure de la journée')
        ax3.set_ylabel('Nombre de trajets')
        ax3.set_title('Trajets par Heure de la Journée', fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        
        # Heatmap jour/heure
        ax4 = plt.subplot(3, 2, (5, 6))
        heatmap_data = self.df.groupby(['jour_semaine', 'heure']).size().unstack(fill_value=0)
        heatmap_data = heatmap_data.reindex(jours_ordre)
        heatmap_data.index = jours_fr
        sns.heatmap(heatmap_data, cmap='YlOrRd', ax=ax4, cbar_kws={'label': 'Nombre de trajets'})
        ax4.set_xlabel('Heure de la journée')
        ax4.set_ylabel('Jour de la semaine')
        ax4.set_title('Heatmap: Trajets par Jour et Heure', fontweight='bold')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_emissions_co2(self, pdf):
        """Page 5: Analyse des émissions CO2"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('Analyse des Émissions CO₂', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # Émissions par mode (camembert)
        ax1 = plt.subplot(2, 2, 1)
        co2_par_mode = self.df.groupby('mode_transport')['emission_co2'].sum()
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(co2_par_mode)))
        ax1.pie(co2_par_mode.values, labels=co2_par_mode.index, 
               autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('Répartition des Émissions CO₂ par Mode', fontweight='bold')
        
        # Émissions cumulées dans le temps
        ax2 = plt.subplot(2, 2, 2)
        self.df_sorted = self.df.sort_values('start_time')
        self.df_sorted['co2_cumule'] = self.df_sorted['emission_co2'].cumsum()  # déjà en kg
        ax2.plot(self.df_sorted['start_time'], self.df_sorted['co2_cumule'], 
                color='darkred', linewidth=2)
        ax2.set_xlabel('Date')
        ax2.set_ylabel('CO₂ cumulé (kg)')
        ax2.set_title('Évolution Cumulative des Émissions CO₂', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Distribution des émissions par trajet
        ax3 = plt.subplot(2, 2, 3)
        self.df['emission_co2'].hist(bins=50, ax=ax3, color='indianred', edgecolor='black', alpha=0.7)
        ax3.set_xlabel('Émissions CO₂ par trajet (g)')
        ax3.set_ylabel('Nombre de trajets')
        ax3.set_title('Distribution des Émissions par Trajet', fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        
        # Comparaison intensité carbone
        ax4 = plt.subplot(2, 2, 4)
        intensite = (self.df.groupby('mode_transport')['emission_co2'].sum() / 
                    self.df.groupby('mode_transport')['distance'].sum()).sort_values()
        colors_intensity = ['green' if x < 50 else 'orange' if x < 150 else 'red' for x in intensite.values]
        intensite.plot(kind='barh', ax=ax4, color=colors_intensity)
        ax4.set_xlabel('g CO₂ / km')
        ax4.set_title('Intensité Carbone par Mode\n(vert: faible, orange: moyen, rouge: élevé)', 
                     fontweight='bold')
        ax4.grid(axis='x', alpha=0.3)
        
        # Texte d'analyse
        emission_totale_kg = self.df['emission_co2'].sum()  # déjà en kg
        distance_totale = self.df['distance'].sum()
        intensite_globale = (self.df['emission_co2'].sum() * 1000 / distance_totale) if distance_totale > 0 else 0  # g/km
        
        texte_analyse = f"""
BILAN CARBONE

Émissions totales : {emission_totale_kg:.1f} kg CO₂
Distance totale : {distance_totale:.1f} km
Intensité carbone moyenne : {intensite_globale:.1f} g CO₂/km

Équivalences :
• {emission_totale_kg/0.2:.0f} trajets Paris-Lyon en TGV
• {emission_totale_kg/2100:.1f} vols Paris-New York
• {emission_totale_kg/0.4:.0f} kg de bœuf produit
        """
        
        fig.text(0.5, 0.02, texte_analyse, ha='center', fontsize=9,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
                fontfamily='monospace')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_top_utilisateurs(self, pdf):
        """Page 6: Top utilisateurs"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('Analyse des Utilisateurs', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # Top 10 utilisateurs par nombre de trajets
        ax1 = plt.subplot(2, 2, 1)
        top_trajets = self.df['utilisateur'].value_counts().head(10)
        top_trajets.plot(kind='barh', ax=ax1, color='steelblue')
        ax1.set_xlabel('Nombre de trajets')
        ax1.set_title('Top 10 - Utilisateurs les Plus Actifs', fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # Top 10 utilisateurs par distance
        ax2 = plt.subplot(2, 2, 2)
        top_distance = self.df.groupby('utilisateur')['distance'].sum().sort_values(ascending=False).head(10)
        top_distance.plot(kind='barh', ax=ax2, color='coral')
        ax2.set_xlabel('Distance totale (km)')
        ax2.set_title('Top 10 - Plus Grandes Distances', fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        # Top 10 utilisateurs par émissions
        ax3 = plt.subplot(2, 2, 3)
        top_co2 = self.df.groupby('utilisateur')['emission_co2'].sum().sort_values(ascending=False).head(10)
        # Valeurs déjà en kg
        top_co2.plot(kind='barh', ax=ax3, color='indianred')
        ax3.set_xlabel('Émissions CO₂ totales (kg)')
        ax3.set_title('Top 10 - Plus Grandes Émissions CO₂', fontweight='bold')
        ax3.grid(axis='x', alpha=0.3)
        
        # Distribution du nombre de trajets par utilisateur
        ax4 = plt.subplot(2, 2, 4)
        trajets_par_user = self.df['utilisateur'].value_counts()
        trajets_par_user.hist(bins=30, ax=ax4, color='lightgreen', edgecolor='black', alpha=0.7)
        ax4.set_xlabel('Nombre de trajets par utilisateur')
        ax4.set_ylabel('Nombre d\'utilisateurs')
        ax4.set_title('Distribution de l\'Activité des Utilisateurs', fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)
        ax4.axvline(trajets_par_user.median(), color='red', linestyle='--', 
                   label=f'Médiane: {trajets_par_user.median():.0f}')
        ax4.legend()
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def generer_rapport_utilisateur(self, utilisateur, filename=None):
        """Génère un rapport individuel pour un utilisateur"""
        if filename is None:
            filename = f'rapport_utilisateur_{utilisateur}.pdf'
        
        df_user = self.df[self.df['utilisateur'] == utilisateur]
        
        if len(df_user) == 0:
            print(f"✗ Aucune donnée pour l'utilisateur {utilisateur}")
            return
        
        with PdfPages(filename) as pdf:
            fig = plt.figure(figsize=(11.69, 8.27))
            fig.suptitle(f'Rapport Personnel - Utilisateur: {utilisateur}', 
                        fontsize=14, fontweight='bold', y=0.98)
            
            # Statistiques personnelles
            ax1 = plt.subplot(3, 2, 1)
            ax1.axis('off')
            stats_user = f"""
STATISTIQUES PERSONNELLES

Nombre de trajets : {len(df_user)}
Distance totale : {df_user['distance'].sum():.1f} km
Distance moyenne : {df_user['distance'].mean():.2f} km

Durée totale : {df_user['duration_in_minutes'].sum():.0f} min
Durée moyenne : {df_user['duration_in_minutes'].mean():.1f} min

Émissions CO₂ totales : {df_user['emission_co2'].sum()*1000:.0f} g ({df_user['emission_co2'].sum():.2f} kg)
Émissions moyennes : {df_user['emission_co2'].mean()*1000:.1f} g/trajet

Mode préféré : {df_user['mode_transport'].mode()[0]}
            """
            ax1.text(0.05, 0.95, stats_user, transform=ax1.transAxes,
                    fontsize=10, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
            
            # Modes de transport utilisés
            ax2 = plt.subplot(3, 2, 2)
            df_user['mode_transport'].value_counts().plot(kind='pie', ax=ax2, autopct='%1.1f%%')
            ax2.set_title('Vos Modes de Transport', fontweight='bold')
            ax2.set_ylabel('')
            
            # Distance par mode
            ax3 = plt.subplot(3, 2, 3)
            df_user.groupby('mode_transport')['distance'].sum().plot(kind='bar', ax=ax3, color='steelblue')
            ax3.set_ylabel('Distance (km)')
            ax3.set_title('Distance par Mode de Transport', fontweight='bold')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(axis='y', alpha=0.3)
            
            # Émissions par mode
            ax4 = plt.subplot(3, 2, 4)
            df_user.groupby('mode_transport')['emission_co2'].sum().plot(kind='bar', ax=ax4, color='coral')
            ax4.set_ylabel('Émissions CO₂ (g)')
            ax4.set_title('Émissions CO₂ par Mode', fontweight='bold')
            ax4.tick_params(axis='x', rotation=45)
            ax4.grid(axis='y', alpha=0.3)
            
            # Évolution temporelle
            ax5 = plt.subplot(3, 1, 3)
            df_user_sorted = df_user.sort_values('start_time')
            df_user_sorted.set_index('start_time')['distance'].plot(ax=ax5, marker='o', linestyle='-', markersize=3)
            ax5.set_xlabel('Date')
            ax5.set_ylabel('Distance (km)')
            ax5.set_title('Évolution de Vos Trajets', fontweight='bold')
            ax5.grid(True, alpha=0.3)
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        print(f"✓ Rapport utilisateur généré : {filename}")
    
    def generer_analyse_pdf(self, filename='analyse_greenmove.pdf', format='pdf'):
        """Génère une analyse en format PDF ou HTML avec illustrations et texte"""
        if format == 'html':
            filename = filename.replace('.pdf', '.html')
            return self.generer_analyse_html(filename)
        
        with PdfPages(filename) as pdf:
            # Page 1: Résumé Exécutif avec KPIs
            self._page_analyse_resume_executif(pdf)
            
            # Page 2: Analyse Détaillée des Modes de Transport
            self._page_analyse_modes_detaillee(pdf)
            
            # Page 3: Impact Environnemental et Recommandations
            self._page_analyse_environnement(pdf)
            
            # Page 4: Analyse Comportementale des Utilisateurs
            self._page_analyse_comportementale(pdf)
            
            # Métadonnées
            d = pdf.infodict()
            d['Title'] = 'Greenmove - Analyse Détaillée'
            d['Author'] = 'Greenmove Analytics'
            d['Subject'] = 'Analyse et Recommandations'
            d['CreationDate'] = datetime.now()
        
        print(f"✓ Analyse PDF générée : {filename}")
    
    def generer_analyse_html(self, filename='analyse_greenmove.html'):
        """Génère l'analyse en format HTML avec illustrations"""
        import base64
        from io import BytesIO
        
        stats = self.stats_globales
        intensite_globale = (stats['emission_totale'] * 1000) / stats['distance_totale']  # g/km
        
        # Déterminer le niveau (seuils configurables dans config.py)
        if intensite_globale < SEUIL_EXCELLENT:
            niveau = "EXCELLENT ✨"
            couleur = '#28a745'
        elif intensite_globale < SEUIL_BON:
            niveau = "BON ✅"
            couleur = '#5cb85c'
        elif intensite_globale < SEUIL_MOYEN:
            niveau = "MOYEN ⚠️"
            couleur = '#ffc107'
        else:
            niveau = "À AMÉLIORER ❗"
            couleur = '#dc3545'
        
        html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Greenmove - Analyse Stratégique</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            text-align: center;
            color: #1e3c72;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            font-size: 1.5em;
            margin-bottom: 40px;
            font-weight: 300;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin: 40px 0;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            color: white;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        .kpi-card:before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%);
        }}
        .kpi-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 30px rgba(0,0,0,0.3);
        }}
        .kpi-icon {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .kpi-value {{
            font-size: 2.8em;
            font-weight: bold;
            margin: 15px 0;
        }}
        .kpi-label {{
            font-size: 1.1em;
            opacity: 0.95;
        }}
        .indicator-card {{
            background: {couleur};
            color: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin: 30px 0;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }}
        .indicator-value {{
            font-size: 3.5em;
            font-weight: bold;
            margin: 20px 0;
        }}
        .indicator-level {{
            font-size: 2em;
            margin: 10px 0;
        }}
        .section {{
            margin: 50px 0;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            border-left: 6px solid #667eea;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #1e3c72;
            font-size: 2.2em;
            margin-bottom: 25px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
        }}
        .chart-container {{
            margin: 30px 0;
            text-align: center;
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 18px;
            text-align: left;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: bold;
            font-size: 1.1em;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        tr:hover {{
            background: #e9ecef;
        }}
        .action-plan {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 35px;
            border-radius: 15px;
            margin: 30px 0;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }}
        .action-plan h3 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 2px solid white;
            padding-bottom: 10px;
        }}
        .action-plan ul {{
            list-style: none;
            padding: 0;
        }}
        .action-plan li {{
            padding: 12px 0 12px 30px;
            position: relative;
            font-size: 1.1em;
        }}
        .action-plan li:before {{
            content: '✓';
            position: absolute;
            left: 0;
            font-weight: bold;
            font-size: 1.3em;
        }}
        .segment-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        .segment-card h4 {{
            color: #667eea;
            font-size: 1.3em;
            margin-bottom: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            color: #666;
            border-top: 2px solid #e9ecef;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 GREENMOVE</h1>
        <div class="subtitle">Analyse Stratégique des Déplacements</div>
        
        <!-- KPIs Principaux -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-icon">👥</div>
                <div class="kpi-label">Utilisateurs Actifs</div>
                <div class="kpi-value">{stats['nombre_utilisateurs']:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🚶</div>
                <div class="kpi-label">Trajets Enregistrés</div>
                <div class="kpi-value">{stats['nombre_trajets']:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🛣️</div>
                <div class="kpi-label">Distance Totale</div>
                <div class="kpi-value">{stats['distance_totale']:,.0f} km</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">⏱️</div>
                <div class="kpi-label">Durée Totale</div>
                <div class="kpi-value">{stats['duree_totale']/60:,.0f} h</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🌱</div>
                <div class="kpi-label">Émissions CO₂</div>
                <div class="kpi-value">{stats['emission_totale']:.1f} kg</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🌍</div>
                <div class="kpi-label">Tours de la Terre</div>
                <div class="kpi-value">{stats['distance_totale']/40075:.1f}</div>
            </div>
        </div>
        
        <!-- Indicateur Global -->
        <div class="indicator-card">
            <div class="kpi-icon" style="font-size: 4em;">📈</div>
            <h2 style="color: white; margin: 20px 0;">Indicateur Global de Performance</h2>
            <div class="indicator-value">{intensite_globale:.1f} g CO₂/km</div>
            <div class="indicator-level">{niveau}</div>
            <p style="margin-top: 20px; font-size: 1.2em;">Objectif recommandé : &lt; {OBJECTIF_RECOMMANDE} g CO₂/km</p>
        </div>
"""
        
        # Ajouter les graphiques d'analyse
        html += self._generer_graphiques_analyse_html()
        
        # Analyse des modes
        html += self._generer_tableau_modes_analyse_html()
        
        # Plan d'action
        html += self._generer_plan_action_html()
        
        # Segmentation utilisateurs
        html += self._generer_segmentation_html()
        
        # Footer
        html += f"""
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 10px;">
                <strong>Période analysée :</strong> {stats['periode_debut'].strftime('%d/%m/%Y')} - {stats['periode_fin'].strftime('%d/%m/%Y')}
            </p>
            <p>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
            <p>Greenmove Analytics - Analyse Stratégique de Mobilité</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Analyse HTML générée : {filename}")
    
    def _generer_graphiques_analyse_html(self):
        """Génère les graphiques pour l'analyse HTML"""
        from io import BytesIO
        import base64
        
        html = '<div class="section"><h2>📊 Visualisations Détaillées</h2>'
        
        # Graphique: Intensité carbone par mode
        fig, ax = plt.subplots(figsize=(12, 6))
        intensite_carbone = ((self.df.groupby('mode_transport')['emission_co2'].sum() * 1000) / 
                            self.df.groupby('mode_transport')['distance'].sum()).sort_values()
        colors_intensity = ['#28a745' if x < 50 else '#ffc107' if x < 150 else '#dc3545' 
                           for x in intensite_carbone.values]
        intensite_carbone.plot(kind='barh', ax=ax, color=colors_intensity)
        ax.set_xlabel('g CO₂ / km', fontsize=12)
        ax.set_title('Intensité Carbone par Mode de Transport', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        html += f'<div class="chart-container"><img src="data:image/png;base64,{image_base64}" /></div>'
        
        # Graphique: Répartition des émissions (donut)
        fig, ax = plt.subplots(figsize=(10, 8))
        co2_par_mode = self.df.groupby('mode_transport')['emission_co2'].sum()
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(co2_par_mode)))
        wedges, texts, autotexts = ax.pie(co2_par_mode.values, labels=co2_par_mode.index,
                                            autopct='%1.1f%%', colors=colors, startangle=90,
                                            pctdistance=0.85)
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        ax.add_artist(centre_circle)
        ax.set_title('Répartition des Émissions CO₂ par Mode', fontsize=14, fontweight='bold')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        html += f'<div class="chart-container"><img src="data:image/png;base64,{image_base64}" /></div></div>'
        
        return html
    
    def _generer_tableau_modes_analyse_html(self):
        """Génère le tableau d'analyse des modes pour HTML"""
        mode_stats = self.df.groupby('mode_transport').agg({
            'utilisateur': 'count',
            'distance': ['sum', 'mean'],
            'duration_in_minutes': 'mean',
            'emission_co2': ['sum', 'mean']
        }).round(2)
        
        html = '<div class="section"><h2>🚗 Analyse Détaillée par Mode de Transport</h2>'
        html += '<table><tr><th>Mode</th><th>Trajets</th><th>Distance Tot.</th><th>Distance Moy.</th>'
        html += '<th>Durée Moy.</th><th>CO₂ Total</th><th>CO₂ Moy.</th><th>Intensité (g/km)</th></tr>'
        
        for mode in mode_stats.index:
            nb = mode_stats.loc[mode, ('utilisateur', 'count')]
            dist_tot = mode_stats.loc[mode, ('distance', 'sum')]
            dist_moy = mode_stats.loc[mode, ('distance', 'mean')]
            duree = mode_stats.loc[mode, ('duration_in_minutes', 'mean')]
            co2_tot = mode_stats.loc[mode, ('emission_co2', 'sum')]  # en kg
            co2_moy = mode_stats.loc[mode, ('emission_co2', 'mean')]  # en kg
            intensite = (co2_tot * 1000) / dist_tot if dist_tot > 0 else 0  # g/km
            
            html += f'<tr><td><strong>{mode.upper()}</strong></td>'
            html += f'<td>{nb:.0f}</td>'
            html += f'<td>{dist_tot:,.1f} km</td>'
            html += f'<td>{dist_moy:.2f} km</td>'
            html += f'<td>{duree:.1f} min</td>'
            html += f'<td>{co2_tot:.2f} kg</td>'
            html += f'<td>{co2_moy*1000:.1f} g</td>'
            html += f'<td><strong>{intensite:.1f}</strong></td></tr>'
        
        html += '</table></div>'
        return html
    
    def _generer_plan_action_html(self):
        """Génère le plan d'action pour HTML"""
        stats = self.stats_globales
        
        html = '''
        <div class="action-plan">
            <h3>🎯 PLAN D'ACTION RECOMMANDÉ</h3>
            <p style="font-size: 1.2em; margin: 20px 0;">
                Objectif : Réduire les émissions de 20% sur 6 mois
            </p>
            
            <div style="margin: 30px 0;">
                <h4 style="font-size: 1.4em; margin-bottom: 15px;">📋 Actions Prioritaires</h4>
                <ul>
                    <li>Promotion des modes doux (vélo, marche) pour trajets < 5 km</li>
                    <li>Mise en place d'incitations et gamification</li>
                    <li>Encourager le covoiturage pour les trajets en voiture</li>
                    <li>Développer les transports en commun pour trajets moyens</li>
                    <li>Dashboard mensuel des émissions par utilisateur</li>
                    <li>Alertes automatiques si dépassement de seuils</li>
                    <li>Formation et ateliers de sensibilisation</li>
                </ul>
            </div>
            
            <div style="margin: 30px 0;">
                <h4 style="font-size: 1.4em; margin-bottom: 15px;">🎖️ Indicateurs de Succès</h4>
                <ul>
                    <li>Réduction de 20% des émissions CO₂</li>
                    <li>+15% de trajets en modes doux</li>
                    <li>Satisfaction utilisateurs > 80%</li>
                    <li>Engagement actif > 70% des utilisateurs</li>
                </ul>
            </div>
        </div>
        '''
        
        return html
    
    def _generer_segmentation_html(self):
        """Génère la segmentation utilisateurs pour HTML"""
        trajets_par_user = self.df.groupby('utilisateur').size()
        
        segments = {
            'Très actifs (>50 trajets)': len(trajets_par_user[trajets_par_user > 50]),
            'Actifs (20-50)': len(trajets_par_user[(trajets_par_user >= 20) & (trajets_par_user <= 50)]),
            'Moyens (10-19)': len(trajets_par_user[(trajets_par_user >= 10) & (trajets_par_user < 20)]),
            'Occasionnels (<10)': len(trajets_par_user[trajets_par_user < 10])
        }
        
        html = '<div class="section"><h2>👥 Segmentation des Utilisateurs</h2>'
        
        for segment, count in segments.items():
            pct = (count / len(trajets_par_user)) * 100
            html += f'''
            <div class="segment-card">
                <h4>{segment}</h4>
                <p style="font-size: 1.3em; margin: 10px 0;">
                    <strong>{count}</strong> utilisateurs (<strong>{pct:.1f}%</strong>)
                </p>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _page_analyse_resume_executif(self, pdf):
        """Page 1: Résumé exécutif avec KPIs principaux"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('ANALYSE GREENMOVE - Résumé Exécutif', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        stats = self.stats_globales
        
        # Encadré principal avec statistiques clés
        ax1 = plt.subplot(2, 3, (1, 2))
        ax1.axis('off')
        
        texte_principal = f"""
╔════════════════════════════════════════════════════════════╗
║           INDICATEURS CLÉS DE PERFORMANCE (KPIs)           ║
╚════════════════════════════════════════════════════════════╝

PÉRIODE ANALYSÉE
  Du {stats['periode_debut'].strftime('%d/%m/%Y')} au {stats['periode_fin'].strftime('%d/%m/%Y')}
  Durée : {(stats['periode_fin'] - stats['periode_debut']).days} jours

UTILISATEURS ET ACTIVITÉ
  👥 Utilisateurs actifs : {stats['nombre_utilisateurs']:,}
  🚶 Trajets enregistrés : {stats['nombre_trajets']:,}
  📊 Moyenne par utilisateur : {stats['nombre_trajets']/stats['nombre_utilisateurs']:.1f} trajets

DISTANCES PARCOURUES
  🛣️  Distance totale : {stats['distance_totale']:,.1f} km
  📏 Distance moyenne : {stats['distance_moyenne']:.2f} km/trajet
  🌍 Équivalent : {stats['distance_totale']/40075:.1f} tours de la Terre

TEMPS DE DÉPLACEMENT
  ⏱️  Durée totale : {stats['duree_totale']:,.0f} minutes ({stats['duree_totale']/60:.0f} heures)
  ⏰ Durée moyenne : {stats['duree_moyenne']:.1f} min/trajet
  📅 Temps par utilisateur : {stats['duree_totale']/(60*stats['nombre_utilisateurs']):.1f} heures

IMPACT ENVIRONNEMENTAL
  🌱 Émissions CO₂ : {stats['emission_totale']:.1f} kg ({stats['emission_totale']/1000:.3f} tonnes)
  💨 Moyenne : {stats['emission_moyenne']*1000:.1f} g/trajet
  🌳 Arbres nécessaires : {stats['emission_totale']*0.09:.0f} pour compenser (1 an)
        """
        
        ax1.text(0.02, 0.98, texte_principal, transform=ax1.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
        
        # Graphique de répartition modale
        ax2 = plt.subplot(2, 3, 3)
        mode_counts = self.df['mode_transport'].value_counts()
        colors = plt.cm.Set3(range(len(mode_counts)))
        wedges, texts, autotexts = ax2.pie(mode_counts.values, labels=mode_counts.index, 
                                            autopct='%1.1f%%', colors=colors, startangle=90)
        ax2.set_title('Répartition Modale\n(nombre de trajets)', fontweight='bold', fontsize=11)
        
        # Top 3 modes les plus utilisés
        ax3 = plt.subplot(2, 3, 4)
        ax3.axis('off')
        top_modes = mode_counts.head(3)
        texte_top = "╔═══════════════════════════════╗\n"
        texte_top += "║   TOP 3 MODES DE TRANSPORT   ║\n"
        texte_top += "╚═══════════════════════════════╝\n\n"
        for i, (mode, count) in enumerate(top_modes.items(), 1):
            pct = (count / stats['nombre_trajets']) * 100
            texte_top += f"{i}. {mode.upper()}\n"
            texte_top += f"   {count:,} trajets ({pct:.1f}%)\n\n"
        
        ax3.text(0.1, 0.9, texte_top, transform=ax3.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        
        # Graphique d'intensité carbone
        ax4 = plt.subplot(2, 3, 5)
        intensite_carbone = ((self.df.groupby('mode_transport')['emission_co2'].sum() * 1000) / 
                            self.df.groupby('mode_transport')['distance'].sum()).sort_values()
        colors_intensity = ['green' if x < 50 else 'orange' if x < 150 else 'red' 
                           for x in intensite_carbone.values]
        intensite_carbone.plot(kind='barh', ax=ax4, color=colors_intensity)
        ax4.set_xlabel('g CO₂ / km', fontsize=9)
        ax4.set_title('Intensité Carbone\npar Mode', fontweight='bold', fontsize=11)
        ax4.grid(axis='x', alpha=0.3)
        
        # Indicateur synthétique
        ax5 = plt.subplot(2, 3, 6)
        ax5.axis('off')
        intensite_globale = (stats['emission_totale'] * 1000) / stats['distance_totale']  # g/km
        
        # Déterminer le niveau
        if intensite_globale < 80:
            niveau = "EXCELLENT"
            couleur = 'green'
            emoji = "🌟"
        elif intensite_globale < 120:
            niveau = "BON"
            couleur = 'lightgreen'
            emoji = "✅"
        elif intensite_globale < 180:
            niveau = "MOYEN"
            couleur = 'orange'
            emoji = "⚠️"
        else:
            niveau = "À AMÉLIORER"
            couleur = 'red'
            emoji = "❗"
        
        texte_indicateur = f"""
╔═══════════════════════════╗
║  INDICATEUR GLOBAL        ║
╚═══════════════════════════╝

Intensité Carbone Moyenne
{intensite_globale:.1f} g CO₂/km

{emoji} Niveau : {niveau}

Objectif recommandé :
< 15 g CO₂/km
        """
        
        ax5.text(0.1, 0.8, texte_indicateur, transform=ax5.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor=couleur, alpha=0.4))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_analyse_modes_detaillee(self, pdf):
        """Page 2: Analyse détaillée des modes de transport"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('ANALYSE DÉTAILLÉE PAR MODE DE TRANSPORT', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # Tableau récapitulatif des modes
        ax1 = plt.subplot(3, 2, (1, 2))
        ax1.axis('off')
        
        mode_stats = self.df.groupby('mode_transport').agg({
            'utilisateur': 'count',
            'distance': ['sum', 'mean'],
            'duration_in_minutes': 'mean',
            'emission_co2': ['sum', 'mean']
        }).round(2)
        
        texte_analyse = "╔════════════════════════════════════════════════════════════════════════════╗\n"
        texte_analyse += "║                    ANALYSE COMPARATIVE DES MODES                           ║\n"
        texte_analyse += "╚════════════════════════════════════════════════════════════════════════════╝\n\n"
        
        for mode in mode_stats.index:
            nb_trajets = mode_stats.loc[mode, ('utilisateur', 'count')]
            dist_totale = mode_stats.loc[mode, ('distance', 'sum')]
            dist_moy = mode_stats.loc[mode, ('distance', 'mean')]
            duree_moy = mode_stats.loc[mode, ('duration_in_minutes', 'mean')]
            co2_total = mode_stats.loc[mode, ('emission_co2', 'sum')]  # en kg
            co2_moy = mode_stats.loc[mode, ('emission_co2', 'mean')]  # en kg
            intensite = (co2_total * 1000) / dist_totale if dist_totale > 0 else 0  # g/km
            
            texte_analyse += f"━━━ {mode.upper()} ━━━\n"
            texte_analyse += f"  Trajets : {nb_trajets:.0f} | Distance : {dist_totale:.1f} km | CO₂ : {co2_total:.2f} kg\n"
            texte_analyse += f"  Moy/trajet : {dist_moy:.2f} km en {duree_moy:.1f} min | {co2_moy*1000:.1f} g CO₂\n"
            texte_analyse += f"  Intensité : {intensite:.1f} g CO₂/km\n\n"
        
        ax1.text(0.02, 0.98, texte_analyse, transform=ax1.transAxes,
                fontsize=8, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # Graphique comparatif : Distance vs CO2
        ax2 = plt.subplot(3, 2, 3)
        for mode in mode_stats.index:
            dist = mode_stats.loc[mode, ('distance', 'sum')]
            co2 = mode_stats.loc[mode, ('emission_co2', 'sum')]  # déjà en kg
            ax2.scatter(dist, co2, s=300, alpha=0.6, label=mode)
            ax2.annotate(mode, (dist, co2), fontsize=8, ha='center')
        
        ax2.set_xlabel('Distance totale (km)', fontsize=9)
        ax2.set_ylabel('Émissions totales (kg CO₂)', fontsize=9)
        ax2.set_title('Distance vs Émissions', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Part modale en distance
        ax3 = plt.subplot(3, 2, 4)
        distance_par_mode = self.df.groupby('mode_transport')['distance'].sum().sort_values(ascending=False)
        distance_par_mode.plot(kind='bar', ax=ax3, color='steelblue')
        ax3.set_ylabel('Distance (km)', fontsize=9)
        ax3.set_title('Distance Totale par Mode', fontweight='bold')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(axis='y', alpha=0.3)
        
        # Efficacité énergétique (vitesse vs émissions)
        ax4 = plt.subplot(3, 2, 5)
        self.df['vitesse_kmh'] = (self.df['distance'] / self.df['duration_in_minutes']) * 60
        vitesse_par_mode = self.df.groupby('mode_transport')['vitesse_kmh'].mean()
        co2_par_km = (self.df.groupby('mode_transport')['emission_co2'].sum() / 
                      self.df.groupby('mode_transport')['distance'].sum())
        
        for mode in vitesse_par_mode.index:
            ax4.scatter(vitesse_par_mode[mode], co2_par_km[mode], s=200, alpha=0.6)
            ax4.annotate(mode, (vitesse_par_mode[mode], co2_par_km[mode]), 
                        fontsize=8, ha='center')
        
        ax4.set_xlabel('Vitesse moyenne (km/h)', fontsize=9)
        ax4.set_ylabel('Intensité carbone (g CO₂/km)', fontsize=9)
        ax4.set_title('Efficacité : Vitesse vs Émissions', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # Recommandations par mode
        ax5 = plt.subplot(3, 2, 6)
        ax5.axis('off')
        
        texte_reco = "╔═══════════════════════════════╗\n"
        texte_reco += "║      RECOMMANDATIONS          ║\n"
        texte_reco += "╚═══════════════════════════════╝\n\n"
        
        # Identifier les opportunités
        mode_max_co2 = self.df.groupby('mode_transport')['emission_co2'].sum().idxmax()
        pct_max = (self.df.groupby('mode_transport')['emission_co2'].sum().max() / 
                  self.stats_globales['emission_totale'] * 100)
        
        texte_reco += f"🎯 PRIORITÉ 1\n"
        texte_reco += f"Mode '{mode_max_co2}' représente\n"
        texte_reco += f"{pct_max:.1f}% des émissions.\n"
        texte_reco += f"→ Cibler ce mode en priorité\n\n"
        
        # Trajets courts en voiture
        if 'car' in self.df['mode_transport'].values:
            trajets_courts = len(self.df[(self.df['mode_transport'] == 'car') & 
                                         (self.df['distance'] < 5)])
            if trajets_courts > 0:
                texte_reco += f"🚗 OPPORTUNITÉ\n"
                texte_reco += f"{trajets_courts} trajets en voiture\n"
                texte_reco += f"< 5 km pourraient être\n"
                texte_reco += f"remplacés par vélo/marche\n\n"
        
        # Mode le plus écologique
        mode_min_co2 = co2_par_km.idxmin()
        texte_reco += f"🌱 MODE LE PLUS VERT\n"
        texte_reco += f"'{mode_min_co2}'\n"
        texte_reco += f"{co2_par_km[mode_min_co2]:.1f} g CO₂/km\n"
        texte_reco += f"→ À promouvoir activement\n"
        
        ax5.text(0.05, 0.95, texte_reco, transform=ax5.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.4))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_analyse_environnement(self, pdf):
        """Page 3: Impact environnemental et recommandations"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('IMPACT ENVIRONNEMENTAL ET RECOMMANDATIONS', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        stats = self.stats_globales
        emission_totale_kg = stats['emission_totale']  # déjà en kg
        
        # Bilan carbone
        ax1 = plt.subplot(3, 2, 1)
        ax1.axis('off')
        
        texte_bilan = f"""
╔════════════════════════════════╗
║      BILAN CARBONE GLOBAL      ║
╚════════════════════════════════╝

Émissions totales
{emission_totale_kg:.2f} kg CO₂
({stats['emission_totale']/1000:.3f} tonnes)

Par utilisateur
{emission_totale_kg/stats['nombre_utilisateurs']:.2f} kg CO₂

Par trajet
{stats['emission_moyenne']*1000:.1f} g CO₂

Intensité moyenne
{(stats['emission_totale']*1000)/stats['distance_totale']:.1f} g CO₂/km
        """
        
        ax1.text(0.05, 0.95, texte_bilan, transform=ax1.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        
        # Équivalences visuelles
        ax2 = plt.subplot(3, 2, 2)
        equivalences = {
            'Vols Paris-NY': emission_totale_kg / 2100,
            'Trajets TGV\nParis-Lyon': emission_totale_kg / 0.2,
            'Kg de bœuf': emission_totale_kg / 0.4,
            'Arbres pour\ncompenser (1 an)': emission_totale_kg * 0.09
        }
        
        ax2.barh(list(equivalences.keys()), list(equivalences.values()), color='coral')
        ax2.set_xlabel('Équivalent', fontsize=9)
        ax2.set_title('Équivalences Environnementales', fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        # Évolution cumulative des émissions
        ax3 = plt.subplot(3, 2, 3)
        df_sorted = self.df.sort_values('start_time')
        df_sorted['co2_cumule'] = df_sorted['emission_co2'].cumsum()  # déjà en kg
        ax3.plot(df_sorted['start_time'], df_sorted['co2_cumule'], 
                color='darkred', linewidth=2)
        ax3.fill_between(df_sorted['start_time'], df_sorted['co2_cumule'], 
                         alpha=0.3, color='red')
        ax3.set_xlabel('Date', fontsize=9)
        ax3.set_ylabel('CO₂ cumulé (kg)', fontsize=9)
        ax3.set_title('Évolution Cumulative des Émissions', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Répartition des émissions (donut chart)
        ax4 = plt.subplot(3, 2, 4)
        co2_par_mode = self.df.groupby('mode_transport')['emission_co2'].sum()
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(co2_par_mode)))
        wedges, texts, autotexts = ax4.pie(co2_par_mode.values, labels=co2_par_mode.index,
                                            autopct='%1.1f%%', colors=colors, startangle=90,
                                            pctdistance=0.85)
        # Ajouter un cercle au centre pour effet donut
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        ax4.add_artist(centre_circle)
        ax4.set_title('Répartition des Émissions CO₂', fontweight='bold')
        
        # Plan d'action
        ax5 = plt.subplot(3, 2, (5, 6))
        ax5.axis('off')
        
        texte_plan = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                          PLAN D'ACTION RECOMMANDÉ                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 OBJECTIFS
   • Réduire les émissions de 20% sur 6 mois
   • Augmenter la part des modes doux (vélo, marche) de 15%
   • Sensibiliser 100% des utilisateurs

📋 ACTIONS PRIORITAIRES

   1. PROMOTION DES MODES DOUX
      → Campagne de sensibilisation sur les trajets < 5 km
      → Mise en place d'incitations (gamification, récompenses)
      → Communication sur les bénéfices santé/environnement

   2. OPTIMISATION DES DÉPLACEMENTS
      → Encourager le covoiturage pour les trajets en voiture
      → Développer les transports en commun pour les trajets moyens
      → Créer des challenges inter-utilisateurs

   3. SUIVI ET MESURE
      → Dashboard mensuel des émissions par utilisateur
      → Alertes automatiques si dépassement de seuils
      → Rapports trimestriels avec comparaison d'objectifs

   4. FORMATION ET ACCOMPAGNEMENT
      → Guide des bonnes pratiques de mobilité durable
      → Ateliers de sensibilisation au bilan carbone
      → Coaching personnalisé pour les plus gros émetteurs

🎖️ INDICATEURS DE SUCCÈS
   ✓ Réduction de 20% des émissions CO₂
   ✓ +15% de trajets en modes doux
   ✓ Satisfaction utilisateurs > 80%
   ✓ Engagement actif > 70% des utilisateurs
        """
        
        ax5.text(0.02, 0.98, texte_plan, transform=ax5.transAxes,
                fontsize=8, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _page_analyse_comportementale(self, pdf):
        """Page 4: Analyse comportementale des utilisateurs"""
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle('ANALYSE COMPORTEMENTALE DES UTILISATEURS', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # Segmentation des utilisateurs
        ax1 = plt.subplot(2, 3, 1)
        ax1.axis('off')
        
        trajets_par_user = self.df.groupby('utilisateur').size()
        
        # Créer des segments
        segments = {
            'Très actifs (>50 trajets)': len(trajets_par_user[trajets_par_user > 50]),
            'Actifs (20-50)': len(trajets_par_user[(trajets_par_user >= 20) & (trajets_par_user <= 50)]),
            'Moyens (10-19)': len(trajets_par_user[(trajets_par_user >= 10) & (trajets_par_user < 20)]),
            'Occasionnels (<10)': len(trajets_par_user[trajets_par_user < 10])
        }
        
        texte_segment = "╔═══════════════════════════╗\n"
        texte_segment += "║  SEGMENTATION UTILISATEURS║\n"
        texte_segment += "╚═══════════════════════════╝\n\n"
        
        for segment, count in segments.items():
            pct = (count / len(trajets_par_user)) * 100
            texte_segment += f"{segment}\n"
            texte_segment += f"{count} users ({pct:.1f}%)\n\n"
        
        ax1.text(0.05, 0.95, texte_segment, transform=ax1.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lavender', alpha=0.5))
        
        # Pie chart des segments
        ax2 = plt.subplot(2, 3, 2)
        colors_seg = ['darkgreen', 'lightgreen', 'orange', 'lightcoral']
        ax2.pie(segments.values(), labels=segments.keys(), autopct='%1.1f%%',
               colors=colors_seg, startangle=90)
        ax2.set_title('Répartition des Profils', fontweight='bold', fontsize=10)
        
        # Distribution de l'activité
        ax3 = plt.subplot(2, 3, 3)
        trajets_par_user.hist(bins=30, ax=ax3, color='steelblue', edgecolor='black', alpha=0.7)
        ax3.axvline(trajets_par_user.median(), color='red', linestyle='--', 
                   label=f'Médiane: {trajets_par_user.median():.0f}')
        ax3.axvline(trajets_par_user.mean(), color='orange', linestyle='--',
                   label=f'Moyenne: {trajets_par_user.mean():.0f}')
        ax3.set_xlabel('Nombre de trajets', fontsize=9)
        ax3.set_ylabel('Nombre d\'utilisateurs', fontsize=9)
        ax3.set_title('Distribution de l\'Activité', fontweight='bold', fontsize=10)
        ax3.legend(fontsize=8)
        ax3.grid(axis='y', alpha=0.3)
        
        # Top 10 utilisateurs par émissions
        ax4 = plt.subplot(2, 3, 4)
        top_co2_users = self.df.groupby('utilisateur')['emission_co2'].sum().sort_values(ascending=False).head(10)
        # Valeurs déjà en kg
        top_co2_users.plot(kind='barh', ax=ax4, color='indianred')
        ax4.set_xlabel('Émissions CO₂ (kg)', fontsize=9)
        ax4.set_title('Top 10 Émetteurs CO₂', fontweight='bold', fontsize=10)
        ax4.grid(axis='x', alpha=0.3)
        
        # Préférences modales par segment
        ax5 = plt.subplot(2, 3, 5)
        # Créer une matrice de préférences
        user_segments = pd.cut(trajets_par_user, bins=[0, 10, 20, 50, float('inf')],
                               labels=['Occasionnel', 'Moyen', 'Actif', 'Très actif'])
        
        df_with_segment = self.df.copy()
        df_with_segment['segment'] = df_with_segment['utilisateur'].map(
            dict(zip(trajets_par_user.index, user_segments))
        )
        
        mode_by_segment = pd.crosstab(df_with_segment['segment'], 
                                       df_with_segment['mode_transport'],
                                       normalize='index') * 100
        
        sns.heatmap(mode_by_segment, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax5,
                   cbar_kws={'label': '% de trajets'})
        ax5.set_xlabel('Mode de transport', fontsize=9)
        ax5.set_ylabel('Segment utilisateur', fontsize=9)
        ax5.set_title('Préférences Modales par Segment', fontweight='bold', fontsize=10)
        plt.setp(ax5.get_xticklabels(), rotation=45, ha='right')
        
        # Insights et recommandations
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        texte_insights = """
╔═════════════════════════════╗
║   INSIGHTS COMPORTEMENTAUX  ║
╚═════════════════════════════╝

📊 OBSERVATIONS CLÉS

• Distribution inégale
  de l'activité entre
  utilisateurs

• Top 20% des utilisateurs
  génèrent potentiellement
  60-80% du trafic

• Corrélation entre
  fréquence d'usage et
  diversité des modes

💡 ACTIONS CIBLÉES

→ Utilisateurs occasionnels:
  Campagnes de réengagement

→ Utilisateurs moyens:
  Encourager régularité

→ Utilisateurs actifs:
  Gamification avancée
  Ambassadeurs green

→ Très actifs:
  Programme VIP
  Challenges personnalisés
        """
        
        ax6.text(0.05, 0.95, texte_insights, transform=ax6.transAxes,
                fontsize=8, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def generer_analyse_textuelle(self, filename='analyse_greenmove.txt'):
        """Génère une analyse textuelle détaillée en français"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("GREENMOVE - RAPPORT D'ANALYSE DES DÉPLACEMENTS\n")
            f.write("=" * 80 + "\n\n")
            
            # Vue d'ensemble
            f.write("1. VUE D'ENSEMBLE\n")
            f.write("-" * 80 + "\n")
            stats = self.stats_globales
            f.write(f"Période d'analyse : du {stats['periode_debut'].strftime('%d/%m/%Y')} ")
            f.write(f"au {stats['periode_fin'].strftime('%d/%m/%Y')}\n\n")
            f.write(f"• Nombre d'utilisateurs actifs : {stats['nombre_utilisateurs']:,}\n")
            f.write(f"• Nombre total de trajets : {stats['nombre_trajets']:,}\n")
            f.write(f"• Distance totale parcourue : {stats['distance_totale']:,.1f} km\n")
            f.write(f"• Distance moyenne par trajet : {stats['distance_moyenne']:.2f} km\n")
            f.write(f"• Durée totale : {stats['duree_totale']:,.0f} minutes ")
            f.write(f"({stats['duree_totale']/60:.0f} heures)\n")
            f.write(f"• Émissions CO₂ totales : {stats['emission_totale']*1000:,.0f} g ")
            f.write(f"({stats['emission_totale']:.1f} kg)\n\n")
            
            # Analyse par mode
            f.write("\n2. ANALYSE PAR MODE DE TRANSPORT\n")
            f.write("-" * 80 + "\n")
            mode_stats = self.df.groupby('mode_transport').agg({
                'utilisateur': 'count',
                'distance': ['sum', 'mean'],
                'duration_in_minutes': 'mean',
                'emission_co2': ['sum', 'mean']
            }).round(2)
            
            for mode in mode_stats.index:
                f.write(f"\n{mode.upper()}\n")
                f.write(f"  • Nombre de trajets : {mode_stats.loc[mode, ('utilisateur', 'count')]:.0f}\n")
                f.write(f"  • Distance totale : {mode_stats.loc[mode, ('distance', 'sum')]:.1f} km\n")
                f.write(f"  • Distance moyenne : {mode_stats.loc[mode, ('distance', 'mean')]:.2f} km\n")
                f.write(f"  • Durée moyenne : {mode_stats.loc[mode, ('duration_in_minutes', 'mean')]:.1f} min\n")
                f.write(f"  • Émissions totales : {mode_stats.loc[mode, ('emission_co2', 'sum')]*1000:.0f} g\n")
                f.write(f"  • Émissions moyennes : {mode_stats.loc[mode, ('emission_co2', 'mean')]*1000:.1f} g\n")
                
                # Calcul intensité carbone
                intensite = (mode_stats.loc[mode, ('emission_co2', 'sum')] * 1000) / mode_stats.loc[mode, ('distance', 'sum')]
                f.write(f"  • Intensité carbone : {intensite:.1f} g CO₂/km\n")
            
            # Impact environnemental
            f.write("\n\n3. IMPACT ENVIRONNEMENTAL\n")
            f.write("-" * 80 + "\n")
            emission_totale_kg = stats['emission_totale']  # déjà en kg
            f.write(f"Les trajets enregistrés ont généré {emission_totale_kg:.1f} kg de CO₂.\n\n")
            f.write("Équivalences :\n")
            f.write(f"  • {emission_totale_kg/0.2:.0f} trajets Paris-Lyon en TGV\n")
            f.write(f"  • {emission_totale_kg/2100:.2f} vols aller-retour Paris-New York\n")
            f.write(f"  • {emission_totale_kg/0.4:.0f} kg de viande de bœuf produite\n")
            f.write(f"  • {emission_totale_kg*0.09:.0f} arbres nécessaires pour compenser (sur 1 an)\n\n")
            
            # Modes les plus propres
            intensite_par_mode = ((self.df.groupby('mode_transport')['emission_co2'].sum() * 1000) / 
                                 self.df.groupby('mode_transport')['distance'].sum()).sort_values()
            f.write("Modes les plus écologiques (g CO₂/km) :\n")
            for i, (mode, val) in enumerate(intensite_par_mode.items(), 1):
                f.write(f"  {i}. {mode} : {val:.1f} g CO₂/km\n")
            
            # Recommandations
            f.write("\n\n4. RECOMMANDATIONS\n")
            f.write("-" * 80 + "\n")
            
            # Identifier le mode le plus émetteur
            mode_max_co2 = self.df.groupby('mode_transport')['emission_co2'].sum().idxmax()
            pct_max_co2 = (self.df.groupby('mode_transport')['emission_co2'].sum().max() / 
                          stats['emission_totale'] * 100)
            
            f.write(f"• Le mode '{mode_max_co2}' représente {pct_max_co2:.1f}% des émissions totales.\n")
            f.write(f"  → Privilégier les alternatives moins polluantes pour ce type de trajet.\n\n")
            
            # Analyser les trajets courts en voiture
            if 'car' in self.df['mode_transport'].values:
                trajets_courts_voiture = len(self.df[(self.df['mode_transport'] == 'car') & 
                                                     (self.df['distance'] < 5)])
                if trajets_courts_voiture > 0:
                    f.write(f"• {trajets_courts_voiture} trajets en voiture font moins de 5 km.\n")
                    f.write(f"  → Ces trajets pourraient être effectués en vélo ou à pied.\n\n")
            
            f.write("• Pour réduire l'empreinte carbone :\n")
            f.write("  - Privilégier les transports en commun pour les trajets urbains\n")
            f.write("  - Utiliser le vélo pour les trajets de moins de 5 km\n")
            f.write("  - Covoiturer pour les trajets en voiture\n")
            f.write("  - Regrouper les déplacements pour optimiser les trajets\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("Rapport généré le " + datetime.now().strftime('%d/%m/%Y à %H:%M:%S') + "\n")
            f.write("=" * 80 + "\n")
        
        print(f"✓ Analyse textuelle générée : {filename}")


def main():
    """Fonction principale"""
    print("=" * 60)
    print("GREENMOVE - Génération de Rapport d'Analyse")
    print("=" * 60)
    print()
    
    # Charger la configuration depuis config.py
    try:
        from config import DB_CONFIG
        print("✓ Configuration chargée depuis config.py")
    except ImportError:
        print("⚠️  Fichier config.py non trouvé")
        print("   Créez config.py à partir de config_template.py")
        print()
        print("Utilisation de la configuration par défaut...")
        DB_CONFIG = {
            'host': input("Hôte PostgreSQL: "),
            'database': input("Nom de la base de données: "),
            'user': input("Utilisateur: "),
            'password': input("Mot de passe: "),
            'port': int(input("Port (défaut 5432): ") or "5432")
        }
    
    print()
    
    # Créer l'instance d'analyse
    analytics = GreenmoveAnalytics(**DB_CONFIG)
    
    # Charger les données
    print("📊 Chargement des données...")
    if not analytics.connect_and_load_data():
        print("❌ Impossible de charger les données. Vérifiez la configuration.")
        return
    
    # Calculer les statistiques
    print("📈 Calcul des statistiques...")
    analytics.calculer_statistiques_globales()
    
    # Demander le format de sortie
    print()
    print("Choisissez le format de sortie:")
    print("  1. PDF (par défaut)")
    print("  2. HTML")
    print("  3. Les deux (PDF + HTML)")
    choix = input("Votre choix (1-3) [1]: ").strip() or "1"
    print()
    
    formats_a_generer = []
    if choix == "1":
        formats_a_generer = ['pdf']
    elif choix == "2":
        formats_a_generer = ['html']
    elif choix == "3":
        formats_a_generer = ['pdf', 'html']
    else:
        print("⚠️  Choix invalide, utilisation du format PDF par défaut")
        formats_a_generer = ['pdf']
    
    # Générer les rapports selon le(s) format(s) choisi(s)
    for format in formats_a_generer:
        ext = 'pdf' if format == 'pdf' else 'html'
        
        # Rapport global
        print(f"📄 Génération du rapport global ({format.upper()})...")
        analytics.generer_rapport_pdf(f'rapport_greenmove_global.{ext}', format=format)
        
        # Analyse avec illustrations
        print(f"📊 Génération de l'analyse avec illustrations ({format.upper()})...")
        analytics.generer_analyse_pdf(f'analyse_greenmove.{ext}', format=format)
    
    # Générer l'analyse textuelle
    print("📝 Génération de l'analyse textuelle...")
    analytics.generer_analyse_textuelle('analyse_greenmove.txt')
    
    # Générer des rapports individuels pour les 5 utilisateurs les plus actifs
    print("👤 Génération des rapports utilisateurs...")
    top_users = analytics.df['utilisateur'].value_counts().head(5).index
    for user in top_users:
        analytics.generer_rapport_utilisateur(user)
    
    print()
    print("=" * 60)
    print("✅ GÉNÉRATION TERMINÉE !")
    print("=" * 60)
    print()
    print("Fichiers générés :")
    if 'pdf' in formats_a_generer:
        print("  • rapport_greenmove_global.pdf - Rapport complet PDF")
        print("  • analyse_greenmove.pdf - Analyse stratégique PDF")
    if 'html' in formats_a_generer:
        print("  • rapport_greenmove_global.html - Rapport complet HTML")
        print("  • analyse_greenmove.html - Analyse stratégique HTML")
    print("  • analyse_greenmove.txt - Analyse textuelle")
    print("  • rapport_utilisateur_*.pdf - Rapports individuels")
    print()


if __name__ == "__main__":
    main()