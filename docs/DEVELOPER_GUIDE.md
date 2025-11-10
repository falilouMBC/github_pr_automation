# 🔧 Guide du Développeur

Guide complet pour comprendre, modifier et étendre GitHub Stats Automation.

---

## 📚 Table des Matières

- [Architecture](#-architecture)
- [Modules Détaillés](#-modules-détaillés)
- [Flux d'Exécution](#-flux-dexécution)
- [API GitHub](#-api-github)
- [Système de Cache](#-système-de-cache)
- [Rate Limiting](#-rate-limiting)
- [Logging](#-logging)
- [Ajouter des Fonctionnalités](#-ajouter-des-fonctionnalités)
- [Tests](#-tests)
- [Bonnes Pratiques](#-bonnes-pratiques)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    update_stats.py                      │
│                  (Point d'entrée)                       │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌──────────────┐
│    Config     │         │ GitHubStats  │
│   Manager     │────────▶│   Private    │
└───────────────┘         └──────┬───────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │  Cache   │  │   Rate   │  │  Utils   │
            │ Manager  │  │ Limiter  │  │          │
            └──────────┘  └──────────┘  └──────────┘
```

### Principes de Design

1. **Séparation des responsabilités** : Chaque module a un rôle précis
2. **Réutilisabilité** : Les modules sont indépendants
3. **Extensibilité** : Facile d'ajouter de nouvelles fonctionnalités
4. **Robustesse** : Gestion d'erreurs et retry automatiques

---

## 🧩 Modules Détaillés

### 1. **config.py** - Gestionnaire de Configuration

#### Responsabilités
- Chargement de la configuration YAML
- Gestion des variables d'environnement
- Validation des paramètres
- Valeurs par défaut

#### Classes Principales

```python
class Config:
    def __init__(self, config_file: str = 'configs/config.yaml')
    def load(self) -> None
    def save(self) -> None
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    def validate(self) -> tuple[bool, list[str]]
```

#### Exemple d'Utilisation

```python
from src.config import Config

# Charger la config
config = Config('configs/config.yaml')

# Récupérer une valeur
token = config.get('github.token')
days_back = config.get('stats.days_back', 365)

# Modifier une valeur
config.set('cache.enabled', False)
config.save()

# Valider
is_valid, errors = config.validate()
if not is_valid:
    for error in errors:
        print(error)
```

#### Ordre de Priorité

1. Variables d'environnement (priorité max)
2. Fichier config.yaml
3. Valeurs par défaut (dans le code)

---

### 2. **cache_manager.py** - Système de Cache

#### Responsabilités
- Stockage des réponses API en JSON
- Vérification de la validité temporelle
- Gestion du cycle de vie du cache

#### Classes Principales

```python
class CacheManager:
    def __init__(self, cache_dir: str = '.cache')
    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]
    def set(self, key: str, data: Any) -> bool
    def delete(self, key: str) -> bool
    def clear(self) -> int
    def get_cache_info(self) -> Dict[str, Any]
```

#### Exemple d'Utilisation

```python
from src.cache_manager import CacheManager

cache = CacheManager('.cache')

# Vérifier le cache
data = cache.get('repos_username', max_age_hours=24)
if data:
    print("Données en cache!")
else:
    # Récupérer depuis l'API
    data = fetch_from_api()
    cache.set('repos_username', data)

# Nettoyer
cache.clear()
```

#### Format de Stockage

```
.cache/
├── a1b2c3d4e5f6.json  # Hash MD5 de la clé
├── f6e5d4c3b2a1.json
└── .gitignore
```

Chaque fichier JSON contient les données brutes de l'API.

---

### 3. **rate_limiter.py** - Gestion du Rate Limit

#### Responsabilités
- Vérification du rate limit GitHub
- Attente automatique si nécessaire
- Affichage de barres de progression

#### Classes Principales

```python
class RateLimitHandler:
    def __init__(self, headers: Dict, min_remaining: int = 100)
    def check_rate_limit(self) -> Dict[str, any]
    def wait_if_needed(self, force_check: bool = False) -> bool
    def get_status_message(self) -> str
```

#### Décorateurs

```python
@rate_limit_aware
def my_api_call(self):
    # Vérifie automatiquement le rate limit avant l'appel
    pass

@with_retry(max_retries=3, delay=2)
def my_api_call(self):
    # Réessaie automatiquement en cas d'erreur
    pass
```

#### Exemple d'Utilisation

```python
from src.rate_limiter import RateLimitHandler, rate_limit_aware

limiter = RateLimitHandler(headers)

# Vérifier manuellement
limiter.wait_if_needed()

# Ou utiliser le décorateur
class MyClass:
    @rate_limit_aware
    def fetch_data(self):
        # Le rate limit est vérifié automatiquement
        response = requests.get(url, headers=self.headers)
        return response.json()
```

#### Limites de l'API GitHub

- **Avec authentification** : 5000 requêtes/heure
- **Sans authentification** : 60 requêtes/heure
- **Endpoint /rate_limit** : Ne compte pas dans le quota

---

### 4. **github_stats.py** - Collecteur de Statistiques

#### Responsabilités
- Communication avec l'API GitHub
- Collecte de toutes les statistiques
- Génération du README
- Publication sur GitHub

#### Classes Principales

```python
class GitHubStatsPrivate:
    def __init__(self, token: str, username: str, config: Optional[Config] = None)
    
    # Méthodes de collecte
    def get_all_repos(self) -> List[Dict]
    def count_stars(self, repos: List[Dict]) -> int
    def count_commits_last_year(self, repos: List[Dict]) -> int
    def count_pull_requests(self, repos: List[Dict]) -> Dict[str, int]
    def count_issues(self, repos: List[Dict]) -> Dict[str, int]
    def get_language_stats(self, repos: List[Dict]) -> Dict[str, float]
    def get_code_changes_stats(self, repos: List[Dict]) -> Dict[str, int]
    def get_activity_heatmap(self, repos: List[Dict]) -> Dict[int, Dict[int, int]]
    
    # Méthodes principales
    def calculate_all_stats(self) -> Dict[str, Any]
    def generate_profile_readme(self, stats: Dict[str, Any]) -> str
    def update_profile_readme(self, content: str) -> Dict
```

#### Exemple d'Utilisation Complète

```python
from src.github_stats import GitHubStatsPrivate
from src.config import Config

# Initialiser
config = Config()
stats_manager = GitHubStatsPrivate(
    token='ghp_...',
    username='johndoe',
    config=config
)

# Calculer les stats
stats = stats_manager.calculate_all_stats()

# Générer le README
readme = stats_manager.generate_profile_readme(stats)

# Publier
result = stats_manager.update_profile_readme(readme)
```

---

### 5. **utils.py** - Utilitaires

#### Fonctions Principales

```python
# Formatage
format_number(num: int) -> str
format_percentage(value: float, total: float) -> str
format_duration(seconds: int) -> str
format_relative_time(date: datetime) -> str

# Graphiques ASCII
generate_ascii_bar(value: int, max_value: int, length: int = 50) -> str
generate_language_bar(percentage: float, length: int = 40) -> str
generate_heatmap_ascii(heatmap: Dict) -> str

# Badges
create_badge_url(label: str, message: str, color: str) -> str

# Validation
validate_github_token(token: str) -> bool
validate_github_username(username: str) -> bool

# Helpers
safe_divide(numerator: float, denominator: float) -> float
get_date_range(days: int) -> tuple[datetime, datetime]
chunk_list(lst: List, chunk_size: int) -> List[List]
```

---

## 🔄 Flux d'Exécution

### Diagramme de Séquence

```
Utilisateur
    │
    ├─► update_stats.py
    │       │
    │       ├─► Config.load()
    │       │       │
    │       │       └─► Charger config.yaml + env vars
    │       │
    │       ├─► GitHubStatsPrivate()
    │       │       │
    │       │       ├─► Initialiser cache
    │       │       ├─► Initialiser rate_limiter
    │       │       └─► Initialiser logger
    │       │
    │       ├─► calculate_all_stats()
    │       │       │
    │       │       ├─► get_all_repos()
    │       │       │       │
    │       │       │       ├─► Vérifier cache
    │       │       │       ├─► Si pas de cache: API call
    │       │       │       └─► Mettre en cache
    │       │       │
    │       │       ├─► count_stars()
    │       │       ├─► count_commits_last_year()
    │       │       │       │
    │       │       │       └─► Pour chaque repo:
    │       │       │               │
    │       │       │               ├─► Vérifier rate limit
    │       │       │               └─► GET /repos/.../commits
    │       │       │
    │       │       ├─► count_pull_requests()
    │       │       ├─► count_issues()
    │       │       ├─► get_language_stats()
    │       │       ├─► get_code_changes_stats()
    │       │       └─► get_activity_heatmap()
    │       │
    │       ├─► generate_profile_readme()
    │       │       │
    │       │       └─► Formater en Markdown
    │       │
    │       └─► update_profile_readme()
    │               │
    │               ├─► GET README.md (récupérer SHA)
    │               ├─► Encoder en base64
    │               └─► PUT README.md
    │
    └─► Afficher résumé
```

---

## 🌐 API GitHub

### Endpoints Utilisés

#### 1. Repositories

```http
GET /user/repos?per_page=100&page=1&type=owner&sort=updated
```

**Retourne** : Liste de tous les repos (publics + privés)

#### 2. Commits

```http
GET /repos/{owner}/{repo}/commits?author={username}&since={date}&per_page=100
```

**Retourne** : Commits d'un repo par un auteur depuis une date

#### 3. Pull Requests

```http
GET /repos/{owner}/{repo}/pulls?state=all&creator={username}&per_page=100
```

**Retourne** : PRs créées par l'utilisateur

#### 4. Issues

```http
GET /repos/{owner}/{repo}/issues?state=all&creator={username}&per_page=100
```

**Retourne** : Issues créées (exclut les PRs via filtrage)

#### 5. Langages

```http
GET /repos/{owner}/{repo}/languages
```

**Retourne** : Bytes de code par langage

#### 6. Statistiques Contributeurs

```http
GET /repos/{owner}/{repo}/stats/contributors
```

**Retourne** : Additions/suppressions par semaine

⚠️ **Attention** : Peut retourner 202 si les stats sont en cours de génération

#### 7. Rate Limit

```http
GET /rate_limit
```

**Retourne** : État actuel du rate limit

#### 8. Update README

```http
PUT /repos/{owner}/{repo}/contents/README.md
```

**Body** :
```json
{
  "message": "Update stats",
  "content": "base64_encoded_content",
  "sha": "existing_file_sha"
}
```

---

## 💾 Système de Cache

### Architecture

```
Cache Layer
    │
    ├─► Clé : MD5(identifiant unique)
    │   Exemples :
    │   - "repos_username"
    │   - "commits_username_reponame"
    │   - "languages_username"
    │
    ├─► Valeur : JSON sérialisé
    │   {
    │     "data": {...},
    │     "timestamp": "2024-01-01T00:00:00"
    │   }
    │
    └─► Validité : Basée sur la durée (heures)
```

### Stratégie de Cache

#### Quoi mettre en cache ?

✅ **À cacher** :
- Liste des repositories (change rarement)
- Statistiques de langages (stable)
- Statistiques de commits (par période)

❌ **À ne pas cacher** :
- Rate limit (doit être à jour)
- État en temps réel

#### Durée de Validité Recommandée

| Donnée | Durée | Raison |
|--------|-------|--------|
| Repos | 24h | Change rarement |
| Commits | 6h | Peut changer plusieurs fois/jour |
| Langages | 48h | Très stable |
| Stats contributeurs | 24h | Génération lente côté GitHub |

---

## ⏱️ Rate Limiting

### Stratégie

1. **Vérification proactive**
   - Check toutes les 5 secondes minimum
   - Si remaining < 100 → Warning
   - Si remaining < min_threshold → Wait

2. **Attente intelligente**
   - Calcul du temps jusqu'au reset
   - Barre de progression pendant l'attente
   - +5 secondes de marge

3. **Décorateurs**
   ```python
   @rate_limit_aware  # Vérifie avant chaque appel
   @with_retry        # Réessaie en cas d'erreur 403
   ```

### Optimisations

- **Pagination intelligente** : Arrêt dès qu'il n'y a plus de données
- **Limite de pages** : `max_commits_pages` pour éviter trop de requêtes
- **Cache** : Réduit drastiquement les appels

---

## 📊 Logging

### Niveaux

- **DEBUG** : Détails pour le développement
- **INFO** : Flux normal d'exécution
- **WARNING** : Avertissements non-bloquants
- **ERROR** : Erreurs bloquantes

### Configuration

```python
logging:
  level: INFO
  directory: logs
  max_size_mb: 10
  backup_count: 5
```

### Exemple

```python
self.logger.debug(f"Processing repo: {repo_name}")
self.logger.info(f"✅ {len(repos)} repos retrieved")
self.logger.warning(f"⚠️ Rate limit low: {remaining}")
self.logger.error(f"❌ Failed to fetch: {error}")
```

---

## ➕ Ajouter des Fonctionnalités

### 1. Nouvelle Statistique

**Exemple** : Compter les forks

```python
# Dans github_stats.py

def count_forks(self, repos: List[Dict]) -> int:
    """Compte le nombre total de forks"""
    total = sum(repo['forks_count'] for repo in repos)
    self.logger.info(f"🍴 Total forks: {total}")
    return total

# Dans calculate_all_stats()
stats['forks'] = self.count_forks(repos)

# Dans generate_profile_readme()
readme += f"| 🍴 Total Forks | **{format_number(stats['forks'])}** |\n"
```

### 2. Nouveau Module

**Exemple** : Analyser les actions GitHub

```python
# src/actions_analyzer.py

class ActionsAnalyzer:
    def __init__(self, headers: Dict):
        self.headers = headers
        self.base_url = 'https://api.github.com'
    
    def get_workflow_runs(self, repo: str) -> List[Dict]:
        """Récupère les exécutions de workflows"""
        url = f'{self.base_url}/repos/{repo}/actions/runs'
        response = requests.get(url, headers=self.headers)
        return response.json()['workflow_runs']
```

### 3. Nouveau Format de Sortie

**Exemple** : Export en HTML

```python
# src/html_generator.py

class HTMLGenerator:
    def generate(self, stats: Dict) -> str:
        """Génère un rapport HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GitHub Stats</title>
        </head>
        <body>
            <h1>Statistiques de {stats['username']}</h1>
            <p>Stars: {stats['stars']}</p>
        </body>
        </html>
        """
        return html
```

---

## 🧪 Tests

### Structure

```python
# tests/test_cache_manager.py

import pytest
from src.cache_manager import CacheManager

@pytest.fixture
def cache():
    return CacheManager('.test_cache')

def test_set_and_get(cache):
    cache.set('test_key', {'data': 'value'})
    result = cache.get('test_key')
    assert result == {'data': 'value'}

def test_expiration(cache):
    cache.set('test_key', {'data': 'value'})
    result = cache.get('test_key', max_age_hours=0)
    assert result is None
```

### Exécution

```bash
# Installer pytest
pip install pytest pytest-cov

# Lancer les tests
pytest tests/

# Avec couverture
pytest --cov=src tests/
```

---

## ✅ Bonnes Pratiques

### Code Style

```python
# ✅ Bon
def get_repos(self) -> List[Dict]:
    """
    Récupère tous les repositories
    
    Returns:
        Liste de dictionnaires représentant les repos
    """
    repos = []
    # ...
    return repos

# ❌ Mauvais
def get_repos(self):
    repos = []
    # ...
    return repos
```

### Gestion d'Erreurs

```python
# ✅ Bon
try:
    response = requests.get(url, headers=self.headers, timeout=30)
    response.raise_for_status()
    return response.json()
except requests.exceptions.Timeout:
    self.logger.error("Timeout while fetching data")
    return None
except requests.exceptions.HTTPError as e:
    self.logger.error(f"HTTP error: {e}")
    return None

# ❌ Mauvais
try:
    response = requests.get(url)
    return response.json()
except:
    return None
```

### Logging

```python
# ✅ Bon
self.logger.info(f"Processing {len(repos)} repos")
self.logger.debug(f"Repo details: {repo}")
self.logger.warning(f"Skipping repo {name}: no commits")

# ❌ Mauvais
print("Processing repos")
```

### Performance

```python
# ✅ Bon - Arrêt anticipé
for repo in repos:
    if repo['private'] and not self.config.get('stats.include_private'):
        continue
    process_repo(repo)

# ❌ Mauvais - Traite tout
for repo in repos:
    if repo['private']:
        if self.config.get('stats.include_private'):
            process_repo(repo)
    else:
        process_repo(repo)
```

---

## 📖 Ressources

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Python Requests Library](https://requests.readthedocs.io/)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Contributeurs, bienvenue ! 🎉**

Ce guide est en constante évolution. N'hésitez pas à proposer des améliorations !

