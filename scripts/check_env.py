#!/usr/bin/env python3
"""
Script de Vérification de l'Environnement
==========================================

Vérifie que toutes les variables d'environnement requises sont correctement configurées.

Usage:
    python scripts/check_env.py
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.env_loader import (
    load_dotenv, 
    find_dotenv, 
    check_required_env_vars,
    display_env_info,
    create_env_template
)
from src.utils import validate_github_token, validate_github_username
import os


def main():
    """Vérifie la configuration de l'environnement"""
    
    print("\n" + "=" * 70)
    print("🔍 VÉRIFICATION DE L'ENVIRONNEMENT".center(70))
    print("=" * 70)
    
    # 1. Chercher le fichier .env
    print("\n📁 Recherche du fichier .env...")
    env_file = find_dotenv()
    
    if env_file:
        print(f"✅ Fichier .env trouvé: {env_file}")
        load_dotenv(str(env_file))
    else:
        print("❌ Aucun fichier .env trouvé")
        print("\n💡 Voulez-vous créer un fichier .env template? (o/n): ", end='')
        
        try:
            response = input().lower()
            if response == 'o':
                create_env_template()
                print("\n⚠️  Éditez le fichier .env et relancez ce script")
                return 1
        except:
            pass
    
    # 2. Vérifier les variables requises
    print("\n🔐 Vérification des variables requises...")
    required_vars = ['GITHUB_TOKEN', 'GITHUB_USERNAME']
    all_present, missing = check_required_env_vars(required_vars)
    
    if not all_present:
        print(f"❌ Variables manquantes: {', '.join(missing)}")
        print("\n💡 Ajoutez ces variables dans votre fichier .env:")
        for var in missing:
            print(f"   {var}=votre_valeur")
        return 1
    else:
        print("✅ Toutes les variables requises sont présentes")
    
    # 3. Afficher les informations
    display_env_info()
    
    # 4. Valider le token
    print("🔑 Validation du token GitHub...")
    token = os.getenv('GITHUB_TOKEN')
    
    if validate_github_token(token):
        print("✅ Format du token valide")
    else:
        print("⚠️  Format du token invalide")
        print("   Les tokens GitHub commencent généralement par 'ghp_'")
        print("   et contiennent 36 caractères alphanumériques")
    
    # 5. Valider le username
    print("\n👤 Validation du username GitHub...")
    username = os.getenv('GITHUB_USERNAME')
    
    if validate_github_username(username):
        print("✅ Format du username valide")
    else:
        print("⚠️  Format du username invalide")
        print("   Les usernames GitHub:")
        print("   - Contiennent uniquement des lettres, chiffres et tirets")
        print("   - Commencent par une lettre ou un chiffre")
        print("   - Font maximum 39 caractères")
    
    # 6. Test de connexion (basique)
    print("\n🌐 Test de connexion à l'API GitHub...")
    try:
        import requests
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Connexion réussie!")
            print(f"   Username: {user_data['login']}")
            print(f"   Nom: {user_data.get('name', 'N/A')}")
            print(f"   Repos publics: {user_data['public_repos']}")
            print(f"   Repos privés: {user_data.get('total_private_repos', 0)}")
            
            # Vérifier le rate limit
            rate_response = requests.get('https://api.github.com/rate_limit', headers=headers, timeout=10)
            if rate_response.status_code == 200:
                rate_data = rate_response.json()
                core = rate_data['resources']['core']
                print(f"\n📊 Rate Limit:")
                print(f"   Restantes: {core['remaining']}/{core['limit']}")
        
        elif response.status_code == 401:
            print("❌ Authentification échouée")
            print("   Le token est invalide ou a expiré")
            print("   Créez un nouveau token sur: https://github.com/settings/tokens")
        
        else:
            print(f"⚠️  Erreur {response.status_code}")
            print(f"   Message: {response.json().get('message', 'Erreur inconnue')}")
    
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("   Vérifiez votre connexion Internet")
    
    # 7. Résumé final
    print("\n" + "=" * 70)
    print("📋 RÉSUMÉ".center(70))
    print("=" * 70)
    
    if all_present and validate_github_token(token) and validate_github_username(username):
        print("\n✅ Votre environnement est correctement configuré!")
        print("\n🚀 Vous pouvez maintenant exécuter:")
        print("   python scripts/update_stats.py --dry-run")
        print("\n" + "=" * 70)
        return 0
    else:
        print("\n⚠️  Votre environnement nécessite des corrections")
        print("\n📝 Actions à faire:")
        
        if not all_present:
            print("   1. Ajoutez les variables manquantes dans .env")
        
        if not validate_github_token(token):
            print("   2. Vérifiez le format de votre GITHUB_TOKEN")
        
        if not validate_github_username(username):
            print("   3. Vérifiez le format de votre GITHUB_USERNAME")
        
        print("\n" + "=" * 70)
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

