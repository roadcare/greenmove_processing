# Configuration de la base de données Greenmove
# Copiez ce fichier en config.py et remplissez vos informations

DB_CONFIG = {
    # Azure PostgreSQL Configuration
    'host': 'rcp-staging-postgresql-server-12.postgres.database.azure.com',
    'database': 'greenmove',
    'user': 'psqladminun',
    'password': '13264_password_staging_8456512',
    'port': 5432
}

# Options de rapport
RAPPORT_OPTIONS = {
    # Nombre d'utilisateurs à inclure dans les rapports individuels
    'nombre_rapports_individuels': 5,
    
    # Générer l'analyse textuelle
    'generer_analyse_txt': True,
    
    # Générer le rapport PDF global
    'generer_rapport_pdf': True,
    
    # Noms de fichiers de sortie
    'fichier_rapport_global': 'rapport_greenmove_global.pdf',
    'fichier_analyse_txt': 'analyse_greenmove.txt',
}
