---
title: OCR P5 Energy API
colorFrom: green
colorTo: purple
sdk: docker
pinned: false
---

# OCR P5 Energy API

Ce projet a été réalisé dans le cadre du projet OpenClassrooms P5 : **Déployez un modèle de Machine Learning**.

L’objectif est de déployer une API de prédiction de consommation énergétique à partir d’un modèle de Machine Learning entraîné sur les données de bâtiments de Seattle.

Le modèle utilisé est un modèle de régression permettant d’estimer la consommation énergétique d’un bâtiment à partir de ses caractéristiques.

## Déploiement

L’API est déployée sur Hugging Face Spaces.

URL de l’application :

```text
https://ldesa-ocr-p5-energy-api.hf.space/
```

Documentation Swagger/OpenAPI :

```text
https://ldesa-ocr-p5-energy-api.hf.space/docs
```

## API FastAPI

### Endpoints disponibles

| Méthode | Endpoint        | Description                                          |
| ------- | --------------- | ---------------------------------------------------- |
| GET     | `/`             | Page d’accueil de l’API                              |
| GET     | `/health`       | Vérification de l’état de l’API                      |
| GET     | `/model-info`   | Informations sur le modèle chargé                    |
| GET     | `/sample-input` | Génère un exemple d’entrée compatible avec le modèle |
| POST    | `/predict`      | Retourne une prédiction de consommation énergétique  |

### Exemple d’utilisation de `/sample-input`

Le endpoint `/sample-input` retourne un exemple réaliste généré à partir du jeu de données brut des bâtiments de Seattle.

```bash
curl -s "https://ldesa-ocr-p5-energy-api.hf.space/sample-input" | python3 -m json.tool
```

### Exemple d’appel à `/predict`

Il est possible de récupérer un exemple aléatoire, puis de l’envoyer directement au modèle :

```bash
curl -s "https://ldesa-ocr-p5-energy-api.hf.space/sample-input" > /tmp/sample_input.json

curl -s -X POST "https://ldesa-ocr-p5-energy-api.hf.space/predict" \
  -H "Content-Type: application/json" \
  -d @/tmp/sample_input.json | python3 -m json.tool
```

Exemple de réponse obtenue :

```json
{
  "predicted_site_energy_use_kbtu": 1313220.69,
  "predicted_site_energy_use_gwh": 0.3849,
  "audit_priority": "priorité normale",
  "model_type": "RandomForestRegressor",
  "model_version": "local-v0.1.0"
}
```

## CI/CD

Le projet utilise GitHub Actions pour automatiser les tests et le déploiement.

Le workflow est défini dans :

```text
.github/workflows/ci-cd.yml
```

Le pipeline contient deux étapes principales :

1. **Lint and test API**

   - installation des dépendances ;
   - vérification du style avec Flake8 ;
   - exécution des tests avec Pytest ;
   - génération d’un rapport de couverture avec pytest-cov.

2. **Deploy to Hugging Face Space**

   - déploiement automatique vers Hugging Face Spaces après validation des tests ;
   - utilisation du secret GitHub `HF_TOKEN` pour sécuriser l’authentification.

Les commandes exécutées localement pour vérifier la qualité du projet sont :

```bash
flake8 app tests
pytest tests -v --cov=app --cov-report=term-missing
```

État actuel des tests :

```text
6 passed
coverage 96%
```

Le déploiement est effectué automatiquement lorsqu’une modification est intégrée à la branche `main`.

## État actuel du projet

À ce stade, les éléments suivants sont fonctionnels :

```text
API FastAPI opérationnelle
Documentation Swagger disponible
Endpoint /sample-input dynamique
Endpoint /predict fonctionnel
Tests Pytest validés
Contrôle qualité Flake8 validé
Pipeline CI/CD GitHub Actions fonctionnel
Déploiement automatique vers Hugging Face Spaces
```

## Prochaine étape

La prochaine étape du projet consiste à intégrer PostgreSQL afin de stocker les données, tracer les entrées envoyées au modèle et enregistrer les prédictions produites par l’API.
