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
    
    def generer_rapport_pdf(self, filename='rapport_greenmove.pdf'):
        """Génère le rapport complet en PDF"""
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

Émissions CO₂ totales : {stats['emission_totale']:,.0f} g ({stats['emission_totale']/1000:.1f} kg)
Émissions moyennes : {stats['emission_moyenne']:.1f} g/trajet
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
        intensite_carbone = (self.df.groupby('mode_transport')['emission_co2'].sum() / 
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
        self.df_sorted['co2_cumule'] = self.df_sorted['emission_co2'].cumsum() / 1000  # en kg
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
        emission_totale_kg = self.df['emission_co2'].sum() / 1000
        distance_totale = self.df['distance'].sum()
        intensite_globale = (self.df['emission_co2'].sum() / distance_totale) if distance_totale > 0 else 0
        
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
        top_co2 = top_co2 / 1000  # en kg
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

Émissions CO₂ totales : {df_user['emission_co2'].sum():.0f} g
Émissions moyennes : {df_user['emission_co2'].mean():.1f} g/trajet

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
            f.write(f"• Émissions CO₂ totales : {stats['emission_totale']:,.0f} g ")
            f.write(f"({stats['emission_totale']/1000:.1f} kg)\n\n")
            
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
                f.write(f"  • Émissions totales : {mode_stats.loc[mode, ('emission_co2', 'sum')]:.0f} g\n")
                f.write(f"  • Émissions moyennes : {mode_stats.loc[mode, ('emission_co2', 'mean')]:.1f} g\n")
                
                # Calcul intensité carbone
                intensite = mode_stats.loc[mode, ('emission_co2', 'sum')] / mode_stats.loc[mode, ('distance', 'sum')]
                f.write(f"  • Intensité carbone : {intensite:.1f} g CO₂/km\n")
            
            # Impact environnemental
            f.write("\n\n3. IMPACT ENVIRONNEMENTAL\n")
            f.write("-" * 80 + "\n")
            emission_totale_kg = stats['emission_totale'] / 1000
            f.write(f"Les trajets enregistrés ont généré {emission_totale_kg:.1f} kg de CO₂.\n\n")
            f.write("Équivalences :\n")
            f.write(f"  • {emission_totale_kg/0.2:.0f} trajets Paris-Lyon en TGV\n")
            f.write(f"  • {emission_totale_kg/2100:.2f} vols aller-retour Paris-New York\n")
            f.write(f"  • {emission_totale_kg/0.4:.0f} kg de viande de bœuf produite\n")
            f.write(f"  • {emission_totale_kg*0.09:.0f} arbres nécessaires pour compenser (sur 1 an)\n\n")
            
            # Modes les plus propres
            intensite_par_mode = (self.df.groupby('mode_transport')['emission_co2'].sum() / 
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
    
    # Configuration de la connexion (à adapter)
    DB_CONFIG = {
        'host': 'votre-serveur.postgres.database.azure.com',
        'database': 'greenmove',
        'user': 'votre_utilisateur',
        'password': 'votre_mot_de_passe',
        'port': 5432
    }
    
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
    
    # Générer le rapport PDF global
    print("📄 Génération du rapport PDF global...")
    analytics.generer_rapport_pdf('rapport_greenmove_global.pdf')
    
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
    print("  • rapport_greenmove_global.pdf - Rapport complet")
    print("  • analyse_greenmove.txt - Analyse textuelle")
    print("  • rapport_utilisateur_*.pdf - Rapports individuels")
    print()


if __name__ == "__main__":
    main()
