#!/usr/bin/with-contenv bashio
# Traduit les options de l'add-on en variables d'environnement lues par `neo_box`.
set -euo pipefail

export NEO_DISPLAY="$(bashio::config 'display')"
export NEO_HELP_URL="$(bashio::config 'help_url')"
export NEO_BACKEND_URL="$(bashio::config 'backend_url')"
export NEO_INTERNET_CHECK_URL="$(bashio::config 'internet_check_url')"
export NEO_ZIGBEE_DEVICE_GLOB="$(bashio::config 'zigbee_device_glob')"
export NEO_VERSION="v$(bashio::addon.version)"
export NEO_DATA_DIR=/data
export NEO_PNG_DIR=/data/screens

pins=""
for key in UP DOWN LEFT RIGHT OK BACK; do
    pin="$(bashio::config "button_pins.${key}")"
    pins="${pins:+${pins},}${key}=${pin}"
done
export NEO_BUTTON_PINS="${pins}"

bashio::log.info "Neo Box ${NEO_VERSION} - ecran ${NEO_DISPLAY}, boutons ${NEO_BUTTON_PINS}"
exec python3 -m neo_box
