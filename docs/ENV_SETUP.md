# 🔐 Configuration du Fichier .env

Guide complet pour configurer vos variables d'environnement.

---

## 📋 Qu'est-ce que le fichier .env ?

Le fichier `.env` permet de stocker vos **credentials sensibles** (token, username) sans les exposer dans le code ou la ligne de commande.

### Avantages :
- ✅ **Sécurité** : Vos secrets ne sont jamais commitées
- ✅ **Simplicité** : Pas besoin d'exporter manuellement les variables
- ✅ **Pratique** : Chargement automatique à chaque exécution

---

## 🚀 Configuration Rapide

### Étape 1 : Créer le fichier .env

À la **racine du projet**, créez un fichier nommé `.env` :

```bash
# Sur Linux/Mac
touch .env

# Sur Windows (PowerShell)
New-Item .env
```

### Étape 2 : Ajouter vos credentials

Éditez le fichier `.env` et ajoutez :

```bash
GITHUB_TOKEN=ghp_votre_token_ici
GITHUB_USERNAME=votre_username
```

**Exemple concret :**
```bash
GITHUB_TOKEN=ghp_1A2b3C4d5E6f7G8h9I0jKlMnOpQrStUvWxYz
GITHUB_USERNAME=johndoe
```

### Étape 3 : Vérifier la configuration

```bash
python scripts/check_env.py
```

Ce script va :
- ✅ Vérifier que le .env existe
- ✅ Valider le format du token
- ✅ Valider le format du username
- ✅ Tester la connexion à l'API GitHub

---

## 🔑 Comment Obtenir un Token GitHub

### 1. Aller sur GitHub Settings

Allez sur : https://github.com/settings/tokens

### 2. Générer un nouveau token

1. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
2. Donnez un nom : `GitHub Stats Automation`
3. **Sélectionnez les permissions** :

```
✅ repo
   ✅ repo:status
   ✅ repo_deployment
   ✅ public_repo
   ✅ repo:invite
   ✅ security_events

✅ user
   ✅ read:user
   ✅ user:email
   ✅ user:follow
```

4. Choisissez une expiration (recommandé : 90 jours)
5. Cliquez sur **"Generate token"**
6. **Copiez le token** (il commence par `ghp_`)

⚠️ **Important** : Copiez le token immédiatement ! Il ne sera plus affiché après.

### 3. Ajouter le token dans .env

```bash
GITHUB_TOKEN=ghp_le_token_que_vous_avez_copié
```

---

## 📝 Format du Fichier .env

### Structure de Base

```bash
# Commentaire : Les lignes commençant par # sont ignorées

# Token GitHub (OBLIGATOIRE)
GITHUB_TOKEN=ghp_votre_token

# Username GitHub (OBLIGATOIRE)
GITHUB_USERNAME=votre_username

# Configuration optionnelle
CACHE_ENABLED=true
LOG_LEVEL=INFO
```

### Avec Guillemets (Optionnel)

```bash
GITHUB_TOKEN="ghp_votre_token"
GITHUB_USERNAME='votre_username'
```

Les guillemets simples ou doubles sont automatiquement supprimés.

### Variables Optionnelles

```bash
# Activer/désactiver le cache
CACHE_ENABLED=true

# Niveau de logging (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Répertoire de cache
CACHE_DIRECTORY=.cache

# Durée du cache (heures)
CACHE_MAX_AGE_HOURS=24
```

---

## ✅ Vérification de la Configuration

### Script de Vérification

```bash
python scripts/check_env.py
```

**Ce script affiche :**

```
═══════════════════════════════════════════════════════════════
              🔍 VÉRIFICATION DE L'ENVIRONNEMENT
═══════════════════════════════════════════════════════════════

📁 Recherche du fichier .env...
✅ Fichier .env trouvé: C:\projet\.env

🔐 Vérification des variables requises...
✅ Toutes les variables requises sont présentes

═══════════════════════════════════════════════════════════════
                   🔐 VARIABLES D'ENVIRONNEMENT GITHUB
═══════════════════════════════════════════════════════════════
✅ GITHUB_TOKEN            : ghp_1A2b...wxYz
✅ GITHUB_USERNAME         : johndoe
═══════════════════════════════════════════════════════════════

🔑 Validation du token GitHub...
✅ Format du token valide

👤 Validation du username GitHub...
✅ Format du username valide

🌐 Test de connexion à l'API GitHub...
✅ Connexion réussie!
   Username: johndoe
   Nom: John Doe
   Repos publics: 15
   Repos privés: 8

📊 Rate Limit:
   Restantes: 4998/5000

═══════════════════════════════════════════════════════════════
                          📋 RÉSUMÉ
═══════════════════════════════════════════════════════════════

✅ Votre environnement est correctement configuré!

🚀 Vous pouvez maintenant exécuter:
   python scripts/update_stats.py --dry-run
```

