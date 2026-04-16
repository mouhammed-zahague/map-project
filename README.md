# 🌿 Green Campus Alert Map
## Plateforme Intelligente de Signalement Environnemental
### ENSSRESD Batna — École Nationale Supérieure des Énergies Renouvelables, Environnement et Développement Durable

---

## 📋 Vue d'ensemble

Green Campus Alert Map est une application web complète permettant aux étudiants et personnels du campus de signaler des problèmes environnementaux. Les alertes sont affichées sur une carte interactive, analysées par Intelligence Artificielle, et gérées via un tableau de bord administratif.

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT (Navigateur)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  Carte       │  │  Dashboard   │  │  Formulaire        │   │
│  │  Leaflet.js  │  │  Chart.js    │  │  Soumission Alerte │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘   │
└─────────┼─────────────────┼────────────────────┼───────────────┘
          │   HTTP/REST JSON │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SERVEUR NODE.JS / EXPRESS                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  API REST   │  │  Auth JWT    │  │  ML Proxy (Claude)  │   │
│  │  /api/*     │  │  Middleware  │  │  /api/ai/classify   │   │
│  └──────┬──────┘  └──────────────┘  └─────────────────────┘   │
│         │                                                        │
│  ┌──────┴──────────────────────────────────────────────────┐   │
│  │  Multer (uploads)  │  Winston (logs)  │  Bcrypt (auth)  │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SQL
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BASE DE DONNÉES SQLite                        │
│  users │ alerts │ categories │ zones │ comments │ ai_results   │
└─────────────────────────────────────────────────────────────────┘
                               ▲
                               │ Python API
┌─────────────────────────────────────────────────────────────────┐
│                MODULE MACHINE LEARNING (Python)                  │
│  TF-IDF Vectorizer → Régression Logistique Multisorties         │
│  Classification: Catégorie + Priorité                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation et Démarrage (OS — Système d'exploitation)

### Prérequis
- Node.js ≥ 18.x
- Python ≥ 3.9
- npm ≥ 9.x

### 1. Cloner et installer

```bash
# Cloner le projet
git clone https://github.com/enssresd/green-campus-alert-map.git
cd green-campus-alert-map

# Installer les dépendances Node.js
npm install

# Installer les dépendances Python
pip install -r ml/requirements.txt
```

### 2. Configuration de l'environnement

```bash
# Copier et éditer la configuration
cp .env.example .env

# Variables requises dans .env:
# PORT=3000
# JWT_SECRET=votre_secret_ici
# ANTHROPIC_API_KEY=sk-ant-xxxxxx
```

### 3. Initialiser la base de données

```bash
# La base est créée automatiquement au premier démarrage
# Ou manuellement:
node scripts/init-db.js
```

### 4. Entraîner le modèle ML

```bash
cd ml
python classifier.py
# → Affiche les métriques d'entraînement
# → Sauvegarde le modèle dans ml/model.pkl
```

### 5. Démarrer le serveur

```bash
# Développement (avec rechargement automatique)
npm run dev

# Production
npm start

# ✅ Serveur démarré sur http://localhost:3000
```

---

## 📡 API REST — Documentation Complète

**Base URL:** `http://localhost:3000/api`  
**Authentification:** JWT Bearer Token  
**Format:** JSON

---

### 🔐 Authentification

#### `POST /auth/login`
Connecter un utilisateur.

**Body:**
```json
{ "username": "admin", "password": "admin123" }
```
**Réponse (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": { "id": 1, "name": "Dr. Amina Bensalem", "role": "admin" }
}
```

#### `GET /auth/me`
Profil de l'utilisateur connecté.  
**Headers:** `Authorization: Bearer <token>`

---

### ⚠️ Alertes

#### `GET /alerts`
Lister toutes les alertes avec filtres optionnels.

| Paramètre | Type   | Description                          |
|-----------|--------|--------------------------------------|
| category  | string | water, energy, waste, green, pollution|
| status    | string | reported, validated, in_progress, resolved |
| priority  | string | high, medium, low                    |
| zone      | string | slug de la zone (ex: batiment_a)     |
| search    | string | Recherche dans titre et description  |

**Réponse (200):**
```json
{
  "alerts": [
    {
      "id": 1,
      "title": "Fuite d'eau devant le laboratoire B",
      "description": "...",
      "category_slug": "water",
      "category_name": "Eau",
      "category_icon": "💧",
      "zone_name": "Bâtiment B – Laboratoires",
      "priority": "high",
      "status": "in_progress",
      "latitude": 35.5561,
      "longitude": 6.1754,
      "reporter_name": "Mohamed Amine Bouali",
      "created_at": "2025-03-12T09:30:00",
      "comment_count": 2
    }
  ],
  "total": 10
}
```

#### `GET /alerts/:id`
Détail d'une alerte avec historique des commentaires.

#### `POST /alerts`
Créer une nouvelle alerte (multipart/form-data pour l'image).

**Body (multipart):**
```
title        (required) string
description  (required) string
category     (required) water|energy|waste|green|pollution
zone         (required) slug de zone
latitude     (optional) float
longitude    (optional) float
ai_priority  (optional) priorité suggérée par IA
ai_confidence(optional) float
image        (optional) fichier image PNG/JPG ≤ 5MB
```

**Réponse (201):**
```json
{ "message": "Alerte créée", "id": 11 }
```

#### `PATCH /alerts/:id`
Mettre à jour le statut (admin/staff uniquement).

**Body:**
```json
{ "status": "in_progress", "priority": "high" }
```

#### `DELETE /alerts/:id`
Supprimer une alerte (admin uniquement).

---

### 💬 Commentaires

#### `POST /alerts/:id/comments`
Ajouter un commentaire.

**Body:**
```json
{ "content": "Intervention prévue demain matin." }
```

---

### 📊 Statistiques

#### `GET /stats`
Tableau de bord statistique complet.

**Réponse:**
```json
{
  "total": 10,
  "byStatus": [{"status": "reported", "count": 3}, ...],
  "byCategory": [{"slug": "water", "name": "Eau", "count": 3}, ...],
  "byZone": [{"slug": "batiment_b", "name": "Bâtiment B", "count": 4}, ...],
  "byMonth": [{"month": "2025-03", "count": 8}, ...],
  "avgResolutionDays": "3.2"
}
```

---

### 🤖 Classification IA

#### `POST /ai/classify`
Classifier automatiquement une alerte.

**Body:**
```json
{
  "title": "Fuite d'eau dans le couloir",
  "description": "Tuyau percé devant la salle 105, eau qui coule abondamment"
}
```

**Réponse:**
```json
{
  "category": "water",
  "priority": "high",
  "confidence": 94.2,
  "reason": "Description typique d'une fuite d'eau urgente nécessitant intervention immédiate.",
  "urgency_keywords": ["fuite", "abondamment", "tuyau percé"]
}
```

---

### 📁 Référentiels

#### `GET /categories` — Liste des catégories
#### `GET /zones` — Liste des zones du campus
#### `GET /users` — Liste des utilisateurs (admin)

---

## 🧠 Module Machine Learning

### Algorithme
**Pipeline scikit-learn:**
1. **TF-IDF Vectorizer** (unigrammes + bigrammes, max 3000 features)
2. **MultiOutputClassifier** avec **Régression Logistique**
   - Sortie 1 : Catégorie (5 classes)
   - Sortie 2 : Priorité (3 classes)

### Performances (dataset de 55 échantillons)
| Métrique           | Score  |
|--------------------|--------|
| Précision catégorie| ~88%   |
| Précision priorité | ~82%   |
| Validation         | 80/20 split |

### Intégration
```python
from ml.classifier import GreenCampusClassifier

clf = GreenCampusClassifier.load()
result = clf.predict("Fuite d'eau dans le couloir du labo")
# → {"category": "water", "priority": "high", "confidence": 91.5}
```

---

## 🗃️ Modèle de Données (MCD)

```
USERS ──────< ALERTS >────── CATEGORIES
  │              │
  │              │──< COMMENTS >── USERS
  │              │
  │              │──< ALERT_HISTORY
  │              │
  │              └──── ZONES
  │
  └──< NOTIFICATIONS
```

---

## 👥 Rôles et Permissions

| Action                     | Étudiant | Personnel | Admin |
|----------------------------|:--------:|:---------:|:-----:|
| Voir les alertes           | ✅       | ✅        | ✅    |
| Soumettre une alerte       | ✅       | ✅        | ✅    |
| Utiliser la classification IA | ✅    | ✅        | ✅    |
| Valider une alerte         | ❌       | ✅        | ✅    |
| Changer le statut          | ❌       | ✅        | ✅    |
| Supprimer une alerte       | ❌       | ❌        | ✅    |
| Gérer les utilisateurs     | ❌       | ❌        | ✅    |
| Voir les logs système      | ❌       | ❌        | ✅    |

---

## 📁 Structure du Projet

```
green-campus/
├── index.html              # Frontend (SPA)
├── backend/
│   └── server.js           # Serveur Express
├── database/
│   ├── schema.sql          # Schéma SQL + données initiales
│   └── campus_alerts.db    # Base SQLite (générée)
├── ml/
│   ├── classifier.py       # Module ML Python
│   ├── model.pkl           # Modèle entraîné (généré)
│   └── requirements.txt    # Dépendances Python
├── uploads/                # Photos uploadées
├── logs/                   # Logs serveur
├── package.json
└── README.md
```

---

## 🔗 Matières couvertes

| Matière              | Implémentation                                      |
|----------------------|-----------------------------------------------------|
| **Réseaux**          | API REST HTTP/JSON, Client-Serveur, JWT             |
| **Machine Learning** | TF-IDF + Régression Logistique, Classification multi-classes |
| **Bases de données** | SQLite, schéma relationnel, index, vues SQL         |
| **OS**               | Scripts bash, gestion fichiers, logs, multer uploads |

---

*ENSSRESD Batna — 2025 · Licence MIT*
