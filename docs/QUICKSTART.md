# ⚡ Guide de Démarrage Rapide

Ce guide vous permettra de démarrer avec GitHub Stats Automation en **moins de 5 minutes** !

---

## 🚀 Étapes Rapides

### 1️⃣ Créer un Token GitHub (2 min)

1. Allez sur https://github.com/settings/tokens
2. Cliquez sur **"Generate new token (classic)"**
3. Nom : `GitHub Stats`
4. Cochez :
   - ✅ `repo` (tout)
   - ✅ `user` (tout)
5. Cliquez **"Generate token"**
6. **Copiez le token** (commence par `ghp_`)

### 2️⃣ Créer le Repository de Profil (1 min)

1. Allez sur https://github.com/new
2. Nom du repository : **EXACTEMENT votre username**
   - Si vous êtes `johndoe`, nommez-le `johndoe`
3. Cochez **"Public"**
4. Cochez **"Add a README file"**
5. Créez le repository

### 3️⃣ Installation (1 min)

```bash
# Cloner
git clone https://github.com/VOTRE_USERNAME/github_pr_automation.git
cd github_pr_automation

# Installer
pip install requests pyyaml

# Configurer
export GITHUB_TOKEN='votre_token_ghp_...'
export GITHUB_USERNAME='votre_username'
```

**Sur Windows PowerShell :**
```powershell
$env:GITHUB_TOKEN='votre_token'
$env:GITHUB_USERNAME='votre_username'
```

### 4️⃣ Lancer ! (30 sec)

```bash
# Test sans publier
python scripts/update_stats.py --dry-run

# Publier pour de vrai
python scripts/update_stats.py
```

### 5️⃣ Vérifier

Allez sur `https://github.com/VOTRE_USERNAME` → Votre README est mis à jour ! 🎉

---

## 🤖 Automatisation avec GitHub Actions (Bonus)

### 1. Configurer le Secret

Dans votre repo `username/username` :

1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Nom : `STATS_TOKEN`
4. Valeur : Votre token `ghp_...`
5. **Add secret**

### 2. Ajouter le Workflow

Créez `.github/workflows/update-stats.yml` :

```yaml
name: Update Stats
on:
  schedule:
    - cron: '0 0 * * *'  # Tous les jours à minuit
  workflow_dispatch:
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests pyyaml
      - run: python scripts/update_stats.py
        env:
          GITHUB_TOKEN: ${{ secrets.STATS_TOKEN }}
          GITHUB_USERNAME: ${{ github.repository_owner }}
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add README.md
          git commit -m "🤖 Update stats" || exit 0
          git push
```

### 3. Activer

Commitez le fichier → Le workflow s'exécute automatiquement !

---

## 🎯 Commandes Essentielles

```bash
# Mode normal
python scripts/update_stats.py

# Test sans publier
python scripts/update_stats.py --dry-run

# Force sans cache
python scripts/update_stats.py --no-cache

# Logs détaillés
python scripts/update_stats.py --verbose

# Tout nettoyer et relancer
python scripts/update_stats.py --clear-cache --no-cache
```

---

## ⚙️ Configuration Rapide

Éditez `configs/config.yaml` :

```yaml
stats:
  days_back: 365          # Période (jours)
  include_private: true   # Inclure privés
  include_languages: true # Langages
  include_heatmap: true   # Heatmap

cache:
  enabled: true           # Activer cache
  max_age_hours: 24       # Validité (h)

readme:
  sections:               # Sections à afficher
    - stats
    - repos
    - languages
```

---

## 🐛 Problèmes Courants

### ❌ "Token manquant"
```bash
export GITHUB_TOKEN='ghp_...'
export GITHUB_USERNAME='username'
```

### ❌ "Rate limit exceeded"
Attendez 1h ou activez le cache :
```yaml
cache:
  enabled: true
```

### ❌ "Repository not found"
Créez `username/username` (public)

### ❌ Le README ne s'affiche pas
1. Le repo doit être public
2. Le repo doit s'appeler exactement comme votre username
3. Le fichier doit s'appeler `README.md` (pas readme.md)

---

## 📊 Personnalisation Rapide

### Changer le Style des Badges

```yaml
readme:
  badge_style: "flat-square"
  # Options: flat, flat-square, plastic, for-the-badge
```

### Changer les Sections

```yaml
readme:
  sections:
    - stats        # Statistiques
    - repos        # Dépôts
    - prs          # Pull Requests
    - issues       # Issues
    - languages    # Langages
    - activity     # Heatmap
    - technologies # Tech stack
    - contact      # Contact
```

### Période d'Analyse

```yaml
stats:
  days_back: 180  # 6 mois au lieu d'un an
```

---

## 🎉 C'est Tout !

Votre profil GitHub affiche maintenant des statistiques automatiques et complètes !

**Prochaines étapes :**
- 📖 Lire [README_PROJECT.md](../README_PROJECT.md) pour la doc complète
- 🎨 Personnaliser votre template dans `templates/`
- 🤖 Configurer GitHub Actions pour l'automatisation
- ⭐ Donner une étoile au projet si ça vous plaît !

---

**Besoin d'aide ?** Ouvrez une [issue](https://github.com/VOTRE_USERNAME/github_pr_automation/issues) !

