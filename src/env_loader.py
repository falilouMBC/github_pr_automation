#!/usr/bin/env python3
"""
Environment Loader Module
=========================

Charge les variables d'environnement depuis un fichier .env

Ce module permet de charger automatiquement les variables d'environnement
depuis un fichier .env sans dépendance externe (python-dotenv).

Fonctionnalités:
- Lecture du fichier .env
- Parsing des variables
- Support des commentaires
- Support des lignes vides
- Export dans os.environ
"""

import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(env_file: str = '.env') -> Dict[str, str]:
    """
    Charge les variables depuis un fichier .env
    
    Args:
        env_file: Chemin vers le fichier .env
    
    Returns:
        Dictionnaire des variables chargées
    
    Example:
        >>> variables = load_env_file('.env')
        >>> print(variables['GITHUB_TOKEN'])
    """
    env_path = Path(env_file)
    variables = {}
    
    if not env_path.exists():
        return variables
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Supprimer les espaces
                line = line.strip()
                
                # Ignorer les lignes vides et les commentaires
                if not line or line.startswith('#'):
                    continue
                
                # Chercher le séparateur '='
                if '=' not in line:
                    continue
                
                # Séparer clé et valeur
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Supprimer les guillemets si présents
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                variables[key] = value
        
        return variables
    
    except Exception as e:
        print(f"⚠️  Erreur lors du chargement de {env_file}: {e}")
        return {}


def load_dotenv(env_file: str = '.env', override: bool = True) -> bool:
    """
    Charge le fichier .env dans os.environ
    
    Similaire à python-dotenv mais sans dépendance externe.
    
    Args:
        env_file: Chemin vers le fichier .env
        override: Si True, écrase les variables existantes
    
    Returns:
        True si le fichier a été chargé, False sinon
    
    Example:
        >>> load_dotenv()
        >>> token = os.getenv('GITHUB_TOKEN')
    """
    variables = load_env_file(env_file)
    
    if not variables:
        return False
    
    for key, value in variables.items():
        # Ne pas écraser si override est False et la variable existe déjà
        if not override and key in os.environ:
            continue
        
        os.environ[key] = value
    
    return True


def get_env_vars(prefix: str = '') -> Dict[str, str]:
    """
    Récupère toutes les variables d'environnement avec un préfixe
    
    Args:
        prefix: Préfixe des variables à récupérer
    
    Returns:
        Dictionnaire des variables
    
    Example:
        >>> github_vars = get_env_vars('GITHUB_')
        >>> print(github_vars)
        {'GITHUB_TOKEN': 'ghp_...', 'GITHUB_USERNAME': 'user'}
    """
    if prefix:
        return {
            key: value 
            for key, value in os.environ.items() 
            if key.startswith(prefix)
        }
    
    return dict(os.environ)


def check_required_env_vars(required_vars: list[str]) -> tuple[bool, list[str]]:
    """
    Vérifie que les variables requises sont présentes
    
    Args:
        required_vars: Liste des variables requises
    
    Returns:
        Tuple (all_present, missing_vars)
    
    Example:
        >>> is_valid, missing = check_required_env_vars(['GITHUB_TOKEN', 'GITHUB_USERNAME'])
        >>> if not is_valid:
        ...     print(f"Variables manquantes: {missing}")
    """
    missing = [var for var in required_vars if not os.getenv(var)]
    return len(missing) == 0, missing


def find_dotenv(filename: str = '.env', start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Cherche un fichier .env en remontant l'arborescence
    
    Args:
        filename: Nom du fichier à chercher
        start_dir: Répertoire de départ (défaut: répertoire courant)
    
    Returns:
        Chemin vers le fichier trouvé ou None
    
    Example:
        >>> env_path = find_dotenv()
        >>> if env_path:
        ...     load_dotenv(str(env_path))
    """
    if start_dir is None:
        start_dir = Path.cwd()
    
    current = Path(start_dir).resolve()
    
    # Remonter jusqu'à la racine
    while True:
        env_file = current / filename
        
        if env_file.exists():
            return env_file
        
        # Si on est à la racine, arrêter
        parent = current.parent
        if parent == current:
            break
        
        current = parent
    
    return None


def display_env_info():
    """
    Affiche les informations sur les variables d'environnement chargées
    """
    github_vars = get_env_vars('GITHUB_')
    
    print("\n" + "=" * 60)
    print("🔐 VARIABLES D'ENVIRONNEMENT GITHUB")
    print("=" * 60)
    
    if not github_vars:
        print("❌ Aucune variable GITHUB_* trouvée")
        print("\n💡 Assurez-vous d'avoir un fichier .env avec:")
        print("   GITHUB_TOKEN=ghp_...")
        print("   GITHUB_USERNAME=votre_username")
    else:
        for key, value in github_vars.items():
            # Masquer les tokens
            if 'TOKEN' in key and value:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            
            status = "✅" if value else "❌"
            print(f"{status} {key:<25} : {display_value}")
    
    print("=" * 60 + "\n")


def create_env_template(output_file: str = '.env'):
    """
    Crée un fichier .env template
    
    Args:
        output_file: Chemin du fichier à créer
    """
    template = """# ============================================================================
# Variables d'Environnement - GitHub Stats Automation
# ============================================================================
#
# Remplissez vos valeurs ci-dessous
#
# ============================================================================

# Token d'authentification GitHub
# Créez-en un sur: https://github.com/settings/tokens
# Permissions: repo (full), user (read)
GITHUB_TOKEN=

# Votre nom d'utilisateur GitHub
GITHUB_USERNAME=

# Optionnel: Configuration avancée
# CACHE_ENABLED=true
# LOG_LEVEL=INFO
"""
    
    output_path = Path(output_file)
    
    if output_path.exists():
        print(f"⚠️  Le fichier {output_file} existe déjà")
        return False
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"✅ Fichier {output_file} créé avec succès")
        print(f"   Éditez-le pour ajouter vos credentials")
        return True
    
    except Exception as e:
        print(f"❌ Erreur lors de la création de {output_file}: {e}")
        return False


# Auto-chargement si le module est importé
def auto_load():
    """
    Charge automatiquement le .env s'il existe
    
    Appelé automatiquement lors de l'import du module.
    """
    env_path = find_dotenv()
    
    if env_path:
        success = load_dotenv(str(env_path), override=False)
        if success:
            # Mode silencieux - ne pas afficher de message
            pass
    

# Charger automatiquement lors de l'import
auto_load()

