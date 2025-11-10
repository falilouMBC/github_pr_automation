# 🚀 GitHub Stats Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Ready-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

**Système automatisé de statistiques GitHub incluant les dépôts privés**

[Installation](#-installation-rapide) • [Utilisation](#-utilisation) • [Documentation](#-documentation) • [Exemples](#-exemples)

</div>

---

## 🎯 À Propos

**GitHub Stats Automation** génère automatiquement des statistiques GitHub complètes et les affiche sur votre profil. L'avantage principal : **accès aux dépôts privés** pour des statistiques vraiment complètes !

### ✨ Fonctionnalités

- ✅ **Statistiques complètes** : Repos privés inclus
- ✅ **Automatisation** : GitHub Actions intégrée
- ✅ **Cache intelligent** : Optimise les requêtes API
- ✅ **Rate limit aware** : Gère automatiquement les limites
- ✅ **Personnalisable** : Configuration YAML complète
- ✅ **Sans dépendances** : Seulement `requests` et `pyyaml`

### 📊 Statistiques Collectées

- Dépôts (publics + privés)
- Commits sur période configurable
- Pull Requests (total, ouvertes, mergées)
- Issues (ouvertes, fermées)
- Étoiles totales
- Langages de programmation (avec %)
- Modifications de code (additions/suppressions)
- Heatmap d'activité

---

## ⚡ Installation Rapide

```bash
# 1. Cloner le repository
git clone https://github.com/falilouMBC/github_pr_automation.git
cd github_pr_automation

# 2. Installer les dépendances
pip install requests pyyaml

# 3. Configurer les credentials
# Créer un fichier .env à la racine
cat > .env << EOF
GITHUB_TOKEN=ghp_votre_token_ici
GITHUB_USERNAME=votre_username
EOF

# 4. Vérifier la configuration
python scripts/check_env.py

# 5. Tester (sans publier)
python scripts/update_stats.py --dry-run

# 6. Publier !
python scripts/update_stats.py
```

---

## 🔑 Créer un Token GitHub

1. Allez sur https://github.com/settings/tokens
2. **"Generate new token (classic)"**
3. Nom : `GitHub Stats Automation`
4. Permissions :
   - ✅ `repo` (Full control)
   - ✅ `user` (Read access)
5. Copiez le token (commence par `ghp_`)
6. Ajoutez dans `.env` : `GITHUB_TOKEN=ghp_...`

---

## 🎮 Utilisation

### Mode Basique

```bash
python scripts/update_stats.py
```

### Avec Options

```bash
# Test sans publier
python scripts/update_stats.py --dry-run

# Sans cache
python scripts/update_stats.py --no-cache

# Mode verbeux
python scripts/update_stats.py --verbose

# Export JSON
python scripts/update_stats.py --json stats/output.json

# Nettoyer le cache
python scripts/update_stats.py --clear-cache
```

### Vérifier la Configuration

```bash
# Vérifier .env, token, connexion API
python scripts/check_env.py
```

---

## 📁 Structure du Projet

```
github_pr_automation/
├── .github/workflows/
│   └── update-stats.yml       # GitHub Actions
├── configs/
│   ├── config.yaml            # Configuration
│   └── env.example            # Template .env
├── docs/
│   ├── QUICKSTART.md          # Guide rapide
│   ├── ENV_SETUP.md           # Config .env
│   └── DEVELOPER_GUIDE.md     # Guide dev
├── scripts/
│   ├── update_stats.py        # Script principal
│   └── check_env.py           # Vérification
├── src/
│   ├── github_stats.py        # Classe principale
│   ├── cache_manager.py       # Cache
│   ├── rate_limiter.py        # Rate limiting
│   ├── config.py              # Config
│   ├── env_loader.py          # Chargement .env
│   └── utils.py               # Utilitaires
├── templates/
│   └── profile_template.md    # Template README
├── exemples/
│   └── example_usage.py       # Exemples
├── .env                       # Vos credentials (à créer)
├── .gitignore                 # Fichiers ignorés
└── README.md                  # Vos stats de profil
```

---

## 🤖 Automatisation avec GitHub Actions

### Configuration

1. **Créer le repo de profil** : `votre_username/votre_username` (public)

2. **Ajouter le secret** :
   - Settings → Secrets → Actions
   - Nouveau secret : `STATS_TOKEN`
   - Valeur : Votre token `ghp_...`

3. **Copier le workflow** :
   ```bash
   cp .github/workflows/update-stats.yml ../votre_username/.github/workflows/
   ```

4. **Le workflow s'exécute** :
   - Tous les jours à minuit (UTC)
   - Manuellement via l'interface

---

## 📊 Exemples de Sorties

### Console

```
═══════════════════════════════════════════════════════════════
📊 RÉSUMÉ DES STATISTIQUES
═══════════════════════════════════════════════════════════════

📦 DÉPÔTS
   Total                :              26
   └─ Publics           :              17
   └─ Privés            :               9

⭐ ÉTOILES
   Total                :               7

📝 COMMITS
   Derniers 365 jours   :              95

🔀 PULL REQUESTS
   Total                :              23
   ├─ Ouvertes          :               0
   ├─ Mergées           :              23
   └─ Fermées           :              23

💻 TOP 5 LANGAGES
   1. Java                      :      34.1%
   2. TypeScript                :      33.2%
   3. PHP                       :      11.2%
   4. Blade                     :       8.7%
   5. HTML                      :       3.9%
```

### README Généré

Voir votre profil : https://github.com/falilouMBC

---

## ⚙️ Configuration

Éditez `configs/config.yaml` :

```yaml
github:
  token: ""  # Chargé depuis .env
  username: ""

stats:
  days_back: 365              # Période d'analyse
  include_private: true       # Inclure privés
  include_languages: true     # Analyser langages
  include_heatmap: true       # Heatmap d'activité

cache:
  enabled: true               # Activer cache
  max_age_hours: 24           # Validité

readme:
  sections:                   # Sections à afficher
    - stats
    - repos
    - languages
    - activity
  badge_style: "for-the-badge"
```

---

## 🎨 Personnalisation

### Changer les Sections

```yaml
readme:
  sections:
    - header
    - stats
    - repos
    - prs
    - issues
    - languages
    - activity
    - technologies
    - contact
```

### Changer le Style

```yaml
readme:
  badge_style: "flat-square"  # flat, flat-square, for-the-badge
```

### Période d'Analyse

```yaml
stats:
  days_back: 180  # 6 mois au lieu d'un an
```

---

## 📚 Documentation

- 📖 [Guide de Démarrage Rapide](docs/QUICKSTART.md)
- 📖 [Configuration .env](docs/ENV_SETUP.md)
- 📖 [Guide du Développeur](docs/DEVELOPER_GUIDE.md)
- 📖 [Exemples d'Utilisation](exemples/example_usage.py)

---

## 🔧 Dépannage

### "Token manquant"

```bash
# Vérifier que .env existe et contient
cat .env

# Doit afficher :
# GITHUB_TOKEN=ghp_...
# GITHUB_USERNAME=...
```

### "Rate limit exceeded"

```bash
# Activer le cache
# Dans config.yaml :
cache:
  enabled: true
  max_age_hours: 24
```

### Le README ne s'affiche pas

1. Le repo doit être **public**
2. Le repo doit s'appeler **exactement** comme votre username
3. Le fichier doit s'appeler `README.md`

---

## 🤝 Contribution

Les contributions sont bienvenues !

1. Fork le projet
2. Créer une branche : `git checkout -b feature/ma-feature`
3. Commit : `git commit -m 'Ajout de ma feature'`
4. Push : `git push origin feature/ma-feature`
5. Ouvrir une Pull Request

---

## 📝 Licence

Ce projet est sous licence MIT.

---

## 🙏 Remerciements

- [GitHub API](https://docs.github.com/en/rest)
- [Shields.io](https://shields.io/)
- Communauté open source

---

## 📞 Support

- 🐛 [Signaler un bug](https://github.com/falilouMBC/github_pr_automation/issues)
- 💡 [Demander une fonctionnalité](https://github.com/falilouMBC/github_pr_automation/issues)
- 💬 [Discussions](https://github.com/falilouMBC/github_pr_automation/discussions)

---

<div align="center">

**Fait avec ❤️ pour automatiser les statistiques GitHub**

⭐ **Si ce projet vous aide, donnez-lui une étoile !** ⭐

</div>

