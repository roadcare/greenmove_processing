# 📦 GREENMOVE ANALYTICS - Package Complet

**Version :** 1.0.0  
**Date :** 28 Octobre 2025  
**Pour :** 9000 utilisateurs Greenmove

---

## ✅ Fichiers Livrés (9 fichiers)

### 🔧 Configuration

| Fichier | Description |
|---------|-------------|
| **config.py** | ⚠️ **FICHIER PRINCIPAL À CONFIGURER** - Ajoutez vos identifiants Azure PostgreSQL |
| config_template.py | Template de configuration (pour référence) |
| .gitignore | Protection des fichiers sensibles |

### 🐍 Scripts Python

| Fichier | Description | Utilisation |
|---------|-------------|-------------|
| **greenmove_reporting.py** | Script principal (33 KB) | `python greenmove_reporting.py` |
| **cli.py** | Interface en ligne de commande | `python cli.py --all` |
| exemple_utilisation.py | Exemples interactifs | `python exemple_utilisation.py` |

### 📚 Documentation

| Fichier | Description |
|---------|-------------|
| **DEMARRAGE_RAPIDE.md** | ⭐ **COMMENCEZ ICI** - Guide en 5 minutes |
| README.md | Documentation complète |
| GUIDE_PROJET.md | Guide avancé (cas d'usage, optimisation) |
| requirements.txt | Dépendances Python |

---

## 🚀 Démarrage en 3 Étapes

### 1️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2️⃣ Configurer config.py
Ouvrez `config.py` et remplissez :
```python
DB_CONFIG = {
    'host': 'VOTRE_SERVEUR.postgres.database.azure.com',
    'database': 'greenmove',
    'user': 'VOTRE_UTILISATEUR@VOTRE_SERVEUR',
    'password': 'VOTRE_MOT_DE_PASSE',
    'port': 5432
}
```

### 3️⃣ Générer les rapports
```bash
python greenmove_reporting.py
```

---

## 📊 Rapports Générés

Le programme génère automatiquement :

### 1. Rapport PDF Global (6 pages)
**Fichier :** `rapport_greenmove_global.pdf`

**Contenu :**
- **Page 1 :** Vue d'ensemble (statistiques générales, répartition des modes)
- **Page 2 :** Analyse détaillée par mode de transport
- **Page 3 :** Distribution des distances (histogrammes, boîtes à moustaches)
- **Page 4 :** Analyse temporelle (évolution, heatmap jour/heure)
- **Page 5 :** Émissions CO₂ (répartition, intensité carbone)
- **Page 6 :** Top utilisateurs (plus actifs, plus grandes distances)

### 2. Analyse Textuelle
**Fichier :** `analyse_greenmove.txt`

**Contenu :**
- Statistiques détaillées par mode
- Impact environnemental avec équivalences
- Recommandations personnalisées

### 3. Rapports Individuels (Top 5)
**Fichiers :** `rapport_utilisateur_*.pdf`

**Contenu :**
- Statistiques personnelles
- Modes de transport utilisés
- Évolution temporelle

---

## 📈 Statistiques Générées

### Indicateurs Globaux
✓ Nombre d'utilisateurs actifs  
✓ Nombre total de trajets  
✓ Distance totale et moyenne  
✓ Durée totale et moyenne  
✓ Émissions CO₂ totales et moyennes  

### Par Mode de Transport
✓ Nombre de trajets  
✓ Distance (totale, moyenne)  
✓ Durée moyenne  
✓ Émissions CO₂ (totales, moyennes)  
✓ Intensité carbone (g CO₂/km)  
✓ Vitesse moyenne (km/h)  

### Analyses Temporelles
✓ Trajets par jour/semaine/heure  
✓ Heatmap jour × heure  
✓ Évolution dans le temps  

### Analyses Environnementales
✓ Répartition des émissions  
✓ Intensité carbone par mode  
✓ Équivalences (vols, arbres, etc.)  

---

## 🎯 Commandes Utiles

```bash
# Rapport complet (PDF + TXT + rapports utilisateurs)
python greenmove_reporting.py

# Statistiques rapides sans PDF
python cli.py --stats

# Rapport global uniquement
python cli.py --global

# Rapport pour un utilisateur
python cli.py --user-id user123

# Top 10 utilisateurs
python cli.py --users 10

# Exemples interactifs
python exemple_utilisation.py
```

---

## 🎨 Graphiques Inclus

Le rapport PDF contient 25+ graphiques :

### Camemberts (Pie Charts)
- Répartition des modes de transport
- Part modale en distance
- Répartition des émissions CO₂

### Graphiques à Barres
- Nombre de trajets par mode
- Distance par mode
- Émissions par mode
- Intensité carbone
- Trajets par jour de la semaine

### Histogrammes
- Distribution globale des distances
- Distribution des émissions

### Boîtes à Moustaches (Box Plots)
- Distribution des distances par mode

### Graphiques Temporels
- Évolution du nombre de trajets
- Émissions cumulées
- Évolution par utilisateur

### Heatmaps
- Trajets par jour et heure

### Scatter Plots
- Distance vs Émissions par mode

---

## ⚙️ Configuration Requise

### Logiciels
- Python 3.8 ou supérieur
- PostgreSQL 12+ (Azure)
- Connexion Internet

### Bibliothèques Python
- psycopg2-binary (connexion PostgreSQL)
- pandas (manipulation de données)
- matplotlib (graphiques)
- seaborn (visualisations avancées)
- numpy (calculs numériques)

### Base de Données
- Table : `tripanalyse.usagestat`
- Champs requis : utilisateur, startTime, mode_transport, distance, duration_in_minutes, emission_co2

---

## ⏱️ Temps d'Exécution

Pour 9000 utilisateurs :

| Opération | Durée |
|-----------|-------|
| Chargement données | 10-30 sec |
| Calcul statistiques | 5-10 sec |
| Rapport PDF global | 30-60 sec |
| Rapports utilisateurs (×5) | 10-25 sec |
| Analyse textuelle | 1-2 sec |
| **TOTAL** | **2-5 minutes** |

---

## 🔒 Sécurité

⚠️ **IMPORTANT :** Le fichier `config.py` contient vos mots de passe !

### Protection
- ✅ `config.py` est dans `.gitignore` (ne sera pas commité)
- ✅ Utilisez des variables d'environnement en production
- ✅ Utilisez Azure Key Vault pour les secrets
- ✅ Limitez les permissions PostgreSQL

### Bonnes Pratiques
```python
# Dans config.py - Production
import os

DB_CONFIG = {
    'host': os.getenv('GREENMOVE_DB_HOST'),
    'database': os.getenv('GREENMOVE_DB_NAME'),
    'user': os.getenv('GREENMOVE_DB_USER'),
    'password': os.getenv('GREENMOVE_DB_PASSWORD'),
    'port': 5432
}
```

---

## 🐛 Dépannage

### Problème : "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Problème : "Connection refused"
1. Vérifiez vos identifiants dans `config.py`
2. Autorisez votre IP dans le pare-feu Azure
3. Format utilisateur : `utilisateur@nom-serveur`

### Problème : "No module named 'config'"
Le fichier `config.py` doit être dans le même dossier.

---

## 📞 Support

- **Documentation :** README.md (complète)
- **Guide rapide :** DEMARRAGE_RAPIDE.md
- **Guide avancé :** GUIDE_PROJET.md

---

## 🎓 Exemples d'Usage

### Usage Simple
```python
from greenmove_reporting import GreenmoveAnalytics
from config import DB_CONFIG

analytics = GreenmoveAnalytics(**DB_CONFIG)
analytics.connect_and_load_data()
analytics.calculer_statistiques_globales()
analytics.generer_rapport_pdf()
```

### Rapport Personnalisé
```python
# Filtrer les données
analytics.df = analytics.df[analytics.df['distance'] > 10]

# Générer le rapport
analytics.generer_rapport_pdf('trajets_longue_distance.pdf')
```

---

## 📝 Licence

[Votre licence ici]

---

## ✨ Fonctionnalités

✅ Statistiques complètes sur 9000 utilisateurs  
✅ 25+ graphiques professionnels  
✅ Analyses en français  
✅ Rapports PDF multi-pages  
✅ Analyses textuelles avec recommandations  
✅ Rapports individuels par utilisateur  
✅ Interface en ligne de commande  
✅ Configuration via fichier config.py  
✅ Support Azure PostgreSQL  
✅ Optimisé pour grandes bases de données  

---

**Temps de configuration : 5 minutes**  
**Temps de génération : 2-5 minutes**  
**Prêt à l'emploi !** 🚀

Pour commencer : Ouvrez **DEMARRAGE_RAPIDE.md** 👈
