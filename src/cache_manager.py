#!/usr/bin/env python3
"""
Cache Manager Module
====================

Ce module gère le système de cache pour optimiser les requêtes API GitHub.

Fonctionnalités:
- Stockage des données API en JSON
- Vérification de la validité du cache basée sur le temps
- Nettoyage automatique du cache
- Utilisation de hash MD5 pour les clés de cache

Avantages:
- Réduit le nombre de requêtes API
- Accélère les exécutions répétées
- Respecte les limites de rate limit de GitHub
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class CacheManager:
    """
    Gestionnaire de cache pour les données API GitHub
    
    Le cache est stocké dans des fichiers JSON avec une durée de validité.
    Chaque entrée de cache a une clé unique générée par hash MD5.
    
    Attributes:
        cache_dir (Path): Répertoire de stockage du cache
    """
    
    def __init__(self, cache_dir: str = '.cache'):
        """
        Initialise le gestionnaire de cache
        
        Args:
            cache_dir: Répertoire où stocker les fichiers de cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Créer un fichier .gitignore pour ne pas versionner le cache
        gitignore_path = self.cache_dir / '.gitignore'
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write('*\n!.gitignore\n')
    
    def _get_cache_key(self, key: str) -> str:
        """
        Génère une clé de cache sécurisée à partir d'une chaîne
        
        Utilise MD5 pour créer un nom de fichier court et unique.
        
        Args:
            key: La clé originale (ex: 'repos_username')
        
        Returns:
            Hash MD5 de la clé
        """
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """
        Récupère une donnée depuis le cache si elle est valide
        
        Vérifie l'âge du fichier de cache. Si trop ancien, retourne None.
        
        Args:
            key: Clé de la donnée à récupérer
            max_age_hours: Âge maximum du cache en heures (défaut: 24h)
        
        Returns:
            Les données cachées ou None si invalide/inexistant
        
        Example:
            >>> cache = CacheManager()
            >>> data = cache.get('repos_user123', max_age_hours=1)
            >>> if data:
            ...     print("Données en cache!")
        """
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        # Vérifier si le fichier existe
        if not cache_file.exists():
            return None
        
        # Vérifier l'âge du fichier
        file_mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        file_age = datetime.now() - file_mod_time
        
        if file_age > timedelta(hours=max_age_hours):
            # Cache périmé, le supprimer
            cache_file.unlink()
            return None
        
        # Charger et retourner les données
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Erreur lecture cache: {e}")
            # Supprimer le fichier corrompu
            cache_file.unlink()
            return None
    
    def set(self, key: str, data: Any) -> bool:
        """
        Sauvegarde une donnée dans le cache
        
        Args:
            key: Clé pour identifier la donnée
            data: Donnée à sauvegarder (doit être sérialisable en JSON)
        
        Returns:
            True si succès, False sinon
        
        Example:
            >>> cache = CacheManager()
            >>> cache.set('repos_user123', {'repos': [...]})
        """
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (TypeError, IOError) as e:
            print(f"⚠️  Erreur écriture cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Supprime une entrée spécifique du cache
        
        Args:
            key: Clé de l'entrée à supprimer
        
        Returns:
            True si supprimé, False si n'existait pas
        """
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False
    
    def clear(self) -> int:
        """
        Nettoie tout le cache
        
        Supprime tous les fichiers .json du répertoire de cache.
        
        Returns:
            Nombre de fichiers supprimés
        
        Example:
            >>> cache = CacheManager()
            >>> count = cache.clear()
            >>> print(f"{count} fichiers supprimés")
        """
        count = 0
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass
        
        return count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Obtient des informations sur l'état du cache
        
        Returns:
            Dictionnaire avec statistiques du cache
        """
        files = list(self.cache_dir.glob('*.json'))
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            'total_files': len(files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_directory': str(self.cache_dir.absolute())
        }

