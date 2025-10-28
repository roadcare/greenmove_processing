#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface en ligne de commande pour Greenmove Analytics
"""

import argparse
import sys
from greenmove_reporting import GreenmoveAnalytics

def main():
    parser = argparse.ArgumentParser(
        description='Greenmove - Génération de rapports d\'analyse',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  
  # Rapport complet en PDF (par défaut)
  python cli.py --all
  
  # Rapport complet en HTML
  python cli.py --all --format html
  
  # Rapport complet en PDF et HTML
  python cli.py --all --format both
  
  # Rapport global en HTML uniquement
  python cli.py --global --format html
  
  # Analyse avec illustrations en PDF
  python cli.py --analyse
  
  # Analyse avec illustrations en HTML
  python cli.py --analyse --format html
  
  # Rapport pour un utilisateur spécifique
  python cli.py --user-id user123
  
  # Statistiques rapides sans générer de fichiers
  python cli.py --stats
  
  # Spécifier la connexion
  python cli.py --host monserveur.com --db greenmove --user admin --all
        """
    )
    
    # Arguments de connexion
    parser.add_argument('--host', 
                       help='Hôte PostgreSQL (ex: serveur.postgres.database.azure.com)')
    parser.add_argument('--db', '--database', 
                       help='Nom de la base de données')
    parser.add_argument('--user', 
                       help='Nom d\'utilisateur PostgreSQL')
    parser.add_argument('--password', 
                       help='Mot de passe (non recommandé, utilisez plutôt config.py)')
    parser.add_argument('--port', type=int, default=5432,
                       help='Port PostgreSQL (défaut: 5432)')
    
    # Types de rapports
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true',
                      help='Générer tous les rapports')
    group.add_argument('--global', dest='global_report', action='store_true',
                      help='Générer uniquement le rapport PDF global')
    group.add_argument('--users', metavar='N', type=int,
                      help='Générer des rapports pour les N utilisateurs les plus actifs')
    group.add_argument('--user-id', dest='user_id',
                      help='Générer un rapport pour un utilisateur spécifique')
    group.add_argument('--text', action='store_true',
                      help='Générer uniquement l\'analyse textuelle')
    group.add_argument('--analyse', '--analysis', action='store_true',
                      help='Générer l\'analyse PDF avec illustrations et recommandations')
    group.add_argument('--stats', action='store_true',
                      help='Afficher uniquement les statistiques (pas de fichier)')
    
    # Options de sortie
    parser.add_argument('--output', '-o',
                       help='Nom du fichier de sortie')
    parser.add_argument('--format', '-f', choices=['pdf', 'html', 'both'], default='pdf',
                       help='Format de sortie : pdf, html, ou both (défaut: pdf)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Mode silencieux')
    
    args = parser.parse_args()
    
    # Charger la configuration
    try:
        from config import DB_CONFIG
        if not args.host:
            config = DB_CONFIG
        else:
            config = {
                'host': args.host,
                'database': args.db,
                'user': args.user,
                'password': args.password,
                'port': args.port
            }
    except ImportError:
        if not all([args.host, args.db, args.user]):
            print("❌ Erreur: Créez un fichier config.py ou spécifiez --host, --db et --user")
            sys.exit(1)
        config = {
            'host': args.host,
            'database': args.db,
            'user': args.user,
            'password': args.password or input("Mot de passe: "),
            'port': args.port
        }
    
    if not args.quiet:
        print("="*60)
        print("GREENMOVE - GÉNÉRATION DE RAPPORTS")
        print("="*60)
        print(f"\nConnexion à {config['host']}...")
    
    # Créer l'instance et charger les données
    analytics = GreenmoveAnalytics(**config)
    
    if not analytics.connect_and_load_data():
        print("❌ Erreur de connexion à la base de données")
        sys.exit(1)
    
    if not args.quiet:
        print(f"✓ {len(analytics.df)} trajets chargés")
        print("Calcul des statistiques...")
    
    stats = analytics.calculer_statistiques_globales()
    
    # Exécuter l'action demandée
    if args.stats:
        # Afficher les statistiques uniquement
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
        
    elif args.global_report:
        # Rapport global uniquement
        formats_list = ['pdf', 'html'] if args.format == 'both' else [args.format]
        for fmt in formats_list:
            ext = 'html' if fmt == 'html' else 'pdf'
            output = args.output or f'rapport_greenmove_global.{ext}'
            if not args.quiet:
                print(f"Génération du rapport global ({fmt.upper()}): {output}")
            analytics.generer_rapport_pdf(output, format=fmt)
            if not args.quiet:
                print(f"✓ Rapport généré: {output}")
    
    elif args.text:
        # Analyse textuelle uniquement
        output = args.output or 'analyse_greenmove.txt'
        if not args.quiet:
            print(f"Génération de l'analyse textuelle: {output}")
        analytics.generer_analyse_textuelle(output)
        if not args.quiet:
            print(f"✓ Analyse générée: {output}")
    
    elif args.analyse:
        # Analyse PDF/HTML avec illustrations
        formats_list = ['pdf', 'html'] if args.format == 'both' else [args.format]
        for fmt in formats_list:
            ext = 'html' if fmt == 'html' else 'pdf'
            output = args.output or f'analyse_greenmove.{ext}'
            if not args.quiet:
                print(f"Génération de l'analyse avec illustrations ({fmt.upper()}): {output}")
            analytics.generer_analyse_pdf(output, format=fmt)
            if not args.quiet:
                print(f"✓ Analyse générée: {output}")
    
    elif args.user_id:
        # Rapport pour un utilisateur spécifique
        output = args.output or f'rapport_utilisateur_{args.user_id}.pdf'
        if not args.quiet:
            print(f"Génération du rapport utilisateur: {output}")
        analytics.generer_rapport_utilisateur(args.user_id, output)
        if not args.quiet:
            print(f"✓ Rapport utilisateur généré: {output}")
    
    elif args.users:
        # Rapports pour les N utilisateurs les plus actifs
        if not args.quiet:
            print(f"Génération de {args.users} rapports utilisateurs...")
        top_users = analytics.df['utilisateur'].value_counts().head(args.users).index
        for i, user in enumerate(top_users, 1):
            if not args.quiet:
                print(f"  [{i}/{args.users}] {user}...", end=' ')
            analytics.generer_rapport_utilisateur(user)
            if not args.quiet:
                print("✓")
        if not args.quiet:
            print(f"✓ {args.users} rapports générés")
    
    elif args.all:
        # Tous les rapports
        if not args.quiet:
            print("Génération de tous les rapports...")
        
        formats_list = ['pdf', 'html'] if args.format == 'both' else [args.format]
        
        # Rapport global
        for fmt in formats_list:
            ext = 'html' if fmt == 'html' else 'pdf'
            if not args.quiet:
                print(f"  • Rapport global {fmt.upper()}...", end=' ')
            analytics.generer_rapport_pdf(f'rapport_greenmove_global.{ext}', format=fmt)
            if not args.quiet:
                print("✓")
        
        # Analyse avec illustrations
        for fmt in formats_list:
            ext = 'html' if fmt == 'html' else 'pdf'
            if not args.quiet:
                print(f"  • Analyse {fmt.upper()} avec illustrations...", end=' ')
            analytics.generer_analyse_pdf(f'analyse_greenmove.{ext}', format=fmt)
            if not args.quiet:
                print("✓")
        
        # Analyse textuelle
        if not args.quiet:
            print("  • Analyse textuelle...", end=' ')
        analytics.generer_analyse_textuelle()
        if not args.quiet:
            print("✓")
        
        # Rapports utilisateurs (top 5)
        if not args.quiet:
            print("  • Rapports utilisateurs (top 5)...")
        top_users = analytics.df['utilisateur'].value_counts().head(5).index
        for i, user in enumerate(top_users, 1):
            if not args.quiet:
                print(f"    [{i}/5] {user}...", end=' ')
            analytics.generer_rapport_utilisateur(user)
            if not args.quiet:
                print("✓")
    
    if not args.quiet:
        print("\n" + "="*60)
        print("✅ TERMINÉ")
        print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
