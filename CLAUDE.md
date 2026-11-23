# CLAUDE.md

## Projet
Radar quotidien des news IA : récupère les posts depuis l'API Hacker News, les classe avec Gemini, écrit un digest Markdown dans `digests/`, génère le dashboard statique `docs/index.html` (GitHub Pages) et les meilleurs repos GitHub de la semaine. Une GitHub Action tourne chaque jour.

## Commandes
- Installer : `pip install -r requirements-dev.txt`
- Tests : `pytest` (config dans `pyproject.toml`, testpaths = `tests`)

## Structure
- `radar/` : code du pipeline (hn, filters, storage, classifier, digest, site, trends, github)
- `tests/` : tests pytest
- `data/posts.csv` et `digests/` : générés par l'Action, ne pas éditer à la main
- `docs/index.html` : dashboard généré depuis `radar/dashboard.html` par `python -m radar site`, ne pas éditer à la main (modifier le template)
- `eval/` et `notebooks/` : évaluation du classifieur

## Linear
- Équipe : "Albert", projet : "AI_news_radar"

## Règles
- Pas de `Co-Authored-By` ni de mention de Claude dans les commits et les PR.
- Une branche par ticket, jamais de commit sur `main`.
- Ne pas toucher aux fichiers hors du périmètre du ticket.
