---
title: OCR P5 Energy API
colorFrom: green
colorTo: purple
sdk: docker
pinned: false
---

# OCR P5 Energy API

Projet OpenClassrooms P5 — **Déployez un modèle de Machine Learning**.

Cette application expose, via une API FastAPI, un modèle de régression capable d’estimer la consommation énergétique annuelle d’un bâtiment non résidentiel de Seattle à partir de ses caractéristiques.

Le projet couvre l’ensemble de la chaîne d’industrialisation d’un modèle de machine learning :

- sérialisation et chargement du modèle ;
- validation des données avec Pydantic ;
- API FastAPI documentée avec Swagger/OpenAPI ;
- authentification par clé API ;
- persistance et traçabilité dans PostgreSQL ;
- tests unitaires, fonctionnels et d’intégration ;
- contrôle qualité avec Flake8 ;
- conteneurisation avec Docker ;
- pipeline CI/CD avec GitHub Actions ;
- déploiement sur Hugging Face Spaces.

## Liens

- API : `https://ldesa-ocr-p5-energy-api.hf.space/`
- Swagger/OpenAPI : `https://ldesa-ocr-p5-energy-api.hf.space/docs`
- Dépôt GitHub : `https://github.com/ludivinedesa/ocr-p5-energy-api`

## Architecture

```text
Client
  |
  | X-API-Key
  v
FastAPI
  |
  +--> Validation Pydantic
  |
  +--> Pipeline scikit-learn
  |      |
  |      +--> Prétraitements
  |      +--> RandomForestRegressor
  |
  +--> Réponse JSON
  |
  +--> Journalisation PostgreSQL optionnelle
         |
         +--> prediction_requests
         +--> prediction_results
         +--> model_versions
```

Principaux composants :

```text
app/
├── main.py                     # Routes FastAPI
├── schemas.py                  # Schémas Pydantic
├── security.py                 # Authentification X-API-Key
├── model_service.py            # Chargement et inférence du modèle
├── sample_service.py           # Exemple d’entrée aléatoire
├── database.py                 # Connexion PostgreSQL
├── prediction_repository.py    # Journalisation des requêtes/résultats
└── artifacts/
    ├── model_pipeline.joblib
    ├── model_metadata.json
    └── sample_inputs.json

scripts/
├── create_tables.sql
├── seed_model_versions.sql
├── load_buildings.py
├── generate_sample_inputs.py
└── retrain_model_compatibility.py

tests/
├── conftest.py
├── test_api.py
├── test_prediction_logging.py
└── test_database_integration.py
```

## Modèle de machine learning

Le modèle provient du Projet 3 OpenClassrooms sur la consommation énergétique des bâtiments de Seattle.

### Caractéristiques principales

- problème : régression ;
- cible : `SiteEnergyUse(kBtu)` ;
- algorithme : `RandomForestRegressor` ;
- nombre de lignes d’entraînement : 1 649 ;
- nombre de variables d’entrée : 17 ;
- transformation de la cible : `log1p` ;
- transformation inverse après prédiction : `expm1` ;
- version de scikit-learn utilisée pour l’artefact : `1.5.2`.

Le pipeline inclut les prétraitements numériques et catégoriels, puis le modèle de régression. L’artefact a été reconstruit avec scikit-learn 1.5.2 afin d’être compatible avec l’environnement de l’API.

### Performances

Résultats de validation croisée hors-échantillon :

| Métrique | Valeur |
|---|---:|
| MAE OOF | 4 305 223,10 kBtu |
| MAE OOF | 1,261736 GWh |
| R² OOF dans l’espace logarithmique | 0,69356 |

La réponse de l’API contient également une priorité d’audit simplifiée, destinée à illustrer une exploitation métier de la prédiction dans le cadre du POC.

## API FastAPI

### Endpoints

| Méthode | Endpoint | Accès | Description |
|---|---|---|---|
| GET | `/` | Public | Informations générales |
| GET | `/health` | Public | Vérification de disponibilité |
| GET | `/model-info` | Public | Métadonnées du modèle |
| GET | `/sample-input` | Public | Exemple valide aléatoire |
| POST | `/predict` | Clé API | Prédiction énergétique |

La documentation interactive est disponible sur `/docs`.

### Authentification

L’endpoint `POST /predict` exige une clé transmise dans l’en-tête HTTP :

```http
X-API-Key: votre_cle
```

La clé est lue depuis la variable d’environnement `API_KEY`.

- en local : valeur stockée dans `.env` ;
- sur Hugging Face : valeur stockée dans les secrets du Space ;
- dans les tests : valeur factice définie dans `tests/conftest.py` ;
- aucune clé réelle n’est enregistrée dans Git.

Une clé absente ou incorrecte retourne :

```json
{
  "detail": "Invalid or missing API key."
}
```

avec le statut HTTP `401`.

Si aucune clé n’est configurée côté serveur, `/predict` retourne un statut `503` afin d’éviter de rendre accidentellement l’endpoint public.

### Exemple complet

Récupérer un exemple :

```bash
curl -s \
  "https://ldesa-ocr-p5-energy-api.hf.space/sample-input" \
  > /tmp/sample_input.json
```

