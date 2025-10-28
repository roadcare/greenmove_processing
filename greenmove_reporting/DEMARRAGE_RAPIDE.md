# 🚀 Guide de Démarrage Rapide - Greenmove Analytics

## ⚡ Installation Express (5 minutes)

### Étape 1 : Télécharger les fichiers
Téléchargez tous les fichiers du projet dans un dossier, par exemple `greenmove-analytics/`

### Étape 2 : Installer les dépendances Python
```bash
cd greenmove-analytics/
pip install -r requirements.txt
```

### Étape 3 : Configurer la base de données

Ouvrez le fichier `config.py` et remplissez vos informations de connexion Azure PostgreSQL :

```python
DB_CONFIG = {
    'host': 'votre-serveur.postgres.database.azure.com',
    'database': 'greenmove',
    'user': 'votre_utilisateur@votre-serveur',
    'password': 'votre_mot_de_passe',
    'port': 5432
}
```

**Exemple concret :**
```python
DB_CONFIG = {
    'host': 'greenmove-prod.postgres.database.azure.com',
    'database': 'greenmove',
    'user': 'admin@greenmove-prod',
    'password': 'MonMotDePasse123!',
    'port': 5432
}
```

### Étape 4 : Générer les rapports !
```bash
python greenmove_reporting.py
```

C'est tout ! Les rapports seront générés en 2-5 minutes.

---

## 📊 Fichiers Générés

Après exécution, vous obtiendrez :

1. **rapport_greenmove_global.pdf** (6 pages)
   - Vue d'ensemble complète
   - Statistiques par mode de transport
   - Analyses temporelles
   - Émissions CO₂

2. **analyse_greenmove.txt**
   - Analyse textuelle détaillée
   - Recommandations

3. **rapport_utilisateur_*.pdf**
   - Un rapport par utilisateur (top 5)

---

## 🎯 Autres Commandes Utiles

### Statistiques rapides (sans générer de PDF)
```bash
python cli.py --stats
```

### Rapport pour un utilisateur spécifique
```bash
python cli.py --user-id user123
```

### Rapport global uniquement
```bash
python cli.py --global
```

### Top 10 utilisateurs
```bash
python cli.py --users 10
```

---

## ⚙️ Configuration Avancée

### Utiliser des variables d'environnement (plus sécurisé)

**Linux/Mac :**
```bash
export GREENMOVE_DB_HOST="votre-serveur.postgres.database.azure.com"
export GREENMOVE_DB_NAME="greenmove"
export GREENMOVE_DB_USER="votre_utilisateur"
export GREENMOVE_DB_PASSWORD="votre_mot_de_passe"
```

**Windows (PowerShell) :**
```powershell
$env:GREENMOVE_DB_HOST="votre-serveur.postgres.database.azure.com"
$env:GREENMOVE_DB_NAME="greenmove"
$env:GREENMOVE_DB_USER="votre_utilisateur"
$env:GREENMOVE_DB_PASSWORD="votre_mot_de_passe"
```

Puis modifiez `config.py` :
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

---

## 🐛 Résolution des Problèmes Courants

### ❌ ImportError: No module named 'psycopg2'
**Solution :**
```bash
pip install psycopg2-binary
```

### ❌ psycopg2.OperationalError: connection failed
**Causes possibles :**
1. Vérifiez vos identifiants dans `config.py`
2. Vérifiez que votre IP est autorisée dans le pare-feu Azure
3. Format utilisateur : `utilisateur@nom-serveur` (important !)
4. Vérifiez que le serveur PostgreSQL est actif

**Test de connexion :**
```python
import psycopg2
from config import DB_CONFIG

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✓ Connexion réussie !")
    conn.close()
except Exception as e:
    print(f"✗ Erreur : {e}")
```

### ❌ ModuleNotFoundError: No module named 'config'
**Solution :**
Le fichier `config.py` doit être dans le même dossier que les scripts Python.

### ❌ Graphiques vides ou erreurs matplotlib
**Solution :**
```bash
pip install --upgrade matplotlib seaborn
```

---

## 📁 Structure des Fichiers

```
greenmove-analytics/
│
├── config.py                    ← ⚠️ À CONFIGURER EN PREMIER
├── greenmove_reporting.py       ← Script principal
├── cli.py                       ← Interface ligne de commande
├── exemple_utilisation.py       ← Exemples interactifs
│
├── README.md                    ← Documentation complète
├── GUIDE_PROJET.md              ← Guide avancé
├── requirements.txt             ← Dépendances
│
└── Rapports générés :
    ├── rapport_greenmove_global.pdf
    ├── analyse_greenmove.txt
    └── rapport_utilisateur_*.pdf
```

---

## 🔒 Sécurité - Important !

⚠️ **NE JAMAIS** commiter le fichier `config.py` avec vos vrais identifiants !

Le fichier `.gitignore` est configuré pour l'exclure automatiquement.

**Bonnes pratiques :**
- Utilisez des variables d'environnement en production
- Utilisez Azure Key Vault pour les secrets
- Limitez les permissions PostgreSQL (lecture seule si possible)
- Activez SSL pour les connexions PostgreSQL

---

## 📞 Besoin d'Aide ?

1. Consultez le **README.md** pour la documentation complète
2. Consultez le **GUIDE_PROJET.md** pour les cas d'usage avancés
3. Vérifiez que votre pare-feu Azure autorise votre IP
4. Testez la connexion PostgreSQL avec un client comme pgAdmin

---

## ✅ Checklist de Démarrage

- [ ] Python 3.8+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichier `config.py` configuré avec vos identifiants
- [ ] IP autorisée dans le pare-feu Azure PostgreSQL
- [ ] Connexion testée avec succès
- [ ] Premier rapport généré !

---

**Temps total de configuration : 5-10 minutes**  
**Temps de génération des rapports : 2-5 minutes (pour 9000 utilisateurs)**

Bon reporting ! 📊✨