---

## 🔒 Sécurité

### Le .env est-il sécurisé ?

✅ **OUI**, si vous suivez ces règles :

### 1. Ne JAMAIS committer le .env

Le fichier `.gitignore` inclut déjà `.env` :

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

### 2. Vérifier avant de commit

```bash
git status

# Assurez-vous que .env n'apparaît PAS dans la liste
```

### 3. Si vous avez accidentellement commité .env

```bash
# Supprimer du dépôt (garde le fichier local)
git rm --cached .env

# Commit
git commit -m "Remove .env from repository"

# IMPORTANT: Révoquez le token sur GitHub !
# https://github.com/settings/tokens
```

### 4. Utiliser des tokens avec expiration

Créez des tokens qui expirent après 30-90 jours pour limiter les risques.

---

## 🛠️ Dépannage

### Problème : "Fichier .env non trouvé"

**Solution 1** : Vérifier l'emplacement
```bash
# Le .env doit être à la racine du projet
github_pr_automation/
├── .env          ← ICI
├── src/
├── scripts/
└── ...
```

**Solution 2** : Créer le fichier
```bash
python scripts/check_env.py
# Répondez "o" pour créer un template
```

### Problème : "Token invalide"

**Causes possibles :**
1. Le token a expiré
2. Le token a été révoqué
3. Format incorrect (doit commencer par `ghp_`)

**Solution :**
Créez un nouveau token sur https://github.com/settings/tokens

### Problème : "Variables non chargées"

**Solution 1** : Vérifier le format
```bash
# ✅ BON
GITHUB_TOKEN=ghp_xxx

# ❌ MAUVAIS (espace autour du =)
GITHUB_TOKEN = ghp_xxx
```

**Solution 2** : Vérifier l'encodage
Le fichier doit être en **UTF-8** sans BOM.

### Problème : "Permission denied"

**Sur Linux/Mac :**
```bash
chmod 600 .env  # Rendre le fichier lisible uniquement par vous
```

---

## 📱 Utilisation sur Différents Systèmes

### Windows

```powershell
# Créer le fichier
New-Item .env

# Éditer
notepad .env
```

### Linux/Mac

```bash
# Créer le fichier
touch .env

# Éditer
nano .env
# ou
vim .env
# ou
code .env  # VS Code
```

---

## 🌍 Variables d'Environnement Système (Alternative)

Si vous préférez ne pas utiliser de fichier .env :

### Windows (PowerShell)

```powershell
$env:GITHUB_TOKEN="ghp_votre_token"
$env:GITHUB_USERNAME="votre_username"

# Permanent (toute la session)
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'ghp_xxx', 'User')
[System.Environment]::SetEnvironmentVariable('GITHUB_USERNAME', 'username', 'User')
```

### Linux/Mac (Bash)

```bash
export GITHUB_TOKEN="ghp_votre_token"
export GITHUB_USERNAME="votre_username"

# Permanent (ajouter dans ~/.bashrc ou ~/.zshrc)
echo 'export GITHUB_TOKEN="ghp_xxx"' >> ~/.bashrc
echo 'export GITHUB_USERNAME="username"' >> ~/.bashrc
```

---

## 📚 Ordre de Priorité

Le système charge les variables dans cet ordre (du plus prioritaire au moins) :

1. **Variables système** (`export` / `$env:`)
2. **Fichier .env** (à la racine)
3. **Fichier config.yaml** (configs/)
4. **Valeurs par défaut** (dans le code)

---

## ✅ Checklist Finale

Avant de lancer le script, vérifiez :

- [ ] Le fichier `.env` existe à la racine
- [ ] `GITHUB_TOKEN` est défini et commence par `ghp_`
- [ ] `GITHUB_USERNAME` est défini et correct
- [ ] Le `.env` n'est pas dans git (`.gitignore` l'inclut)
- [ ] `python scripts/check_env.py` réussit

---

## 🎯 Prochaines Étapes

Une fois le `.env` configuré :

```bash
# 1. Vérifier la config
python scripts/check_env.py

# 2. Test sans publier
python scripts/update_stats.py --dry-run

# 3. Publier pour de vrai
python scripts/update_stats.py
```

---

**Besoin d'aide ?** Ouvrez une [issue](https://github.com/VOTRE_USERNAME/github_pr_automation/issues) !