Envoyer la prédiction :

```bash
curl -s -X POST \
  "https://ldesa-ocr-p5-energy-api.hf.space/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  --data-binary @/tmp/sample_input.json \
  | python3 -m json.tool
```

Exemple de réponse :

```json
{
  "predicted_site_energy_use_kbtu": 1574535.22,
  "predicted_site_energy_use_gwh": 0.4615,
  "audit_priority": "priorité normale",
  "model_type": "RandomForestRegressor",
  "model_version": "local-v0.1.0"
}
```

Les valeurs numériques changent selon le bâtiment fourni.

## Installation locale

### Prérequis

- Python 3.10 recommandé ;
- Git ;
- Docker et Docker Compose pour PostgreSQL ;
- un environnement virtuel Python.

### Cloner et installer

```bash
git clone https://github.com/ludivinedesa/ocr-p5-energy-api.git
cd ocr-p5-energy-api

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Variables d’environnement

Créer le fichier local :

```bash
cp .env.example .env
```

Variables attendues :

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ocr_p5_energy
POSTGRES_USER=ocr_p5_user
POSTGRES_PASSWORD=change_me
DATABASE_LOGGING_ENABLED=false
API_KEY=replace_with_a_long_random_secret
```

Le fichier `.env` est ignoré par Git. Il ne doit jamais être envoyé dans le dépôt.

Pour générer une clé robuste :

```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
```

Copier ensuite la valeur dans `API_KEY` sans la publier.

### Lancer l’API sans PostgreSQL

Avec `DATABASE_LOGGING_ENABLED=false` :

```bash
python -m uvicorn app.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

Documentation locale :

```text
http://127.0.0.1:8000/docs
```

## PostgreSQL

### Schéma

La base contient quatre tables principales :

| Table | Rôle |
|---|---|
| `buildings` | Bâtiments issus du dataset Seattle |
| `model_versions` | Versions, chemins et métriques du modèle |
| `prediction_requests` | Entrées reçues, statut et erreurs |
| `prediction_results` | Prédictions, unité, priorité et version du modèle |

Relations principales :

- une requête de prédiction peut avoir un résultat ;
- un résultat référence une version du modèle ;
- la suppression d’une requête supprime automatiquement son résultat associé ;
- les contraintes SQL contrôlent les statuts autorisés et l’intégrité référentielle.

Des index sont définis sur les identifiants et dates utiles afin de faciliter les recherches.

### Démarrer PostgreSQL

```bash
docker compose up -d db
docker compose ps
```

Créer ou mettre à jour le schéma :

```bash
docker compose exec -T db sh -lc \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < scripts/create_tables.sql
```

Enregistrer la version du modèle :

```bash
docker compose exec -T db sh -lc \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < scripts/seed_model_versions.sql
```

Charger les 3 376 bâtiments :

```bash
python scripts/load_buildings.py
```

Le chargement est conçu pour pouvoir être relancé sans dupliquer les données.

### Activer la journalisation

Dans `.env` :

```env
DATABASE_LOGGING_ENABLED=true
```

Puis redémarrer l’API.

Le flux devient :

```text
POST /predict
  -> prediction_requests
  -> modèle ML
  -> prediction_results
  -> model_versions
```

En cas d’erreur lors de la prédiction, la requête est marquée avec le statut d’échec et le message correspondant.

## Docker Compose

La pile locale complète se lance avec :

```bash
docker compose up --build
```

Services :

- API exposée sur `http://localhost:8000` ;
- PostgreSQL exposé sur `localhost:5432`.

Le port interne du conteneur API est `7860`, mappé vers le port `8000` du Mac.

Dans Docker Compose, l’API utilise `POSTGRES_HOST=db`, car `db` est le nom réseau du service PostgreSQL.

Un healthcheck empêche l’API de démarrer avant que PostgreSQL accepte les connexions.

Arrêt :

```bash
docker compose down
```

Les données PostgreSQL persistent dans le volume `postgres_data`.

## Tests

### Tests unitaires et fonctionnels

Commande standard :

```bash
pytest tests -v \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=xml:logs/coverage.xml \
  --cov-report=html:htmlcov
```

Résultat validé :

```text
11 passed
5 skipped
```

Les cinq tests ignorés correspondent aux tests d’intégration PostgreSQL, désactivés par défaut afin que la suite standard ne dépende pas de Docker.

### Tests d’intégration PostgreSQL

Une base isolée `ocr_p5_energy_test` est utilisée afin de ne jamais modifier la base principale.

Commande :

```bash
RUN_DB_INTEGRATION_TESTS=true \
POSTGRES_TEST_DB=ocr_p5_energy_test \
pytest tests/test_database_integration.py -v
```

Contrôles effectués :

- présence des quatre tables ;
- insertion réelle d’une requête et de son résultat ;
- rejet d’un statut invalide ;
- rejet d’une clé étrangère inexistante ;
- suppression en cascade.

Résultat validé :

```text
5 passed
```

### Validation complète

Avec PostgreSQL actif et la base de test initialisée :

