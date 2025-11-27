#!/usr/bin/env python3
"""
Script Principal - Mise à Jour des Statistiques GitHub
========================================================

Ce script est le point d'entrée principal pour mettre à jour
les statistiques GitHub du profil.

Fonctionnalités:
- Chargement de la configuration
- Validation des credentials
- Récupération des statistiques
- Génération du README
- Mise à jour du profil GitHub
- Sauvegarde des données en JSON (optionnel)
- Mode dry-run pour tester sans publier

Usage:
    python scripts/update_stats.py [options]

Options:
    --dry-run : Ne pas publier sur GitHub, juste afficher
    --no-cache : Désactiver le cache
    --config PATH : Chemin vers le fichier de configuration
    --output PATH : Fichier de sortie pour le README
    --verbose : Mode verbeux (plus de logs)

Exemples:
    python scripts/update_stats.py
    python scripts/update_stats.py --dry-run
    python scripts/update_stats.py --no-cache --verbose
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Charger les variables d'environnement depuis .env
from src.env_loader import load_dotenv, find_dotenv

# Charger le .env automatiquement
env_file = find_dotenv()
if env_file:
    load_dotenv(str(env_file))
    print(f"🔐 Fichier .env chargé depuis: {env_file}")
else:
    print("⚠️  Aucun fichier .env trouvé (utilisation des variables d'environnement système)")

from src.config import Config
from src.github_stats import GitHubStatsPrivate
from src.cache_manager import CacheManager
from src.utils import format_number, validate_github_token, validate_github_username


def parse_arguments():
    """
    Parse les arguments de la ligne de commande

    Returns:
        Arguments parsés
    """
    parser = argparse.ArgumentParser(
        description='Met à jour les statistiques GitHub du profil',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  %(prog)s                          # Mode normal
  %(prog)s --dry-run                # Tester sans publier
  %(prog)s --no-cache --verbose     # Sans cache, mode verbeux
  %(prog)s --config custom.yaml     # Utiliser une config personnalisée
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Ne pas publier sur GitHub, juste afficher le résultat'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Désactiver le cache (force la récupération depuis l\'API)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='configs/config.yaml',
        help='Chemin vers le fichier de configuration (défaut: configs/config.yaml)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Fichier de sortie pour le README (défaut: README.md)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbeux (affiche plus d\'informations)'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Nettoyer le cache avant de commencer'
    )
    
    parser.add_argument(
        '--json',
        type=str,
        help='Sauvegarder les stats en JSON dans ce fichier'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Afficher la configuration et quitter'
    )
    
    return parser.parse_args()


def validate_credentials(token: str, username: str) -> tuple[bool, list[str]]:
    """
    Valide les credentials GitHub
    
    Args:
        token: Token d'authentification
        username: Nom d'utilisateur
    
    Returns:
        Tuple (is_valid, errors)
    """
    errors = []
    
    if not token:
        errors.append("❌ Token GitHub manquant (GITHUB_TOKEN)")
    elif not validate_github_token(token):
        errors.append("⚠️  Format du token GitHub invalide")
    
    if not username:
        errors.append("❌ Username GitHub manquant (GITHUB_USERNAME)")
    elif not validate_github_username(username):
        errors.append("⚠️  Format du username GitHub invalide")
    
    return len(errors) == 0, errors


def print_banner():
    """Affiche la bannière du script"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🚀 GITHUB STATS AUTOMATION 2025                     ║
║                                                              ║
║          Mise à jour automatique des statistiques           ║
║          incluant les dépôts privés                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_summary(stats: dict):
    """
    Affiche un résumé des statistiques

    Args:
        stats: Dictionnaire des statistiques
    """
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES STATISTIQUES".center(70))
    print("=" * 70)

    print(f"\n{'📦 DÉPÔTS':<40}")
    print(f"   Total                : {format_number(stats['total_repos']):>15}")
    print(f"   └─ Publics           : {format_number(stats['public_repos']):>15}")
    print(f"   └─ Privés            : {format_number(stats['private_repos']):>15}")

    print(f"\n{'⭐ ÉTOILES':<40}")
    print(f"   Total                : {format_number(stats['stars']):>15}")
    
    print(f"\n{'📝 COMMITS':<40}")
    print(f"   Derniers {stats['period_days']} jours   : {format_number(stats['commits_last_year']):>15}")
    
    print(f"\n{'🔀 PULL REQUESTS':<40}")
    print(f"   Total                : {format_number(stats['prs']['total']):>15}")
    print(f"   ├─ Ouvertes          : {format_number(stats['prs']['open']):>15}")
    print(f"   ├─ Mergées           : {format_number(stats['prs']['merged']):>15}")
    print(f"   └─ Fermées           : {format_number(stats['prs']['closed']):>15}")
    
    print(f"\n{'❗ ISSUES':<40}")
    print(f"   Total                : {format_number(stats['issues']['total']):>15}")
    print(f"   ├─ Ouvertes          : {format_number(stats['issues']['open']):>15}")
    print(f"   └─ Fermées           : {format_number(stats['issues']['closed']):>15}")
    
    if stats['code_changes']['total_changes'] > 0:
        print(f"\n{'💻 MODIFICATIONS DE CODE':<40}")
        print(f"   Lignes ajoutées      : {format_number(stats['code_changes']['additions']):>15}")
        print(f"   Lignes supprimées    : {format_number(stats['code_changes']['deletions']):>15}")
        print(f"   Total modifications  : {format_number(stats['code_changes']['total_changes']):>15}")
    
    if stats['languages']:
        print(f"\n{'💻 TOP 5 LANGAGES':<40}")
        for i, (lang, percent) in enumerate(list(stats['languages'].items())[:5], 1):
            print(f"   {i}. {lang:<25} : {percent:>10.1f}%")
    
    print(f"\n{'🤝 CONTRIBUTIONS':<40}")
    print(f"   Repos contribués     : {format_number(stats['contributed_repos']):>15}")
    
    print("\n" + "=" * 70)


