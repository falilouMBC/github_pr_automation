#!/usr/bin/env python3
"""
GitHub Stats Module
===================

Module principal pour récupérer les statistiques GitHub complètes.

Ce module utilise l'API GitHub pour collecter:
- Statistiques de dépôts (publics + privés)
- Commits, PRs, Issues
- Langages de programmation
- Statistiques de code (additions/suppressions)
- Heatmap d'activité
- Contributions externes

Le module intègre:
- Système de cache pour optimiser les requêtes
- Gestion du rate limiting
- Logging détaillé
- Retry automatique en cas d'erreur
"""

import os
import requests
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .cache_manager import CacheManager
from .rate_limiter import RateLimitHandler, rate_limit_aware, with_retry
from .config import Config
from .utils import (
    format_number, generate_ascii_bar, generate_language_bar,
    generate_heatmap_ascii, create_badge_url, format_relative_time,
    get_emoji_for_metric, safe_divide
)


class GitHubStatsPrivate:
    """
    Classe principale pour récupérer les statistiques GitHub
    
    Cette classe permet de récupérer toutes les statistiques d'un compte GitHub,
    incluant les dépôts privés si un token avec les bonnes permissions est fourni.
    
    Attributes:
        token (str): Token d'authentification GitHub
        username (str): Nom d'utilisateur GitHub
        config (Config): Configuration de l'application
        cache (CacheManager): Gestionnaire de cache
        rate_limiter (RateLimitHandler): Gestionnaire de rate limit
        logger (logging.Logger): Logger pour le suivi
    """
    
    def __init__(self, token: str, username: str, config: Optional[Config] = None):
        """
        Initialise le collecteur de statistiques
        
        Args:
            token: Token d'authentification GitHub (avec scope 'repo' et 'user')
            username: Nom d'utilisateur GitHub
            config: Configuration (si None, charge depuis fichier)
        """
        self.token = token
        self.username = username
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        
        # Configuration
        self.config = config or Config()
        
        # Cache
        cache_dir = self.config.get('cache.directory', '.cache')
        self.cache = CacheManager(cache_dir)
        
        # Rate limiter
        min_remaining = self.config.get('rate_limit.min_remaining', 100)
        self.rate_limiter = RateLimitHandler(self.headers, min_remaining)
        
        # Logger
        self.logger = self._setup_logger()
        
        self.logger.info(f"🚀 Initialisation pour l'utilisateur: {username}")
    
    def _setup_logger(self) -> logging.Logger:
        """
        Configure le système de logging
        
        Returns:
            Logger configuré
        """
        logger = logging.getLogger('GitHubStats')
        
        # Éviter les duplications
        if logger.handlers:
            return logger
        
        log_level = self.config.get('logging.level', 'INFO')
        logger.setLevel(getattr(logging, log_level))
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # Handler fichier (optionnel)
        log_dir = Path(self.config.get('logging.directory', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        try:
            file_handler = logging.FileHandler(log_dir / 'github_stats.log', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"⚠️  Impossible de créer le fichier log: {e}")
        
        return logger
    
    @rate_limit_aware
    @with_retry(max_retries=3, delay=2)
    def get_all_repos(self) -> List[Dict]:
        """
        Récupère TOUS les dépôts (publics + privés)
        
        Utilise le cache si activé et valide.
        Pagine automatiquement pour récupérer tous les repos.
        
        Returns:
            Liste de dictionnaires représentant les dépôts
        
        Example:
            >>> stats = GitHubStatsPrivate(token, username)
            >>> repos = stats.get_all_repos()
            >>> print(f"Nombre de repos: {len(repos)}")
        """
        cache_key = f'repos_{self.username}'
        
        # Vérifier le cache
        if self.config.get('cache.enabled', True):
            cached = self.cache.get(cache_key, max_age_hours=self.config.get('cache.max_age_hours', 24))
            if cached:
                self.logger.info(f"📦 Utilisation du cache pour les repos ({len(cached)} repos)")
                return cached
        
        self.logger.info("🔍 Récupération des dépôts depuis l'API...")
        
        repos = []
        page = 1
        per_page = self.config.get('stats.max_repos_per_page', 100)
        
        while True:
            url = f'{self.base_url}/user/repos'
            params = {
                'per_page': per_page,
                'page': page,
                'type': 'owner',  # Seulement vos dépôts
                'sort': 'updated'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            repos.extend(data)
            self.logger.debug(f"   Page {page}: {len(data)} repos récupérés")
            page += 1
        
        self.logger.info(f"✅ {len(repos)} dépôt(s) récupéré(s)")
        
        # Mettre en cache
        if self.config.get('cache.enabled', True):
            self.cache.set(cache_key, repos)
        
        return repos
    
    def count_stars(self, repos: List[Dict]) -> int:
        """
        Compte le total d'étoiles sur tous les dépôts
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Nombre total d'étoiles
        """
        total = sum(repo['stargazers_count'] for repo in repos)
        self.logger.info(f"⭐ Total d'étoiles: {total}")
        return total
    
    @rate_limit_aware
    def count_commits_last_year(self, repos: List[Dict]) -> int:
        """
        Compte les commits de la dernière année
        
        Parcourt tous les repos et compte les commits de l'utilisateur
        sur la période spécifiée.
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Nombre total de commits
        """
        self.logger.info("📝 Comptage des commits...")
        
        total_commits = 0
        days_back = self.config.get('stats.days_back', 365)
        since_date = datetime.now() - timedelta(days=days_back)
        max_pages = self.config.get('stats.max_commits_pages', 10)
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo['full_name']
            self.logger.debug(f"   [{i}/{len(repos)}] {repo_name}")
            
            try:
                url = f'{self.base_url}/repos/{repo_name}/commits'
                params = {
                    'author': self.username,
                    'since': since_date.isoformat(),
                    'per_page': 100
                }
                
                page = 1
                while page <= max_pages:
                    params['page'] = page
                    response = requests.get(url, headers=self.headers, params=params, timeout=30)
                    
                    if response.status_code != 200:
                        break
                    
                    commits = response.json()
                    if not commits:
                        break
                    
                    total_commits += len(commits)
                    page += 1
                
            except Exception as e:
                self.logger.warning(f"⚠️  Erreur commits pour {repo_name}: {e}")
                continue
        
        self.logger.info(f"✅ Total commits: {total_commits}")
        return total_commits
    
    @rate_limit_aware
    def count_pull_requests(self, repos: List[Dict]) -> Dict[str, int]:
        """
        Compte les Pull Requests (créées par l'utilisateur)
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Dictionnaire avec les stats de PRs
        """
        self.logger.info("🔀 Comptage des Pull Requests...")
        
        stats = {
            'total': 0,
            'open': 0,
            'closed': 0,
            'merged': 0
        }
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo['full_name']
            self.logger.debug(f"   [{i}/{len(repos)}] {repo_name}")
            
            try:
                url = f'{self.base_url}/repos/{repo_name}/pulls'
                params = {
                    'state': 'all',
                    'creator': self.username,
                    'per_page': 100
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    continue
                
                prs = response.json()
                
                for pr in prs:
                    stats['total'] += 1
                    
                    if pr['state'] == 'open':
                        stats['open'] += 1
                    else:
                        stats['closed'] += 1
                    
                    if pr.get('merged_at'):
                        stats['merged'] += 1
            
            except Exception as e:
                self.logger.warning(f"⚠️  Erreur PRs pour {repo_name}: {e}")
                continue
        
        self.logger.info(f"✅ Total PRs: {stats['total']} (merged: {stats['merged']})")
        return stats
    
    @rate_limit_aware
    def count_issues(self, repos: List[Dict]) -> Dict[str, int]:
        """
        Compte les Issues (créées par l'utilisateur)
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Dictionnaire avec les stats d'issues
        """
        self.logger.info("❗ Comptage des Issues...")
        
        stats = {
            'total': 0,
            'open': 0,
            'closed': 0
        }
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo['full_name']
            self.logger.debug(f"   [{i}/{len(repos)}] {repo_name}")
            
            try:
                url = f'{self.base_url}/repos/{repo_name}/issues'
                params = {
                    'state': 'all',
                    'creator': self.username,
                    'per_page': 100
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    continue
                
                issues = response.json()
                
                # Filtrer les PRs (GitHub considère les PRs comme des issues)
                issues = [i for i in issues if 'pull_request' not in i]
                
                for issue in issues:
                    stats['total'] += 1
                    
                    if issue['state'] == 'open':
                        stats['open'] += 1
                    else:
                        stats['closed'] += 1
            
            except Exception as e:
                self.logger.warning(f"⚠️  Erreur issues pour {repo_name}: {e}")
                continue
        
        self.logger.info(f"✅ Total Issues: {stats['total']}")
        return stats
    
    def count_contributed_repos_last_year(self, repos: List[Dict]) -> int:
        """
        Compte les dépôts auxquels l'utilisateur a contribué cette année
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Nombre de dépôts avec contributions récentes
        """
        count = 0
        days_back = self.config.get('stats.days_back', 365)
        threshold_date = datetime.now() - timedelta(days=days_back)
        
        for repo in repos:
            updated_at = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            
            if updated_at >= threshold_date:
                count += 1
        
        self.logger.info(f"🤝 Repos contribués: {count}")
        return count
    
    @rate_limit_aware
    def get_language_stats(self, repos: List[Dict]) -> Dict[str, float]:
        """
        Récupère les statistiques des langages de programmation
        
        Analyse tous les repos pour déterminer les langages utilisés
        et leur proportion.
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Dictionnaire {langage: pourcentage}
        """
        if not self.config.get('stats.include_languages', True):
            return {}
        
        self.logger.info("💻 Analyse des langages...")
        
        language_bytes = {}
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo['full_name']
            self.logger.debug(f"   [{i}/{len(repos)}] {repo_name}")
            
            try:
                url = f'{self.base_url}/repos/{repo_name}/languages'
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    languages = response.json()
                    
                    for lang, bytes_count in languages.items():
                        language_bytes[lang] = language_bytes.get(lang, 0) + bytes_count
            
            except Exception as e:
                self.logger.warning(f"⚠️  Erreur langages pour {repo_name}: {e}")
                continue
        
        # Convertir en pourcentages
        total_bytes = sum(language_bytes.values())
        if total_bytes == 0:
            return {}
        
        language_percentages = {
            lang: round((bytes_count / total_bytes) * 100, 2)
            for lang, bytes_count in language_bytes.items()
        }
        
        # Trier par pourcentage décroissant
        sorted_languages = dict(sorted(
            language_percentages.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        self.logger.info(f"✅ {len(sorted_languages)} langage(s) détecté(s)")
        return sorted_languages
    
    @rate_limit_aware
    def get_code_changes_stats(self, repos: List[Dict]) -> Dict[str, int]:
        """
        Récupère les statistiques d'ajout/suppression de code
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Dictionnaire avec additions, deletions, total_changes
        """
        if not self.config.get('stats.include_code_changes', True):
            return {'additions': 0, 'deletions': 0, 'total_changes': 0}
        
        self.logger.info("➕ Analyse des modifications de code...")
        
        stats = {
            'additions': 0,
            'deletions': 0,
            'total_changes': 0
        }
        
        days_back = self.config.get('stats.days_back', 365)
        since_date = datetime.now() - timedelta(days=days_back)
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo['full_name']
            self.logger.debug(f"   [{i}/{len(repos)}] {repo_name}")
            
            try:
                url = f'{self.base_url}/repos/{repo_name}/stats/contributors'
                response = requests.get(url, headers=self.headers, timeout=30)
                
                # Les stats peuvent prendre du temps à générer
                if response.status_code == 202:
                    import time
                    time.sleep(2)
                    response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    contributors = response.json()
                    
                    for contributor in contributors:
                        if contributor['author']['login'] == self.username:
                            for week in contributor['weeks']:
                                week_date = datetime.fromtimestamp(week['w'])
                                if week_date >= since_date:
                                    stats['additions'] += week['a']
                                    stats['deletions'] += week['d']
            
            except Exception as e:
                self.logger.warning(f"⚠️  Erreur stats code pour {repo_name}: {e}")
                continue
        
        stats['total_changes'] = stats['additions'] + stats['deletions']
        self.logger.info(f"✅ Modifications: +{stats['additions']} -{stats['deletions']}")
        return stats
    
    @rate_limit_aware
    def get_activity_heatmap(self, repos: List[Dict]) -> Dict[int, Dict[int, int]]:
        """
        Génère une heatmap d'activité par jour/heure
        
        Args:
            repos: Liste des dépôts
        
        Returns:
            Dictionnaire {jour: {heure: nombre_de_commits}}
        """
        if not self.config.get('stats.include_heatmap', True):
            return {}
        
        self.logger.info("🔥 Génération de la heatmap d'activité...")
        
        heatmap = {day: {hour: 0 for hour in range(24)} for day in range(7)}
        
        days_back = self.config.get('stats.days_back', 365)
        since_date = datetime.now() - timedelta(days=days_back)
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo['full_name']
            self.logger.debug(f"   [{i}/{len(repos)}] {repo_name}")
            
            try:
                url = f'{self.base_url}/repos/{repo_name}/commits'
                params = {
                    'author': self.username,
                    'since': since_date.isoformat(),
                    'per_page': 100
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    commits = response.json()
                    
                    for commit in commits:
                        date_str = commit['commit']['author']['date']
                        commit_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                        
                        day = commit_date.weekday()
                        hour = commit_date.hour
                        
                        heatmap[day][hour] += 1
            
            except Exception as e:
                self.logger.warning(f"⚠️  Erreur heatmap pour {repo_name}: {e}")
                continue
        
        self.logger.info("✅ Heatmap générée")
        return heatmap
    
    def calculate_all_stats(self) -> Dict[str, Any]:
        """
        Calcule toutes les statistiques disponibles
        
        Returns:
            Dictionnaire complet avec toutes les statistiques
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🚀 DÉBUT DU CALCUL DES STATISTIQUES")
        self.logger.info("=" * 60)
        
        # Afficher l'état du rate limit
        print(self.rate_limiter.get_status_message())
        
        stats = {}
        
        # Récupérer les repos
        repos = self.get_all_repos()
        
        # Stats de base
        stats['total_repos'] = len(repos)
        stats['public_repos'] = len([r for r in repos if not r['private']])
        stats['private_repos'] = len([r for r in repos if r['private']])
        
        # Étoiles
        stats['stars'] = self.count_stars(repos)
        
        # Commits
        stats['commits_last_year'] = self.count_commits_last_year(repos)
        
        # Pull Requests
        stats['prs'] = self.count_pull_requests(repos)
        
        # Issues
        stats['issues'] = self.count_issues(repos)
        
        # Contributions
        stats['contributed_repos'] = self.count_contributed_repos_last_year(repos)
        
        # Langages
        stats['languages'] = self.get_language_stats(repos)
        
        # Modifications de code
        stats['code_changes'] = self.get_code_changes_stats(repos)
        
        # Heatmap
        stats['activity_heatmap'] = self.get_activity_heatmap(repos)
        
        # Métadonnées
        stats['updated_at'] = datetime.now().isoformat()
        stats['period_days'] = self.config.get('stats.days_back', 365)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("✅ STATISTIQUES CALCULÉES AVEC SUCCÈS")
        self.logger.info("=" * 60)
        
        return stats
    
    def generate_profile_readme(self, stats: Dict[str, Any]) -> str:
        """
        Génère le README du profil avec les stats
        
        Args:
            stats: Dictionnaire des statistiques
        
        Returns:
            Contenu markdown du README
        """
        self.logger.info("📝 Génération du README...")
        
        sections = self.config.get('readme.sections', [])
        badge_style = self.config.get('readme.badge_style', 'for-the-badge')
        
        readme = f"""# 👋 Bonjour, je suis {self.username}!

## 📊 Statistiques GitHub Complètes (Publics + Privés)

<div align="center">

"""
        
        # Section: Statistiques générales
        if 'stats' in sections:
            readme += """### 🌟 Statistiques Générales

| Métrique | Valeur |
|----------|--------|
"""
            readme += f"| ⭐ Total Stars Earned | **{format_number(stats['stars'])}** |\n"
            readme += f"| 📝 Total Commits ({stats['period_days']} jours) | **{format_number(stats['commits_last_year'])}** |\n"
            readme += f"| 🔀 Total PRs | **{format_number(stats['prs']['total'])}** |\n"
            readme += f"| ❗ Total Issues | **{format_number(stats['issues']['total'])}** |\n"
            readme += f"| 📦 Repos Contribués | **{format_number(stats['contributed_repos'])}** |\n"
            
            if stats['code_changes']['total_changes'] > 0:
                readme += f"| ➕ Lignes Ajoutées | **{format_number(stats['code_changes']['additions'])}** |\n"
                readme += f"| ➖ Lignes Supprimées | **{format_number(stats['code_changes']['deletions'])}** |\n"
            
            readme += "\n"
        
        # Section: Dépôts
        if 'repos' in sections:
            readme += f"""### 📦 Dépôts

{create_badge_url('Total', stats['total_repos'], 'blue', badge_style)}
{create_badge_url('Public', stats['public_repos'], 'green', badge_style)}
{create_badge_url('Private', stats['private_repos'], 'orange', badge_style)}

"""
        
        # Section: Pull Requests
        if 'prs' in sections:
            readme += f"""### 🔀 Pull Requests Détaillées

{create_badge_url('Total', stats['prs']['total'], 'blue', badge_style)}
{create_badge_url('Open', stats['prs']['open'], 'green', badge_style)}
{create_badge_url('Merged', stats['prs']['merged'], 'purple', badge_style)}
{create_badge_url('Closed', stats['prs']['closed'], 'red', badge_style)}

"""
        
        # Section: Issues
        if 'issues' in sections:
            readme += f"""### ❗ Issues

{create_badge_url('Total', stats['issues']['total'], 'blue', badge_style)}
{create_badge_url('Open', stats['issues']['open'], 'green', badge_style)}
{create_badge_url('Closed', stats['issues']['closed'], 'red', badge_style)}

"""
        
        readme += "</div>\n\n---\n\n"
        
        # Section: Langages
        if 'languages' in sections and stats['languages']:
            readme += "## 💻 Langages les Plus Utilisés\n\n```\n"
            
            for lang, percentage in list(stats['languages'].items())[:10]:
                bar = generate_language_bar(percentage, length=40)
                readme += f"{lang:<20} {bar}\n"
            
            readme += "```\n\n---\n\n"
        
        # Section: Heatmap d'activité
        if 'activity' in sections and stats['activity_heatmap']:
            readme += "## 🔥 Heatmap d'Activité\n\n"
            readme += generate_heatmap_ascii(stats['activity_heatmap'])
            readme += "\n---\n\n"
        
        # Section: Graphique ASCII
        readme += "## 📈 Graphique ASCII\n\n```\n"
        
        max_value = max(stats['stars'], stats['commits_last_year'] // 10, 1)
        
        readme += f"Stars       : {generate_ascii_bar(stats['stars'], max_value, 50)} {format_number(stats['stars'])}\n"
        readme += f"Commits     : {generate_ascii_bar(stats['commits_last_year'] // 10, max_value, 50)} {format_number(stats['commits_last_year'])}\n"
        readme += f"PRs         : {generate_ascii_bar(stats['prs']['total'] * 3, max_value, 50)} {format_number(stats['prs']['total'])}\n"
        readme += f"Issues      : {generate_ascii_bar(stats['issues']['total'] * 3, max_value, 50)} {format_number(stats['issues']['total'])}\n"
        
        readme += "```\n\n---\n\n"
        
        # Section: Technologies
        if 'technologies' in sections:
            readme += """## 🛠️ Technologies & Compétences

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

---

"""
        
        # Section: Contact
        if 'contact' in sections:
            readme += f"""## 📫 Contact

[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:contact@example.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/{self.username})
[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/{self.username})

---

"""
        
        # Footer
        readme += f"""<div align="center">

  <img src="https://komarev.com/ghpvc/?username={self.username}&style=for-the-badge&color=blue" alt="Profile Views" />

</div>

"""
        
        if self.config.get('readme.include_update_time', True):
            update_time = datetime.now().strftime('%d/%m/%Y à %H:%M')
            readme += f"""<div align="center">

  <sub>📊 Stats mises à jour automatiquement le {update_time}</sub>

</div>
"""
        
        self.logger.info("✅ README généré")
        return readme
    
    @rate_limit_aware
    def update_profile_readme(self, content: str) -> Dict:
        """
        Met à jour le README du profil sur GitHub
        
        Args:
            content: Contenu markdown du README
        
        Returns:
            Réponse de l'API GitHub
        """
        self.logger.info("💾 Mise à jour du README sur GitHub...")
        
        url = f'{self.base_url}/repos/{self.username}/{self.username}/contents/README.md'
        
        # Récupérer le SHA du fichier actuel
        sha = None
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                sha = response.json()['sha']
                self.logger.debug(f"   SHA du fichier actuel: {sha[:7]}...")
        except Exception as e:
            self.logger.warning(f"⚠️  Impossible de récupérer le SHA: {e}")
        
        # Encoder en base64
        content_encoded = base64.b64encode(content.encode()).decode()
        
        # Préparer les données
        data = {
            'message': f'🤖 Auto-update stats - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            'content': content_encoded,
        }
        
        if sha:
            data['sha'] = sha
        
        # Envoyer la requête
        response = requests.put(url, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        
        self.logger.info("✅ README mis à jour sur GitHub")
        return response.json()