```bash
RUN_DB_INTEGRATION_TESTS=true \
POSTGRES_TEST_DB=ocr_p5_energy_test \
pytest tests -v \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=xml:logs/coverage.xml \
  --cov-report=html:htmlcov
```

Résultat validé :

```text
16 passed
```

Rapports générés :

- terminal : lignes non couvertes ;
- XML : `logs/coverage.xml` ;
- HTML : `htmlcov/index.html`.

Ouvrir le rapport HTML sur macOS :

```bash
open htmlcov/index.html
```

### Qualité du code

```bash
flake8 app scripts tests
```

Le contrôle Flake8 est validé sans erreur.

## CI/CD GitHub Actions

Le workflow se trouve dans :

```text
.github/workflows/ci-cd.yml
```

### Intégration continue

À chaque push ou Pull Request vers `main`, GitHub Actions :

1. récupère le dépôt ;
2. installe Python 3.10 ;
3. installe les dépendances ;
4. démarre un service PostgreSQL 16 temporaire ;
5. initialise les tables ;
6. insère la version du modèle ;
7. exécute Flake8 sur `app`, `scripts` et `tests` ;
8. exécute les 16 tests ;
9. génère les rapports XML et HTML de couverture ;
10. publie les rapports comme artefacts du workflow.

Les identifiants PostgreSQL utilisés dans la CI sont temporaires et limités au job.

### Déploiement continu

Après succès de la CI, un push sur `main` déclenche le déploiement automatique vers Hugging Face Spaces.

Le workflow utilise le secret GitHub :

```text
HF_TOKEN
```

La clé protégeant `/predict` n’est pas transférée par GitHub : elle est configurée directement comme secret `API_KEY` dans les paramètres du Space Hugging Face.

## Environnements

### Développement local

- API lancée avec Uvicorn ;
- `.env` local ;
- PostgreSQL facultatif ;
- journalisation activable avec `DATABASE_LOGGING_ENABLED`.

### Test

- Pytest définit une clé factice ;
- la base `ocr_p5_energy_test` est isolée ;
- les tests peuvent détruire et recréer leurs données sans toucher au développement ;
- GitHub Actions utilise un conteneur PostgreSQL temporaire.

### Production

- conteneur Docker sur Hugging Face Spaces ;
- clé `API_KEY` stockée dans les secrets du Space ;
- `HF_TOKEN` stocké dans GitHub Secrets ;
- journalisation PostgreSQL désactivée par défaut tant qu’aucune base distante n’est configurée.

## Sécurité et gestion des accès

Mesures appliquées :

- protection de `/predict` avec `X-API-Key` ;
- comparaison de secrets avec `hmac.compare_digest` ;
- secrets stockés dans `.env`, GitHub Secrets et Hugging Face Secrets ;
- `.env` ignoré par Git ;
- aucune clé réelle dans `.env.example` ;
- réponses `401` pour clé absente ou invalide ;
- réponse `503` si l’authentification serveur n’est pas configurée ;
- validation stricte des entrées avec Pydantic ;
- contraintes, clés étrangères et transactions PostgreSQL ;
- séparation entre base principale et base de test.

Le POC n’implémente pas de comptes utilisateurs ni de mots de passe. Le hachage de mots de passe n’est donc pas applicable. Pour une application multi-utilisateur, l’évolution attendue serait une authentification OAuth2/JWT, une gestion des rôles et une rotation automatisée des secrets.

## Besoins analytiques

Les données journalisées peuvent alimenter un tableau de bord de suivi avec notamment :

- nombre de prédictions par jour ou par période ;
- taux de succès et taux d’erreur ;
- temps de traitement moyen, si cette métrique est ajoutée ;
- consommation énergétique moyenne et médiane prédite ;
- répartition des priorités d’audit ;
- bâtiments les plus énergivores ;
- répartition par type de bâtiment et quartier ;
- fréquence d’utilisation des différentes versions du modèle ;
- suivi des erreurs de validation et de connexion ;
- comparaison future entre prédictions et valeurs réellement observées.

Ces indicateurs permettraient à la fois de suivre l’usage technique de l’API, d’identifier les bâtiments prioritaires pour un audit et de surveiller la performance du modèle dans le temps.

## Limites et améliorations possibles

- la clé API est un secret partagé et non une authentification nominative ;
- la base PostgreSQL de développement est locale ;
- la production Hugging Face ne journalise pas en base sans service PostgreSQL distant ;
- la priorité d’audit est une règle simplifiée de POC ;
- aucun tableau de bord n’est encore développé ;
- un suivi de dérive du modèle pourrait être ajouté ;
- la comparaison prédiction/réalité nécessiterait de nouvelles données observées ;
- des migrations versionnées, par exemple avec Alembic, amélioreraient la gestion du schéma.

## Versionnement Git

Le développement utilise :

- une branche principale `main` ;
- des branches dédiées aux fonctionnalités et corrections ;
- des Pull Requests avec validation CI ;
- un tag de version final prévu après le merge de la version livrable.

Le tag final recommandé est :

```bash
git tag -a v1.0.0 -m "Version finale du projet OCR P5"
git push origin v1.0.0
```