def save_stats_to_json(stats: dict, filepath: str):
    """
    Sauvegarde les statistiques en JSON
    
    Args:
        stats: Statistiques à sauvegarder
        filepath: Chemin du fichier JSON
    """
    try:
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convertir les données non-sérialisables
        stats_copy = dict(stats)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats_copy, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Statistiques sauvegardées dans: {filepath}")
    
    except Exception as e:
        print(f"⚠️  Erreur lors de la sauvegarde JSON: {e}")


def save_readme_to_file(content: str, filepath: str):
    """
    Sauvegarde le README dans un fichier local
    
    Args:
        content: Contenu du README
        filepath: Chemin du fichier
    """
    try:
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ README sauvegardé dans: {filepath}")
    
    except Exception as e:
        print(f"⚠️  Erreur lors de la sauvegarde du README: {e}")


def main():
    """Point d'entrée principal du script"""
    
    # Parser les arguments
    args = parse_arguments()
    
    # Afficher la bannière
    print_banner()
    
    # Charger la configuration
    try:
        config = Config(args.config)
        print(f"✅ Configuration chargée depuis: {args.config}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration: {e}")
        return 1
    
    # Afficher la config si demandé
    if args.show_config:
        config.display()
        return 0
    
    # Appliquer les options de ligne de commande
    if args.no_cache:
        config.set('cache.enabled', False)
        print("🔧 Cache désactivé")
    
    if args.verbose:
        config.set('logging.level', 'DEBUG')
        print("🔧 Mode verbeux activé")
    
    # Récupérer les credentials
    token = config.get('github.token')
    username = config.get('github.username')
    
    # Valider les credentials
    is_valid, errors = validate_credentials(token, username)
    if not is_valid:
        print("\n❌ ERREUR: Credentials invalides\n")
        for error in errors:
            print(f"   {error}")
        
        print("\n💡 Configuration requise:")
        print("   export GITHUB_TOKEN='votre_token'")
        print("   export GITHUB_USERNAME='votre_username'")
        print("\n🔑 Créez un token sur: https://github.com/settings/tokens")
        print("   Permissions requises: repo (full), user (read)")
        return 1
    
    # Valider la configuration complète
    is_valid, errors = config.validate()
    if not is_valid:
        print("\n⚠️  Avertissements de configuration:\n")
        for error in errors:
            print(f"   {error}")
        print()
    
    print(f"\n🎯 Utilisateur cible: {username}")
    print(f"🔑 Token: {token[:8]}...{token[-4:]}")
    
    # Nettoyer le cache si demandé
    if args.clear_cache:
        cache = CacheManager(config.get('cache.directory', '.cache'))
        count = cache.clear()
        print(f"🧹 Cache nettoyé: {count} fichier(s) supprimé(s)")
    
    # Initialiser le gestionnaire de stats
    try:
        stats_manager = GitHubStatsPrivate(token, username, config)
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return 1
    
    # Calculer les statistiques
    print("\n" + "=" * 70)
    print("🔍 RÉCUPÉRATION DES STATISTIQUES...")
    print("=" * 70 + "\n")
    
    try:
        stats = stats_manager.calculate_all_stats()
    except Exception as e:
        print(f"\n❌ Erreur lors du calcul des statistiques: {e}")
        return 1
    
    # Afficher le résumé
    print_summary(stats)
    
    # Sauvegarder les stats en JSON si demandé
    if args.json:
        save_stats_to_json(stats, args.json)
    elif config.get('output.save_json', False):
        json_file = config.get('output.json_file', 'stats/github_stats.json')
        save_stats_to_json(stats, json_file)
    
    # Générer le README
    print("\n📝 Génération du README...")
    try:
        readme_content = stats_manager.generate_profile_readme(stats)
    except Exception as e:
        print(f"❌ Erreur lors de la génération du README: {e}")
        return 1
    
    # Sauvegarder le README localement
    output_file = args.output or config.get('output.readme_file', 'README.md')
    save_readme_to_file(readme_content, output_file)
    
    # Mode dry-run
    if args.dry_run:
        print("\n" + "=" * 70)
        print("🔍 MODE DRY-RUN - Aperçu du README:".center(70))
        print("=" * 70)
        
        # Afficher les 30 premières lignes
        lines = readme_content.split('\n')
        for line in lines[:30]:
            print(line)
        
        if len(lines) > 30:
            print(f"\n... ({len(lines) - 30} lignes supplémentaires)")
        
        print("\n" + "=" * 70)
        print("ℹ️  Mode dry-run: Le README n'a PAS été publié sur GitHub")
        print("=" * 70)
        return 0
    
    # Publier sur GitHub
    print("\n💾 Publication sur GitHub...")
    
    try:
        result = stats_manager.update_profile_readme(readme_content)
        
        print("\n" + "=" * 70)
        print("✅ SUCCÈS !".center(70))
        print("=" * 70)
        print(f"\n🔗 Voir votre profil: https://github.com/{username}")
        print(f"📝 README mis à jour avec succès")
        print(f"🕐 Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        print("\n" + "=" * 70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Erreur lors de la publication: {e}")
        print(f"\n💡 Le README a été sauvegardé localement dans: {output_file}")
        print("   Vous pouvez le copier manuellement sur GitHub si nécessaire.")
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

