# 🧪 GUIDE DE TEST RAPIDE

## Test de la Correction v1.2.1

Suivez ces étapes pour vérifier que tout fonctionne correctement après la correction.

---

## ✅ Pré-requis

- [ ] Fichier `greenmove_reporting.py` v1.2.1 téléchargé
- [ ] Fichier `config.py` configuré avec vos identifiants
- [ ] Dépendances installées (`pip install -r requirements.txt`)

---

## 🧪 Tests à Effectuer

### Test 1 : Vérification Basique (30 secondes)
```bash
python cli.py --stats
```

**Résultat attendu :**
```
✓ Configuration chargée depuis config.py
✓ X trajets chargés
[Affichage des statistiques]
```

**Si ça fonctionne :** ✅ Configuration OK, continuez

**Si erreur :** ❌ Vérifiez config.py et connexion base de données

---

### Test 2 : Format HTML (1-2 minutes)
```bash
python cli.py --analyse --format html
```

**Résultat attendu :**
```
Génération de l'analyse avec illustrations (HTML): analyse_greenmove.html
✓ Analyse HTML générée : analyse_greenmove.html
```

**Vérification :**
- [ ] Fichier `analyse_greenmove.html` créé
- [ ] Ouvrir dans navigateur → affichage correct avec graphiques
- [ ] Design moderne avec dégradés et cartes colorées

**Si ça fonctionne :** ✅ Format HTML OK

**Si erreur "unexpected keyword argument 'format'" :** ❌ Téléchargez à nouveau `greenmove_reporting.py` v1.2.1

---

### Test 3 : Format PDF (1-2 minutes)
```bash
python cli.py --global --format pdf
```

**Résultat attendu :**
```
Génération du rapport global (PDF): rapport_greenmove_global.pdf
✓ Rapport généré: rapport_greenmove_global.pdf
```

**Vérification :**
- [ ] Fichier `rapport_greenmove_global.pdf` créé
- [ ] Ouvrir → 6 pages avec graphiques

**Si ça fonctionne :** ✅ Format PDF OK

---

### Test 4 : Les Deux Formats (2-4 minutes)
```bash
python cli.py --analyse --format both
```

**Résultat attendu :**
```
Génération de l'analyse avec illustrations (PDF): analyse_greenmove.pdf
✓ Analyse générée: analyse_greenmove.pdf
Génération de l'analyse avec illustrations (HTML): analyse_greenmove.html
✓ Analyse générée: analyse_greenmove.html
```

**Vérification :**
- [ ] 2 fichiers créés : `.pdf` et `.html`
- [ ] Les deux s'ouvrent correctement
- [ ] Contenu similaire dans les deux formats

**Si ça fonctionne :** ✅ Mode Both OK

---

### Test 5 : Génération Complète (3-6 minutes)
```bash
python cli.py --all --format html
```

**Résultat attendu :**
```
Génération de tous les rapports...
  • Rapport global HTML... ✓
  • Analyse HTML avec illustrations... ✓
  • Analyse textuelle... ✓
  • Rapports utilisateurs (top 5)...
```

**Vérification :**
- [ ] `rapport_greenmove_global.html`
- [ ] `analyse_greenmove.html`
- [ ] `analyse_greenmove.txt`
- [ ] `rapport_utilisateur_*.pdf` (5 fichiers)

**Si ça fonctionne :** ✅ Tout est opérationnel ! 🎉

---

## 🎯 Checklist Finale

Cochez si tous les tests passent :

- [ ] ✅ Test 1 : Statistiques (config OK)
- [ ] ✅ Test 2 : HTML seul
- [ ] ✅ Test 3 : PDF seul
- [ ] ✅ Test 4 : Both
- [ ] ✅ Test 5 : Génération complète

**Si tous les tests passent :** 🎉 **Félicitations ! Tout fonctionne parfaitement.**

---

## ❌ En Cas de Problème

### Erreur : "unexpected keyword argument 'format'"
**Cause :** Ancienne version de `greenmove_reporting.py`

**Solution :**
1. Téléchargez à nouveau `greenmove_reporting.py` v1.2.1
2. Remplacez l'ancien fichier
3. Relancez le test

---

### Erreur : "No module named 'config'"
**Cause :** Fichier `config.py` manquant ou mal placé

**Solution :**
1. Assurez-vous que `config.py` est dans le même dossier que `cli.py`
2. Vérifiez que `config.py` contient `DB_CONFIG = {...}`

---

### Erreur : "Connection refused" ou "Operational Error"
**Cause :** Problème de connexion PostgreSQL

**Solution :**
1. Vérifiez vos identifiants dans `config.py`
2. Vérifiez que votre IP est autorisée dans Azure
3. Format utilisateur : `utilisateur@nom-serveur`
4. Testez avec : `psql` ou pgAdmin

---

### HTML s'affiche mal
**Cause :** Navigateur trop ancien

**Solution :**
1. Utilisez Chrome, Firefox, Safari ou Edge récent
2. Mettez à jour votre navigateur

---

### PDF illisible ou vide
**Cause :** Problème de génération matplotlib

**Solution :**
```bash
pip install --upgrade matplotlib
pip install --upgrade seaborn
```

---

## 📞 Support

Si les tests ne passent pas :
1. Consultez [CORRECTION_v1.2.1.md](computer:///mnt/user-data/outputs/CORRECTION_v1.2.1.md)
2. Vérifiez [FORMAT_HTML_PDF.md](computer:///mnt/user-data/outputs/FORMAT_HTML_PDF.md)
3. Relisez [DEMARRAGE_RAPIDE.md](computer:///mnt/user-data/outputs/DEMARRAGE_RAPIDE.md)

---

## ⏱️ Temps de Test Total

- Test 1 : 30 secondes
- Test 2 : 1-2 minutes
- Test 3 : 1-2 minutes
- Test 4 : 2-4 minutes
- Test 5 : 3-6 minutes

**Total : ~10-15 minutes pour valider complètement**

---

## 🎯 Objectif

À la fin de ces tests, vous devez avoir :

✅ Statistiques affichées correctement  
✅ Rapport HTML moderne et interactif  
✅ Rapport PDF professionnel  
✅ Les deux formats générés simultanément  
✅ Génération complète fonctionnelle  

---

**Version testée :** 1.2.1  
**Date :** 28 Octobre 2025  
**Statut :** ✅ Production Ready
