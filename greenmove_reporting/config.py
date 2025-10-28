# Configuration de la base de données Greenmove
# Remplissez vos informations de connexion Azure PostgreSQL ci-dessous

DB_CONFIG = {
    # Hôte Azure PostgreSQL
    # Format: votre-serveur.postgres.database.azure.com
    'host': 'rcp-staging-postgresql-server-12.postgres.database.azure.com',
    
    # Nom de la base de données
    'database': 'greenmove',
    
    # Nom d'utilisateur
    # Format Azure: utilisateur@nom-serveur
    'user': 'psqladminun',
    
    # Mot de passe
    'password': '13264_password_staging_8456512',
    
    # Port PostgreSQL (par défaut 5432)
    'port': 5432
}


# Options de rapport (optionnel)
RAPPORT_OPTIONS = {
    # Nombre d'utilisateurs à inclure dans les rapports individuels
    'nombre_rapports_individuels': 21,
    
    # Générer l'analyse textuelle
    'generer_analyse_txt': True,
    
    # Générer le rapport PDF global
    'generer_rapport_pdf': True,
    
    # Noms de fichiers de sortie
    'fichier_rapport_global': 'rapport_greenmove_global.pdf',
    'fichier_analyse_txt': 'analyse_greenmove.txt',
}

# Seuils d'intensité carbone (g CO₂/km)
SEUILS_INTENSITE_CARBONE = {
    # Objectif recommandé affiché dans les rapports
    'objectif_recommande': 15,  # g CO₂/km
    
    # Seuils pour les niveaux de performance
    'excellent': 15,    # < 15 g/km : EXCELLENT ✨
    'bon': 20,          # 15-50 g/km : BON ✅
    'moyen': 40,       # 50-100 g/km : MOYEN ⚠️
    # > 100 g/km : À AMÉLIORER ❗
}

# ============================================================================
# EXEMPLE DE CONFIGURATION COMPLÉTÉE :
# ============================================================================
# DB_CONFIG = {
#     'host': 'greenmove-db.postgres.database.azure.com',
#     'database': 'greenmove',
#     'user': 'admin@greenmove-db',
#     'password': 'MonMotDePasseSecurise123!',
#     'port': 5432
# }
# =======================================================