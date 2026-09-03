# Neo Box

Le logiciel embarque de la **box domotique Neo** : un Raspberry Pi 4 B sous Home
Assistant OS, une antenne Zigbee (ZHA), un ecran e-ink Waveshare 2.13" (250 x 122)
et une croix directionnelle, dans un boitier imprime en 3D.

Ce dossier est un **depot d'add-ons Home Assistant OS**. L'add-on `neo_box` pilote
l'ecran et les boutons :

| Ecran | Quand | Contenu |
|---|---|---|
| Installation | box neuve, pas encore enrolee | QR + code a recopier, scanne par l'app installateur |
| Statut | au repos | Internet / Cloud / Home Assistant / Zigbee, IP, nom |
| Erreur | des qu'une sonde tombe | code `Exx`, libelle, QR vers la fiche d'aide |
| Menu | touche OK | appairage Zigbee, assistance a distance, reseau, redemarrage |

Les codes erreur vivent dans `src/neo_box/features/errors/domain/catalogue.py` et
sont stables pour toujours : on en ajoute, on n'en renomme jamais.

## Developper sans materiel

```bash
cd neo_box
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run python tools/render_screens.py     # PNG de tous les ecrans + planche contact
```

`tools/render_screens.py` produit `out/screens/contact-sheet.png` : **regarder la
planche avant de livrer**. Les tests prouvent que rien ne deborde ; ils ne prouvent
pas qu'un ecran est lisible.

Pour lancer le daemon en local avec un ecran PNG (rafraichi dans `out/live/latest.png`) :

```bash
NEO_DISPLAY=png NEO_PNG_DIR=out/live NEO_DATA_DIR=out/data \
NEO_SUPERVISOR_URL=http://localhost:1 NEO_HA_URL=http://localhost:1 \
uv run python -m neo_box
```

## Sur la box

Ajouter ce dossier comme depot d'add-ons dans le Supervisor, installer **Neo Box**.
Les options (`config.yaml`) : type d'ecran, URL d'aide, URL du backend, broches BCM
des six boutons.

**Non verifie sur materiel a ce jour** : le driver Waveshare (`waveshare_display.py`),
les boutons GPIO (`gpio_buttons.py`), les `devices` du `config.yaml` et le
`Dockerfile`. A valider au premier boot sur le Pi.

## Architecture

Clean architecture par feature (`src/neo_box/features/*`), domaine pur (aucun
`PIL`, aucun HTTP) : les ecrans sont des listes de primitives (`shared/drawing.py`),
mesurees avec les vraies metriques de police (`shared/layout.py`) et rasterisees par
l'infrastructure (`features/display/infra`).

```
shared/        primitives, geometrie 250x122, touches
features/
  display/     port Display + Pillow, PNG, Waveshare
  errors/      catalogue Exx + ecran d'erreur
  enrollment/  jeton Crockford + ecran QR
  status/      BoxState, diagnostic (priorite des erreurs), ecrans statut/reseau
  menu/        navigation a la croix + ecran
  app/         machine a etats (BoxApp), boucle (Runtime), adaptateurs HA/Supervisor
```
