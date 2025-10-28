# 📊 NOUVELLE FONCTIONNALITÉ : Analyse PDF avec Illustrations

## 🎉 Qu'est-ce que c'est ?

Une **nouvelle fonctionnalité** a été ajoutée pour générer un rapport d'analyse complet en format PDF avec des **illustrations visuelles** et des **recommandations détaillées**.

Ce rapport complète le rapport global existant en fournissant une **analyse approfondie** avec des insights stratégiques.

---

## 📄 Contenu du Rapport d'Analyse (4 pages)

### Page 1 : Résumé Exécutif avec KPIs
**Objectif :** Vue d'ensemble des indicateurs clés de performance

**Contenu :**
- 📊 **Tableau de bord KPIs** avec tous les indicateurs principaux :
  - Utilisateurs actifs et nombre de trajets
  - Distances totales et moyennes
  - Durées de déplacement
  - Impact environnemental (CO₂)
  - Équivalences (tours de la Terre, etc.)

- 🥧 **Graphiques visuels :**
  - Répartition modale (camembert)
  - Top 3 des modes de transport
  - Intensité carbone par mode (code couleur)
  - Indicateur global de performance (avec niveau : Excellent/Bon/Moyen/À améliorer)

### Page 2 : Analyse Détaillée des Modes de Transport
**Objectif :** Comparaison approfondie de chaque mode

**Contenu :**
- 📋 **Tableau récapitulatif** pour chaque mode :
  - Nombre de trajets
  - Distance (totale et moyenne)
  - Durée moyenne
  - Émissions CO₂
  - Intensité carbone (g CO₂/km)

- 📊 **Graphiques comparatifs :**
  - Distance vs Émissions (scatter plot)
  - Part modale en distance
  - Efficacité énergétique (vitesse vs émissions)

- 💡 **Recommandations ciblées :**
  - Priorités d'action
  - Opportunités d'amélioration
  - Mode le plus écologique à promouvoir

### Page 3 : Impact Environnemental et Recommandations
**Objectif :** Bilan carbone et plan d'action

**Contenu :**
- 🌍 **Bilan carbone global :**
  - Émissions totales (kg, tonnes)
  - Par utilisateur
  - Par trajet
  - Intensité moyenne

- 📈 **Visualisations :**
  - Équivalences environnementales (vols, trajets TGV, kg de bœuf, arbres)
  - Évolution cumulative des émissions dans le temps
  - Répartition des émissions (donut chart)

