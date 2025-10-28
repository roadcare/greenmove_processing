#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'exemple simplifié pour tester rapidement l'analyse Greenmove
"""

from greenmove_reporting import GreenmoveAnalytics

def exemple_simple():
    """Exemple d'utilisation simple"""
    
    # Charger la configuration
    try:
        from config import DB_CONFIG as config
        print("✓ Configuration chargée depuis config.py")
    except ImportError:
        print("⚠️  Fichier config.py non trouvé. Utilisation manuelle.")
        config = {
            'host': input("Hôte PostgreSQL: "),
            'database': input("Base de données: "),
            'user': input("Utilisateur: "),
            'password': input("Mot de passe: "),
            'port': 5432
        }
    
    print("Connexion à la base de données...")
    analytics = GreenmoveAnalytics(**config)
    
    # Charger les données
    if analytics.connect_and_load_data():
        print(f"✓ {len(analytics.df)} trajets chargés")
        
        # Calculer les statistiques
        print("\nCalcul des statistiques...")
        stats = analytics.calculer_statistiques_globales()
        
        # Afficher un résumé
        print("\n" + "="*60)
        print("RÉSUMÉ DES STATISTIQUES")
        print("="*60)
        print(f"Utilisateurs actifs : {stats['nombre_utilisateurs']}")
        print(f"Nombre de trajets : {stats['nombre_trajets']}")
        print(f"Distance totale : {stats['distance_totale']:.1f} km")
        print(f"Émissions CO₂ : {stats['emission_totale']/1000:.1f} kg")
        print("="*60)
        
        # Générer les rapports
        reponse = input("\nGénérer les rapports complets ? (o/n) : ")
        if reponse.lower() == 'o':
            print("\nGénération des rapports...")
            analytics.generer_rapport_pdf()
            analytics.generer_analyse_textuelle()
            print("✓ Rapports générés !")
    else:
        print("✗ Erreur de connexion")

def exemple_utilisateur_specifique():
    """Exemple pour générer un rapport pour un utilisateur spécifique"""
    
    # Charger la configuration
    try:
        from config import DB_CONFIG as config
        print("✓ Configuration chargée depuis config.py")
    except ImportError:
        print("⚠️  Fichier config.py non trouvé")
        config = {
            'host': input("Hôte PostgreSQL: "),
            'database': input("Base de données: "),
            'user': input("Utilisateur: "),
            'password': input("Mot de passe: "),
            'port': 5432
        }
    
    analytics = GreenmoveAnalytics(**config)
    
    if analytics.connect_and_load_data():
        # Afficher les premiers utilisateurs
        print("\nUtilisateurs disponibles (10 premiers) :")
        for i, user in enumerate(analytics.df['utilisateur'].unique()[:10], 1):
            nb_trajets = len(analytics.df[analytics.df['utilisateur'] == user])
            print(f"{i}. {user} ({nb_trajets} trajets)")
        
        # Demander l'utilisateur
        user_id = input("\nEntrez l'ID utilisateur : ")
        analytics.generer_rapport_utilisateur(user_id)

def exemple_statistiques_rapides():
    """Affiche uniquement des statistiques rapides sans générer de PDF"""
    
    # Charger la configuration
    try:
        from config import DB_CONFIG as config
        print("✓ Configuration chargée depuis config.py")
    except ImportError:
        print("⚠️  Fichier config.py non trouvé")
        config = {
            'host': input("Hôte PostgreSQL: "),
            'database': input("Base de données: "),
            'user': input("Utilisateur: "),
            'password': input("Mot de passe: "),
            'port': 5432
        }
    
    analytics = GreenmoveAnalytics(**config)
    
    if analytics.connect_and_load_data():
        stats = analytics.calculer_statistiques_globales()
        
        print("\n" + "="*80)
        print("STATISTIQUES GREENMOVE")
        print("="*80)
        
        print(f"\n📊 Vue d'ensemble")
        print(f"   Période : du {stats['periode_debut'].strftime('%d/%m/%Y')} au {stats['periode_fin'].strftime('%d/%m/%Y')}")
        print(f"   Utilisateurs : {stats['nombre_utilisateurs']:,}")
        print(f"   Trajets : {stats['nombre_trajets']:,}")
        
        print(f"\n🛣️  Distances")
        print(f"   Total : {stats['distance_totale']:,.1f} km")
        print(f"   Moyenne : {stats['distance_moyenne']:.2f} km/trajet")
        
        print(f"\n⏱️  Durées")
        print(f"   Total : {stats['duree_totale']:,.0f} min ({stats['duree_totale']/60:.1f} h)")
        print(f"   Moyenne : {stats['duree_moyenne']:.1f} min/trajet")
        
        print(f"\n🌍 Émissions CO₂")
        print(f"   Total : {stats['emission_totale']/1000:.1f} kg")
        print(f"   Moyenne : {stats['emission_moyenne']:.1f} g/trajet")
        
        print("\n📈 Par mode de transport :")
        mode_stats = analytics.df.groupby('mode_transport').agg({
            'utilisateur': 'count',
            'distance': 'sum',
            'emission_co2': 'sum'
        }).sort_values('utilisateur', ascending=False)
        
        for mode in mode_stats.index:
            nb = mode_stats.loc[mode, 'utilisateur']
            dist = mode_stats.loc[mode, 'distance']
            co2 = mode_stats.loc[mode, 'emission_co2']
            pct = (nb / stats['nombre_trajets']) * 100
            print(f"   {mode:15s} : {nb:6.0f} trajets ({pct:5.1f}%) - {dist:8.1f} km - {co2/1000:6.1f} kg CO₂")
        
        print("="*80)

if __name__ == "__main__":
    print("="*60)
    print("GREENMOVE - EXEMPLES D'UTILISATION")
    print("="*60)
    print("\nChoisissez une option :")
    print("1. Exemple simple (génération complète)")
    print("2. Rapport pour un utilisateur spécifique")
    print("3. Statistiques rapides (sans PDF)")
    print()
    
    choix = input("Votre choix (1-3) : ")
    
    if choix == "1":
        exemple_simple()
    elif choix == "2":
        exemple_utilisateur_specifique()
    elif choix == "3":
        exemple_statistiques_rapides()
    else:
        print("Choix invalide")
