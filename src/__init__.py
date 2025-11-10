"""
GitHub Stats Automation Package
================================

Ce package permet de collecter et afficher automatiquement les statistiques GitHub
incluant les dépôts privés.

Modules:
    - cache_manager: Gestion du cache pour optimiser les requêtes API
    - rate_limiter: Gestion des limites de l'API GitHub
    - config: Gestion de la configuration
    - github_stats: Classe principale pour récupérer les statistiques
    - utils: Fonctions utilitaires diverses
    - env_loader: Chargement automatique du fichier .env
"""

__version__ = '1.0.0'
__author__ = 'GitHub Stats Team'

from .cache_manager import CacheManager
from .rate_limiter import RateLimitHandler
from .config import Config
from .github_stats import GitHubStatsPrivate
from .env_loader import load_dotenv, find_dotenv

__all__ = [
    'CacheManager',
    'RateLimitHandler',
    'Config',
    'GitHubStatsPrivate',
    'load_dotenv',
    'find_dotenv'
]

