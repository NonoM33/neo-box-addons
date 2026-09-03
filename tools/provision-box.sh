#!/usr/bin/env bash
# Provisionne une box HA OS fraichement flashee, depuis le Mac, par les API.
#   ./tools/provision-box.sh http://homeassistant.local:8123 https://stg.api.neo-domotique.fr
# VERIFIE SUR MATERIEL : NON. Chaque etape est idempotente autant que possible.
set -euo pipefail

HA_URL="${1:?URL de la box, ex. http://homeassistant.local:8123}"
BACKEND_URL="${2:?URL du backend Neo}"
ADDON_REPO="https://github.com/NonoM33/neo-box-addons"
CLIENT_ID="${HA_URL}/"
STATE_DIR="${HOME}/.neo-box"
mkdir -p "$STATE_DIR"

log() { printf '\033[1;34m[box]\033[0m %s\n' "$*"; }
# Les extraits python vivent dans des fonctions : bash 3.2 (macOS) se perd dans
# des guillemets imbriques a l'interieur de $( ... ).
onboarding_pending() { python3 -c 'import sys,json; sys.exit(0 if any(s["step"]=="user" and not s["done"] for s in json.load(sys.stdin)) else 1)'; }
json_field() { python3 -c 'import sys,json; print(json.load(sys.stdin)'"$1"')'; }
addon_slug() { python3 -c 'import sys,json; print(next(a["slug"] for a in json.load(sys.stdin)["data"]["addons"] if a["name"]=="Neo Box"))'; }
zha_flow() { python3 -c 'import sys,json; f=[x for x in json.load(sys.stdin) if x.get("handler")=="zha"]; print(f[0]["flow_id"] if f else "")'; }
api() { # api METHOD PATH [JSON]
  local method="$1" path="$2" body="${3:-}"
  curl -sS -X "$method" "${HA_URL}${path}" \
    -H "Authorization: Bearer ${TOKEN:-}" -H "Content-Type: application/json" \
    ${body:+--data "$body"}
}

# 1. Onboarding : le compte proprietaire, une seule fois par box.
if curl -sS "${HA_URL}/api/onboarding" | onboarding_pending; then
  PASSWORD="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)"
  log "creation du compte proprietaire neo"
  CODE=$(curl -sS -X POST "${HA_URL}/api/onboarding/users" -H "Content-Type: application/json" \
    --data "{\"client_id\":\"${CLIENT_ID}\",\"name\":\"Neo\",\"username\":\"neo\",\"password\":\"${PASSWORD}\",\"language\":\"fr\"}" \
    | json_field '["auth_code"]')
  TOKEN=$(curl -sS -X POST "${HA_URL}/auth/token" \
    --data-urlencode "grant_type=authorization_code" --data-urlencode "code=${CODE}" \
    --data-urlencode "client_id=${CLIENT_ID}" | json_field '["access_token"]')
  echo "${PASSWORD}" > "${STATE_DIR}/$(echo "$HA_URL" | tr -c 'A-Za-z0-9' '_').password"
  log "mot de passe du compte neo garde dans ${STATE_DIR} (affiche UNE fois) : ${PASSWORD}"
  api POST /api/onboarding/core_config '{}' >/dev/null
  api POST /api/onboarding/analytics '{}' >/dev/null
  api POST /api/onboarding/integration "{\"client_id\":\"${CLIENT_ID}\",\"redirect_uri\":\"${CLIENT_ID}\"}" >/dev/null || true
else
  log "onboarding deja fait"
fi

: "${TOKEN:?Relancer avec TOKEN=<jeton longue duree HA> : l'onboarding etait deja fait}"

# 2. Configuration de base.
api POST /api/config/core/update '{"location_name":"Neo Box","time_zone":"Europe/Paris","unit_system":"metric","currency":"EUR","country":"FR","language":"fr"}' >/dev/null
log "configuration de base posee"

# 3. Depot d'add-ons + neo_box.
api POST /api/hassio/store/repositories "{\"repository\":\"${ADDON_REPO}\"}" >/dev/null || true
api POST /api/hassio/store/reload '{}' >/dev/null || true
SLUG=$(api GET /api/hassio/store | addon_slug)
log "add-on ${SLUG}"
api POST "/api/hassio/store/addons/${SLUG}/install" '{}' >/dev/null || log "deja installe"
api POST "/api/hassio/addons/${SLUG}/options" "{\"options\":{\"display\":\"waveshare\",\"mesh\":\"tailscale\",\"backend_url\":\"${BACKEND_URL}\",\"help_url\":\"https://neo-domotique.fr\",\"internet_check_url\":\"https://neo-domotique.fr/\",\"zigbee_device_glob\":\"/dev/serial/by-id/*\",\"button_pins\":{\"UP\":5,\"DOWN\":6,\"LEFT\":13,\"RIGHT\":19,\"OK\":26,\"BACK\":21}}}" >/dev/null
api POST "/api/hassio/addons/${SLUG}/start" '{}' >/dev/null
log "neo_box demarre : la box doit afficher l'ecran INSTALLATION"

# 4. ZHA : confirmer le dongle decouvert (flux en attente) ou en ouvrir un.
FLOW=$(api GET /api/config/config_entries/flow | zha_flow)
if [ -n "$FLOW" ]; then
  api POST "/api/config/config_entries/flow/${FLOW}" '{}' >/dev/null && log "ZHA : dongle confirme" || log "ZHA : a terminer dans l'interface (Parametres > Integrations)"
else
  log "ZHA : aucun dongle decouvert — verifier l'USB, puis Parametres > Integrations > ZHA"
fi
log "termine. Rattacher la box : app integrateur > projet > Box, ou back-office > Box domotiques."
