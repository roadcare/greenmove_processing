# Structure du Projet Greenmove Analytics

## 📁 Fichiers du Projet

```
greenmove-analytics/
│
├── greenmove_reporting.py      # Script principal avec la classe GreenmoveAnalytics
├── cli.py                       # Interface en ligne de commande
├── exemple_utilisation.py       # Exemples d'utilisation
├── config_template.py           # Template de configuration
├── requirements.txt             # Dépendances Python
├── README.md                    # Documentation complète
└── .gitignore                   # Fichiers à ignorer par Git
```

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier de configuration
cp config_template.py config.py
# Éditer config.py avec vos identifiants
```

### 2. Première utilisation

**Option A - Script principal :**
```bash
python greenmove_reporting.py
```

**Option B - Interface en ligne de commande :**
```bash
# Tous les rapports
python cli.py --all

# Statistiques rapides
python cli.py --stats

# Rapport global uniquement
python cli.py --global

# Rapport pour un utilisateur
python cli.py --user-id user123
```

**Option C - Exemples interactifs :**
```bash
python exemple_utilisation.py
```

## 📊 Fichiers Générés

Après exécution, vous obtiendrez :

### Rapports PDF
- `rapport_greenmove_global.pdf` (6 pages)
  - Vue d'ensemble
  - Analyse par mode de transport
  - Distribution des distances
  - Analyse temporelle
  - Émissions CO₂
  - Top utilisateurs

- `rapport_utilisateur_*.pdf` (1 page par utilisateur)
  - Statistiques personnelles
  - Graphiques individuels

### Analyses Textuelles
- `analyse_greenmove.txt`
  - Statistiques détaillées
  - Recommandations
  - Équivalences environnementales

## 🔧 Configuration

### config.py

```python
DB_CONFIG = {
    'host': 'votre-serveur.postgres.database.azure.com',
    'database': 'greenmove',
    'user': 'votre_utilisateur@votre-serveur',
    'password': 'VOTRE_MOT_DE_PASSE',
    'port': 5432
}
```

### Variables d'environnement (Recommandé pour la production)

```bash
export GREENMOVE_DB_HOST="votre-serveur.postgres.database.azure.com"
export GREENMOVE_DB_NAME="greenmove"
export GREENMOVE_DB_USER="votre_utilisateur"
export GREENMOVE_DB_PASSWORD="votre_mot_de_passe"
```

Puis dans votre code :
```python
import os

DB_CONFIG = {
    'host': os.getenv('GREENMOVE_DB_HOST'),
    'database': os.getenv('GREENMOVE_DB_NAME'),
    'user': os.getenv('GREENMOVE_DB_USER'),
    'password': os.getenv('GREENMOVE_DB_PASSWORD'),
    'port': 5432
}
```

## 🎯 Cas d'Usage

### 1. Rapport Mensuel Automatisé

Créer un script `rapport_mensuel.py` :

```python
from greenmove_reporting import GreenmoveAnalytics
from config import DB_CONFIG
from datetime import datetime

analytics = GreenmoveAnalytics(**DB_CONFIG)
analytics.connect_and_load_data()
analytics.calculer_statistiques_globales()

# Nom avec date
date_str = datetime.now().strftime('%Y-%m')
analytics.generer_rapport_pdf(f'rapport_mensuel_{date_str}.pdf')
```

Puis avec cron (Linux) :
```bash
# Tous les 1er du mois à 8h
0 8 1 * * cd /path/to/greenmove && python rapport_mensuel.py
```

### 2. Rapport Personnalisé pour un Département

```python
from greenmove_reporting import GreenmoveAnalytics
from config import DB_CONFIG

analytics = GreenmoveAnalytics(**DB_CONFIG)
analytics.connect_and_load_data()

# Filtrer par département
df_dept = analytics.df[analytics.df['utilisateur'].str.startswith('DEPT_')]
analytics.df = df_dept

analytics.calculer_statistiques_globales()
analytics.generer_rapport_pdf('rapport_departement.pdf')
```

### 3. Comparaison Temporelle

```python
import pandas as pd
from greenmove_reporting import GreenmoveAnalytics
from config import DB_CONFIG

analytics = GreenmoveAnalytics(**DB_CONFIG)
analytics.connect_and_load_data()

# Mois actuel vs mois précédent
df_current = analytics.df[analytics.df['start_time'] >= pd.Timestamp.now() - pd.DateOffset(months=1)]
df_previous = analytics.df[(analytics.df['start_time'] >= pd.Timestamp.now() - pd.DateOffset(months=2)) & 
                            (analytics.df['start_time'] < pd.Timestamp.now() - pd.DateOffset(months=1))]

