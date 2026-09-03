ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-python:3.12-alpine3.21
FROM ${BUILD_FROM}

# Pillow (FreeType pour la police), spidev/gpiozero pour l'e-ink et les boutons.
# Le driver Waveshare n'est pas publie sur PyPI : installe depuis le depot officiel.
# VERIFIE SUR MATERIEL : NON.
RUN apk add --no-cache freetype jpeg zlib libgpiod git \
    && pip install --no-cache-dir \
        "pillow>=11.0" "qrcode>=8.0" spidev gpiozero lgpio \
        "git+https://github.com/waveshareteam/e-Paper#subdirectory=RaspberryPi_JetsonNano/python" \
    && apk del git

WORKDIR /app
COPY src /app/src
COPY run.sh /run.sh
RUN chmod a+x /run.sh

ENV PYTHONPATH=/app/src
CMD ["/run.sh"]
