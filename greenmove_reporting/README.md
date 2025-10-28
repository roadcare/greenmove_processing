# Greenmove - Rapport d'Analyse des Déplacements

## 📋 Description

Ce programme Python génère des rapports d'analyse complets pour l'application Greenmove, incluant :
- Des statistiques globales sur tous les utilisateurs
- Des analyses détaillées par mode de transport
- Des visualisations graphiques (PDF)
- Des analyses textuelles
- Des rapports individuels par utilisateur

## 🔧 Prérequis

### Logiciels requis
- Python 3.8 ou supérieur
- PostgreSQL 12 ou supérieur
- Accès à la base de données Azure PostgreSQL Greenmove

### Bibliothèques Python
```bash
pip install psycopg2-binary pandas matplotlib seaborn numpy
```

## 📦 Installation

1. **Cloner ou télécharger les fichiers**
   ```bash
   git clone [votre-repo]
   cd greenmove-reporting
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer la connexion à la base de données**
   ```bash
   cp config_template.py config.py
   ```
   
   Éditer `config.py` avec vos informations de connexion :
   ```python
   DB_CONFIG = {
       'host': 'votre-serveur.postgres.database.azure.com',
       'database': 'greenmove',
       'user': 'votre_utilisateur@votre-serveur',
       'password': 'votre_mot_de_passe',
       'port': 5432
   }
   ```

## 🚀 Utilisation

### Génération complète des rapports

```bash
python greenmove_reporting.py
```

Cette commande génère :
- `rapport_greenmove_global.pdf` : Rapport complet avec graphiques (6 pages)
- `analyse_greenmove.txt` : Analyse textuelle détaillée
- `rapport_utilisateur_*.pdf` : Rapports individuels pour les utilisateurs les plus actifs

### Utilisation avancée (en Python)

```python
from greenmove_reporting import GreenmoveAnalytics

# Créer l'instance
analytics = GreenmoveAnalytics(
    host='votre-serveur.postgres.database.azure.com',
    database='greenmove',
    user='votre_user',
    password='votre_password'
)

# Charger les données
analytics.connect_and_load_data()

# Calculer les statistiques
analytics.calculer_statistiques_globales()

# Générer le rapport PDF global
analytics.generer_rapport_pdf('mon_rapport.pdf')

# Générer un rapport pour un utilisateur spécifique
analytics.generer_rapport_utilisateur('user123', 'rapport_user123.pdf')