print(f"Trajets mois actuel: {len(df_current)}")
print(f"Trajets mois précédent: {len(df_previous)}")
print(f"Évolution: {((len(df_current) - len(df_previous)) / len(df_previous) * 100):.1f}%")
```

### 4. Alertes Automatiques

```python
from greenmove_reporting import GreenmoveAnalytics
from config import DB_CONFIG

analytics = GreenmoveAnalytics(**DB_CONFIG)
analytics.connect_and_load_data()
stats = analytics.calculer_statistiques_globales()

# Alerte si émissions trop élevées
seuil_co2 = 100000  # 100 kg
if stats['emission_totale'] > seuil_co2:
    print(f"⚠️ ALERTE: Émissions élevées ({stats['emission_totale']/1000:.1f} kg)")
    # Envoyer email, Slack, etc.

# Alerte si baisse d'activité
seuil_trajets = 1000
if stats['nombre_trajets'] < seuil_trajets:
    print(f"⚠️ ALERTE: Activité faible ({stats['nombre_trajets']} trajets)")
```

## 📈 Performance

### Temps d'Exécution Estimés

Pour 9000 utilisateurs :

| Opération | Durée Estimée |
|-----------|---------------|
| Chargement données | 10-30 secondes |
| Calcul statistiques | 5-10 secondes |
| Rapport PDF global | 30-60 secondes |
| Rapport utilisateur | 2-5 secondes |
| Analyse textuelle | 1-2 secondes |
| **TOTAL (complet)** | **2-5 minutes** |

### Optimisation

Pour de grandes bases de données :

```python
# Charger uniquement les données récentes
query = """
    SELECT * FROM tripanalyse.usagestat
    WHERE "startTime" >= NOW() - INTERVAL '3 months'
"""
analytics.df = pd.read_sql_query(query, conn)

# Ou limiter le nombre d'enregistrements
query = """
    SELECT * FROM tripanalyse.usagestat
    ORDER BY "startTime" DESC
    LIMIT 100000
"""
```

## 🔒 Sécurité

### Checklist de Sécurité

- [ ] Ne jamais commiter `config.py` (ajouté dans `.gitignore`)
- [ ] Utiliser des variables d'environnement en production
- [ ] Utiliser Azure Key Vault pour les secrets
- [ ] Restreindre les permissions PostgreSQL (lecture seule si possible)
- [ ] Utiliser SSL pour les connexions PostgreSQL
- [ ] Logs sans informations sensibles

### Connexion SSL PostgreSQL

```python
DB_CONFIG = {
    'host': 'votre-serveur.postgres.database.azure.com',
    'database': 'greenmove',
    'user': 'votre_utilisateur',
    'password': 'votre_mot_de_passe',
    'port': 5432,
    'sslmode': 'require'  # Forcer SSL
}
```

## 🐛 Debugging

### Logs détaillés

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

analytics = GreenmoveAnalytics(**DB_CONFIG)
```

### Test de connexion

```python
import psycopg2
from config import DB_CONFIG

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✓ Connexion réussie")
    conn.close()
except Exception as e:
    print(f"✗ Erreur: {e}")
```

## 📞 Support et Ressources

- **Documentation PostgreSQL** : https://www.postgresql.org/docs/
- **Pandas** : https://pandas.pydata.org/docs/
- **Matplotlib** : https://matplotlib.org/stable/index.html
- **Seaborn** : https://seaborn.pydata.org/
- **Azure PostgreSQL** : https://docs.microsoft.com/azure/postgresql/

## 🔄 Mises à Jour

### Ajouter un Nouveau Graphique

1. Créer une méthode dans `GreenmoveAnalytics` :
```python
def _page_mon_graphique(self, pdf):
    fig = plt.figure(figsize=(11.69, 8.27))
    # Votre code
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
```

2. L'ajouter dans `generer_rapport_pdf()` :
```python
self._page_mon_graphique(pdf)
```

### Ajouter une Nouvelle Statistique

```python
def calculer_statistiques_globales(self):
    # Existant...
    
    # Nouvelle statistique
    self.stats_globales['ma_nouvelle_stat'] = self.df['colonne'].sum()
```

## 📄 Licence et Crédits

Ce projet utilise :
- Python 3
- PostgreSQL
- Pandas, Matplotlib, Seaborn
- psycopg2

---

**Auteur** : [Votre nom]
**Version** : 1.0.0
**Date** : Octobre 2025
