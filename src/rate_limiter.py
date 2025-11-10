#!/usr/bin/env python3
"""
Rate Limiter Module
===================

Gère les limites de l'API GitHub pour éviter les erreurs 403 (rate limit exceeded).

L'API GitHub impose des limites:
- 5000 requêtes/heure avec authentification
- 60 requêtes/heure sans authentification

Ce module:
- Vérifie automatiquement le rate limit restant
- Met en pause si nécessaire
- Affiche des warnings avant d'atteindre la limite
- Peut être utilisé comme décorateur
"""

import time
import requests
from datetime import datetime
from typing import Dict, Callable
from functools import wraps


class RateLimitHandler:
    """
    Gestionnaire du rate limiting de l'API GitHub
    
    Permet de gérer automatiquement les limites de l'API en vérifiant
    le nombre de requêtes restantes et en attendant si nécessaire.
    
    Attributes:
        headers (Dict): Headers d'authentification GitHub
        base_url (str): URL de base de l'API GitHub
        min_remaining (int): Seuil minimal avant d'attendre
    """
    
    def __init__(self, headers: Dict, min_remaining: int = 100):
        """
        Initialise le gestionnaire de rate limit
        
        Args:
            headers: Headers contenant le token d'authentification
            min_remaining: Nombre minimum de requêtes avant d'attendre
        """
        self.headers = headers
        self.base_url = 'https://api.github.com'
        self.min_remaining = min_remaining
        self._last_check = None
        self._last_rate_info = None
    
    def check_rate_limit(self) -> Dict[str, any]:
        """
        Vérifie l'état actuel du rate limit via l'API
        
        Cette requête ne compte pas dans le rate limit.
        
        Returns:
            Dictionnaire avec les informations de rate limit:
            - remaining: Nombre de requêtes restantes
            - limit: Limite totale
            - reset: Timestamp de reset
            - reset_datetime: Date/heure de reset
            - used: Nombre de requêtes utilisées
        
        Raises:
            requests.RequestException: En cas d'erreur de connexion
        """
        try:
            response = requests.get(
                f'{self.base_url}/rate_limit',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            core = data['resources']['core']
            
            rate_info = {
                'remaining': core['remaining'],
                'limit': core['limit'],
                'reset': core['reset'],
                'reset_datetime': datetime.fromtimestamp(core['reset']),
                'used': core['used']
            }
            
            self._last_check = datetime.now()
            self._last_rate_info = rate_info
            
            return rate_info
            
        except Exception as e:
            print(f"⚠️  Erreur lors de la vérification du rate limit: {e}")
            
            # Retourner des valeurs par défaut en cas d'erreur
            return {
                'remaining': 5000,
                'limit': 5000,
                'reset': 0,
                'reset_datetime': datetime.now(),
                'used': 0
            }
    
    def get_cached_rate_info(self) -> Dict[str, any]:
        """
        Retourne la dernière info de rate limit sans faire de requête
        
        Utile pour éviter de faire trop de requêtes de vérification.
        
        Returns:
            Dernière info de rate limit connue ou None
        """
        return self._last_rate_info
    
    def wait_if_needed(self, force_check: bool = False) -> bool:
        """
        Attend si le rate limit est proche de la limite
        
        Vérifie le nombre de requêtes restantes et met en pause
        si nécessaire pour éviter d'être bloqué.
        
        Args:
            force_check: Force la vérification même si récente
        
        Returns:
            True si on a attendu, False sinon
        
        Example:
            >>> limiter = RateLimitHandler(headers)
            >>> limiter.wait_if_needed()
            >>> # Continue avec les requêtes API
        """
        # Vérifier seulement toutes les 10 requêtes pour optimiser
        if not force_check and self._last_check:
            time_since_check = (datetime.now() - self._last_check).total_seconds()
            if time_since_check < 5:  # Moins de 5 secondes
                return False
        
        rate_info = self.check_rate_limit()
        
        # Afficher un warning si on approche de la limite
        if rate_info['remaining'] < 500:
            print(f"⚠️  Rate limit faible: {rate_info['remaining']}/{rate_info['limit']}")
        
        # Attendre si on est en dessous du seuil
        if rate_info['remaining'] < self.min_remaining:
            reset_time = rate_info['reset_datetime']
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            
            if wait_seconds > 0:
                wait_minutes = int(wait_seconds / 60)
                print(f"\n⏳ Rate limit atteint!")
                print(f"   Requêtes restantes: {rate_info['remaining']}/{rate_info['limit']}")
                print(f"   Reset à: {reset_time.strftime('%H:%M:%S')}")
                print(f"   Attente de {wait_minutes} minutes et {int(wait_seconds % 60)} secondes...\n")
                
                # Attendre avec indication de progression
                self._wait_with_progress(wait_seconds + 5)
                
                return True
        
        return False
    
    def _wait_with_progress(self, seconds: float):
        """
        Attend en affichant une barre de progression
        
        Args:
            seconds: Nombre de secondes à attendre
        """
        start_time = time.time()
        end_time = start_time + seconds
        
        while time.time() < end_time:
            remaining = end_time - time.time()
            progress = (seconds - remaining) / seconds
            
            # Barre de progression
            bar_length = 30
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Afficher (écrase la ligne précédente)
            print(f'\r   [{bar}] {int(remaining)}s restantes', end='', flush=True)
            
            time.sleep(1)
        
        print('\r   ' + '█' * 30 + ' ✅ Reprise des requêtes!\n')
    
    def get_status_message(self) -> str:
        """
        Obtient un message formaté sur l'état du rate limit
        
        Returns:
            Message formaté avec les statistiques
        """
        rate_info = self.check_rate_limit()
        
        percentage_used = (rate_info['used'] / rate_info['limit']) * 100
        reset_time = rate_info['reset_datetime'].strftime('%H:%M:%S')
        
        return f"""
📊 État du Rate Limit GitHub:
   • Utilisées: {rate_info['used']}/{rate_info['limit']} ({percentage_used:.1f}%)
   • Restantes: {rate_info['remaining']}
   • Reset à: {reset_time}
"""


def rate_limit_aware(func: Callable) -> Callable:
    """
    Décorateur pour gérer automatiquement le rate limiting
    
    Vérifie et attend automatiquement avant chaque appel de fonction
    si la limite est proche.
    
    Usage:
        @rate_limit_aware
        def get_repos(self):
            # Votre code ici
            pass
    
    Args:
        func: Fonction à décorer
    
    Returns:
        Fonction décorée avec gestion du rate limit
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Vérifier si l'objet a un rate_limiter
        if hasattr(self, 'rate_limiter') and isinstance(self.rate_limiter, RateLimitHandler):
            self.rate_limiter.wait_if_needed()
        
        # Exécuter la fonction
        return func(self, *args, **kwargs)
    
    return wrapper


def with_retry(max_retries: int = 3, delay: int = 2):
    """
    Décorateur pour réessayer en cas d'erreur de rate limit
    
    Réessaie automatiquement en cas d'erreur 403 (rate limit).
    
    Args:
        max_retries: Nombre maximum de tentatives
        delay: Délai entre les tentatives (secondes)
    
    Returns:
        Décorateur configuré
    
    Usage:
        @with_retry(max_retries=3, delay=5)
        def make_api_call(self):
            # Votre code ici
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403:
                        # Rate limit atteint
                        print(f"⚠️  Rate limit atteint, tentative {attempt + 1}/{max_retries}")
                        
                        if attempt < max_retries - 1:
                            wait_time = delay * (2 ** attempt)  # Backoff exponentiel
                            time.sleep(wait_time)
                        
                        last_exception = e
                    else:
                        raise
                
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            
            # Si toutes les tentatives ont échoué
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator

