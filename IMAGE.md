# Image de la box — du Pi nu a la box enrolee

Etat au 2026-09-03 : **rien de ceci n'a encore tourne sur un Pi** (pas de carte SD).
La recette est ecrite d'apres la doc HA OS / Supervisor ; la valider au premier boot.

## 1. Flasher Home Assistant OS (une fois par carte)

1. Telecharger l'image RPi 4 64 bits : https://github.com/home-assistant/operating-system/releases
   (`haos_rpi4-64-<version>.img.xz`).
2. Flasher avec Balena Etcher ou Raspberry Pi Imager (pas de `dd` a l'aveugle :
   une erreur de disque efface le Mac).
3. Optionnel, pour le WiFi ou une IP fixe : cle USB nommee `CONFIG` avec
   `network/my-network` (format NetworkManager), branchee au premier boot.
4. Brancher l'ecran e-ink sur le GPIO, le dongle Zigbee en USB, le cable Ethernet,
   puis l'alimentation. Premier boot : 5 a 15 min (HA OS telecharge le core).
   La box repond ensuite sur `http://homeassistant.local:8123`.

## 2. Provisionner (depuis le Mac, sur le meme reseau)

```bash
./tools/provision-box.sh http://homeassistant.local:8123 https://stg.api.neo-domotique.fr
```

Le script enchaine, par les API HA/Supervisor :

1. onboarding : compte proprietaire `neo` (mot de passe genere, affiche une fois) ;
2. configuration de base (Paris, metrique, francais) ;
3. ajout du depot d'add-ons `https://github.com/NonoM33/neo-box-addons`,
   installation de `neo_box`, options (backend, mesh tailscale, ecran waveshare),
   demarrage ;
4. ZHA : confirmation du dongle decouvert en USB.

A la fin, la box affiche l'ecran **INSTALLATION** avec son QR : le rattachement se
fait depuis l'app integrateur (fiche projet > Box) ou le back-office.

## 3. Ce qui reste manuel pour l'instant

- L'image « doree » (SD clonee apres provisioning) : a produire une fois la
  recette validee, pour ne plus refaire l'etape 2 en serie.
- Le theme Neo et les automatisations de `neo-cloud/templates/` ne sont pas
  encore poses sur la box (ils le sont sur le chemin cloud-hosted).