- 📋 **Plan d'action complet :**
  - Objectifs chiffrés (ex: -20% d'émissions en 6 mois)
  - 4 axes d'actions prioritaires :
    1. Promotion des modes doux
    2. Optimisation des déplacements
    3. Suivi et mesure
    4. Formation et accompagnement
  - Indicateurs de succès

### Page 4 : Analyse Comportementale des Utilisateurs
**Objectif :** Comprendre les profils et comportements

**Contenu :**
- 👥 **Segmentation des utilisateurs :**
  - Très actifs (>50 trajets)
  - Actifs (20-50 trajets)
  - Moyens (10-19 trajets)
  - Occasionnels (<10 trajets)

- 📊 **Analyses visuelles :**
  - Pie chart de répartition des profils
  - Distribution de l'activité (histogramme)
  - Top 10 émetteurs CO₂
  - Heatmap des préférences modales par segment

- 💡 **Insights comportementaux :**
  - Observations clés
  - Actions ciblées par segment
  - Stratégies de réengagement

---

## 🚀 Comment l'Utiliser ?

### Méthode 1 : Script Principal
```bash
python greenmove_reporting.py
```
→ Génère automatiquement `analyse_greenmove.pdf`

### Méthode 2 : Interface en Ligne de Commande
```bash
# Générer uniquement l'analyse PDF
python cli.py --analyse

# Avec un nom personnalisé
python cli.py --analyse --output mon_analyse.pdf

# Tout générer (rapport global + analyse + rapports utilisateurs)
python cli.py --all
```

### Méthode 3 : Dans Votre Code Python
```python
from greenmove_reporting import GreenmoveAnalytics
from config import DB_CONFIG

analytics = GreenmoveAnalytics(**DB_CONFIG)
analytics.connect_and_load_data()
analytics.calculer_statistiques_globales()

# Générer l'analyse PDF
analytics.generer_analyse_pdf('mon_analyse.pdf')
```

---

## 📦 Fichiers Générés Maintenant

Après l'exécution complète, vous obtiendrez **3 types de rapports** :

| Fichier | Description | Pages | Utilisation |
|---------|-------------|-------|-------------|
| **rapport_greenmove_global.pdf** | Rapport statistique complet | 6 | Statistiques détaillées, graphiques multiples |
| **analyse_greenmove.pdf** | 🆕 Analyse stratégique | 4 | KPIs, recommandations, plan d'action |
| **analyse_greenmove.txt** | Analyse textuelle | - | Format texte pour scripts/emails |
| **rapport_utilisateur_*.pdf** | Rapports individuels | 1/user | Feedback personnalisé |

---

## 🎯 Cas d'Usage

### 1. Présentation à la Direction
Utilisez `analyse_greenmove.pdf` :
- Résumé exécutif avec KPIs
- Plan d'action clair
- Indicateurs de succès

### 2. Reporting Mensuel
Générez les 2 PDF :
- `rapport_greenmove_global.pdf` pour les détails
- `analyse_greenmove.pdf` pour les décisions

### 3. Sensibilisation des Équipes
Utilisez l'analyse comportementale :
- Segmentation des profils
- Actions ciblées par segment

---

## 🆚 Différence entre les Rapports

### Rapport Global (rapport_greenmove_global.pdf)
✅ **Focus :** Statistiques et données  
✅ **Contenu :** 25+ graphiques détaillés  
✅ **Audience :** Analystes, data scientists  
✅ **Utilisation :** Analyse approfondie

### Analyse Stratégique (analyse_greenmove.pdf) 🆕
✅ **Focus :** Insights et recommandations  
✅ **Contenu :** KPIs + Plan d'action  
✅ **Audience :** Direction, managers  
✅ **Utilisation :** Prise de décision

### Analyse Textuelle (analyse_greenmove.txt)
✅ **Focus :** Texte pur  
✅ **Contenu :** Statistiques + Recommandations  
✅ **Audience :** Scripts, emails  
✅ **Utilisation :** Automatisation

---

## 🎨 Caractéristiques Visuelles

### Codes Couleur
- 🟢 **Vert** : Performance excellente (< 50 g CO₂/km)
- 🟡 **Orange** : Performance moyenne (50-150 g CO₂/km)
- 🔴 **Rouge** : À améliorer (> 150 g CO₂/km)

### Emojis et Symboles
- 🌟 Excellent
- ✅ Bon
- ⚠️ Moyen
- ❗ À améliorer

### Mise en Forme
- Encadrés ASCII pour les sections importantes
- Tableaux récapitulatifs clairs
- Graphiques professionnels avec légendes
- Code couleur cohérent

---

## 📊 Exemples de KPIs Affichés

### Indicateurs Globaux
```
👥 Utilisateurs actifs : 9,000
🚶 Trajets enregistrés : 125,000
🛣️  Distance totale : 1,250,000 km
⏱️  Durée totale : 750,000 minutes
🌱 Émissions CO₂ : 185,000 kg
```

### Indicateur de Performance
```
╔═══════════════════════════╗
║  INDICATEUR GLOBAL        ║
╚═══════════════════════════╝

Intensité Carbone Moyenne
148.0 g CO₂/km

⚠️ Niveau : MOYEN

Objectif recommandé :
< 100 g CO₂/km
```

---

## 💡 Nouveautés par Rapport à la Version Précédente

| Fonctionnalité | Avant | Maintenant |
|----------------|-------|------------|
| Analyse PDF | ❌ Non | ✅ Oui (4 pages) |
| Résumé exécutif | ❌ Non | ✅ Oui avec KPIs |
| Plan d'action | ❌ Non | ✅ Oui détaillé |
| Segmentation utilisateurs | ❌ Non | ✅ Oui (4 segments) |
| Recommandations ciblées | ⚠️ Basique | ✅ Avancées |
| Indicateur global | ❌ Non | ✅ Oui avec niveau |
| Heatmap préférences | ❌ Non | ✅ Oui |

---

## ⏱️ Temps d'Exécution

Pour 9000 utilisateurs :

| Opération | Durée |
|-----------|-------|
| Rapport global | 30-60 sec |
| **Analyse PDF** 🆕 | **20-40 sec** |
| Analyse textuelle | 1-2 sec |
| **TOTAL** | **3-6 minutes** |

---

## 🔧 Personnalisation

### Modifier les Seuils de Segmentation
Dans `_page_analyse_comportementale()` :
```python
segments = {
    'Très actifs (>50 trajets)': len(trajets_par_user[trajets_par_user > 50]),
    'Actifs (20-50)': len(trajets_par_user[(trajets_par_user >= 20) & ...]),
    # Ajustez les valeurs selon vos besoins
}
```

### Modifier les Seuils d'Intensité Carbone
Dans `_page_analyse_resume_executif()` :
```python
if intensite_globale < 80:  # Changez 80
    niveau = "EXCELLENT"
elif intensite_globale < 120:  # Changez 120
    niveau = "BON"
# etc.
```

---

## 📞 Support

Pour toute question sur cette nouvelle fonctionnalité :
1. Consultez le **README.md** pour la documentation complète
2. Consultez le **GUIDE_PROJET.md** pour les cas d'usage avancés

---

## ✨ Résumé

✅ **4 nouvelles pages** d'analyse stratégique  
✅ **KPIs visuels** avec indicateurs de performance  
✅ **Plan d'action détaillé** avec objectifs chiffrés  
✅ **Segmentation utilisateurs** en 4 profils  
✅ **Recommandations ciblées** par mode et segment  
✅ **Visualisations avancées** (heatmaps, donut charts, scatter plots)  
✅ **Génération automatique** avec le script principal  
✅ **Interface CLI** avec option `--analyse`  

**Temps d'exécution : +20-40 secondes** pour un rapport d'analyse complet ! 🚀

---

**Version :** 1.1.0  
**Ajouté le :** 28 Octobre 2025
