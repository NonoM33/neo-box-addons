"""Parsing des identifiants soumis par le portail captif."""

from neo_box.features.wifi_setup.domain.wifi import WifiCredentials
from neo_box.features.wifi_setup.infra.portal import page_html, parse_credentials


def test_parse_un_formulaire_complet() -> None:
    creds = parse_credentials("ssid=Maison+Neo&password=secret123")
    assert creds == WifiCredentials("Maison Neo", "secret123")


def test_parse_ignore_un_ssid_vide() -> None:
    assert parse_credentials("ssid=&password=x") is None
    assert parse_credentials("password=x") is None


def test_parse_garde_un_mot_de_passe_vide() -> None:
    creds = parse_credentials("ssid=Maison&password=")
    assert creds == WifiCredentials("Maison", "")


def test_la_page_contient_le_ssid_et_le_formulaire() -> None:
    page = page_html("NeoBox-Setup")
    assert "NeoBox-Setup" in page
    assert 'name="ssid"' in page
    assert 'name="password"' in page