# Générer l'analyse textuelle
analytics.generer_analyse_textuelle('mon_analyse.txt')
```

## 📊 Contenu des Rapports

### Rapport PDF Global (6 pages)

**Page 1 : Vue d'ensemble**
- Statistiques générales (utilisateurs, trajets, distances, durées, émissions)
- Répartition des modes de transport
- Nombre de trajets par mode
- Distance et émissions par mode

**Page 2 : Analyse par mode de transport**
- Distance moyenne vs émissions moyennes
- Intensité carbone par mode (g CO₂/km)
- Vitesse moyenne par mode
- Part modale en distance

**Page 3 : Distribution des distances**
- Histogramme global des distances
- Boîtes à moustaches par mode
- Répartition par catégorie (<1km, 1-5km, 5-10km, etc.)
- Distribution cumulative

**Page 4 : Analyse temporelle**
- Évolution du nombre de trajets par jour
- Trajets par jour de la semaine
- Trajets par heure de la journée
- Heatmap jour/heure

**Page 5 : Analyse des émissions CO₂**
- Répartition des émissions par mode
- Évolution cumulative des émissions
- Distribution des émissions par trajet
- Intensité carbone avec code couleur

**Page 6 : Analyse des utilisateurs**
- Top 10 utilisateurs les plus actifs
- Top 10 plus grandes distances
- Top 10 plus grandes émissions
- Distribution de l'activité

### Analyse Textuelle

- Vue d'ensemble avec statistiques clés
- Analyse détaillée par mode de transport
- Impact environnemental avec équivalences
- Recommandations personnalisées

### Rapports Individuels

- Statistiques personnelles
- Modes de transport utilisés
- Distance et émissions par mode
- Évolution temporelle des trajets

## 📈 Indicateurs Calculés

### Indicateurs globaux
- Nombre d'utilisateurs actifs
- Nombre total de trajets
- Distance totale et moyenne
- Durée totale et moyenne
- Émissions CO₂ totales et moyennes

### Indicateurs par mode de transport
- Nombre de trajets
- Distance totale et moyenne
- Durée moyenne
- Émissions totales et moyennes
- Intensité carbone (g CO₂/km)
- Vitesse moyenne (km/h)

### Analyses temporelles
- Trajets par jour
- Trajets par jour de la semaine
- Trajets par heure
- Heatmap jour/heure

### Analyses environnementales
- Répartition des émissions par mode
- Évolution cumulative des émissions
- Intensité carbone par mode
- Équivalences environnementales

## 🎨 Personnalisation

### Modifier les couleurs des graphiques

Dans `greenmove_reporting.py`, section configuration de style :
```python
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")  # Changer la palette de couleurs
```

### Modifier le nombre de rapports individuels

Dans la fonction `main()` :
```python
top_users = analytics.df['utilisateur'].value_counts().head(10).index
```

### Ajouter des graphiques personnalisés

Créer une nouvelle méthode dans la classe `GreenmoveAnalytics` :
```python
def _page_mon_analyse(self, pdf):
    fig = plt.figure(figsize=(11.69, 8.27))
    # Votre code de visualisation
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
```

## 🐛 Résolution de problèmes

### Erreur de connexion PostgreSQL

**Problème :** `psycopg2.OperationalError`

**Solution :**
1. Vérifier que votre IP est autorisée dans Azure
2. Vérifier les identifiants de connexion
3. Vérifier que le pare-feu Azure autorise votre IP
4. Utiliser le format complet : `utilisateur@serveur`

### Erreur "No module named 'psycopg2'"

**Solution :**
```bash
pip install psycopg2-binary
```

### Graphiques illisibles

**Solution :**
Augmenter la taille des figures dans `plt.rcParams['figure.figsize']`

### Mémoire insuffisante

**Solution :**
Pour de très grandes bases de données, charger les données par lots :
```python
query = """
    SELECT * FROM tripanalyse.usagestat
    WHERE "startTime" >= '2024-01-01'
    LIMIT 100000
"""
```

## 📝 Structure des données

### Table tripanalyse.usagestat

| Champ | Type | Description |
|-------|------|-------------|
| utilisateur | VARCHAR | Identifiant de l'utilisateur |
| startTime | TIMESTAMP | Date/heure de début du trajet |
| mode_transport | TEXT | Mode de transport (walking, bicycle, car, train, etc.) |
| distance | NUMERIC | Distance en kilomètres |
| duration_in_minutes | DOUBLE | Durée en minutes |
| emission_co2 | NUMERIC | Émissions en grammes de CO₂ |

## 🔒 Sécurité

### Bonnes pratiques

1. **Ne jamais commiter le fichier config.py**
   - Ajouter `config.py` au `.gitignore`

2. **Utiliser des variables d'environnement**
   ```python
   import os
   DB_CONFIG = {
       'host': os.getenv('DB_HOST'),
       'user': os.getenv('DB_USER'),
       'password': os.getenv('DB_PASSWORD')
   }
   ```

3. **Utiliser Azure Key Vault**
   Pour la production, stockez les secrets dans Azure Key Vault

## 📞 Support

Pour toute question ou problème :
- Documentation PostgreSQL : https://www.postgresql.org/docs/
- Documentation Pandas : https://pandas.pydata.org/docs/
- Documentation Matplotlib : https://matplotlib.org/stable/index.html

## 📄 Licence

[Votre licence]

## 👥 Contributeurs

[Liste des contributeurs]

## 🔄 Changelog

### Version 1.0.0 (Date)
- Génération de rapports PDF avec graphiques
- Analyse textuelle détaillée
- Rapports individuels par utilisateur
- Analyses temporelles et environnementales

---

**Note :** Ce programme nécessite environ 2-5 minutes pour générer tous les rapports pour 9000 utilisateurs et leurs trajets.
